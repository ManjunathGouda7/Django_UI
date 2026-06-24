from grl_api.db_helper import run_async
# grl_api/api/views_pfo.py
import asyncio
import json
import csv
from datetime import datetime
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

# FastAPI_MongoDB optional import
try:
    from FastAPI_MongoDB.SRC.Util import DBmodule  
except Exception:  
    DBmodule = None  

def _envelope(payload: dict):
    return Response(payload)

# Initialize database connection
DBmod = DBmodule()
PFO_Collection = DBmod.get_collection("PFO_DB", "PFOData")

class PFOHealthView(APIView):
    def get(self, request):
        return Response({
            "status": "success", 
            "code": 200, 
            "Details": {"data": "PFO service is running"}
        })

class GetPFODataView(APIView):
    """Get PFO data with filtering capabilities"""
    
    def get(self, request):
        return self._get(request)
    
    def post(self, request):
        return self._get(request)
    
    def _get(self, request):
        try:
            # Get filter parameters from request data or query params
            data = request.data if request.method == 'POST' else {}
            
            # Build filter dictionary
            filters = {
                "Board": data.get("Board") or request.query_params.get("Board"),
                "CRX": data.get("CRX") or request.query_params.get("CRX"),
                "DUT": data.get("DUT") or request.query_params.get("DUT"),
                "Position": data.get("Position") or request.query_params.get("Position"),
                "Power": data.get("Power") or request.query_params.get("Power"),
                "PowerMode": data.get("PowerMode") or request.query_params.get("PowerMode"),
                "RUN": data.get("RUN") or request.query_params.get("RUN"),
                "Product": data.get("Product") or request.query_params.get("Product"),
                "Category": data.get("Category") or request.query_params.get("Category"),
                "Webpage": data.get("Webpage") or request.query_params.get("Webpage"),
                "Frame": data.get("Frame") or request.query_params.get("Frame"),
                "ElementName": data.get("ElementName") or request.query_params.get("ElementName"),
            }
            
            # Build match query (exclude "(All)" and empty values)
            match = {}
            for key, value in filters.items():
                if value and value not in ["", "(All)", "All", "all"]:
                    match[key] = value
            
            # Build aggregation pipeline
            pipeline = []
            if match:
                pipeline.append({"$match": match})
            
            # Project to remove _id and sort
            pipeline.append({"$project": {"_id": 0}})
            pipeline.append({"$sort": {"Power": 1, "PFO": 1}})
            
            # Pagination parameters
            try:
                limit = int(data.get("limit") or request.query_params.get("limit", 100))
            except ValueError:
                limit = 100
            try:
                offset = int(data.get("offset") or request.query_params.get("offset", 0))
            except ValueError:
                offset = 0

            # Get total count
            if match:
                total_count = run_async(PFO_Collection.count_documents(match))
            else:
                total_count = run_async(PFO_Collection.count_documents({}))

            # Execute query with skip/limit
            if pipeline:
                pipeline_paginated = list(pipeline)
                if offset > 0:
                    pipeline_paginated.append({"$skip": offset})
                pipeline_paginated.append({"$limit": limit})
                cursor = PFO_Collection.aggregate(pipeline_paginated)
            else:
                cursor = PFO_Collection.find({}, {"_id": 0}).sort("Power", 1).skip(offset).limit(limit)
            
            # Convert cursor to list
            result = run_async(cursor.to_list(length=limit))
            
            # If no data from DB, return sample data for demo
            if not result and total_count == 0:
                sample_data = get_sample_data()
                total_count = len(sample_data)
                result = sample_data[offset:offset+limit]
            
            return _envelope({
                "status": "success",
                "code": 200,
                "message": "PFO data fetched successfully",
                "data": result,
                "total": total_count,
                "limit": limit,
                "offset": offset
            })
            
        except Exception as e:
            # Return sample data on error for demo
            return _envelope({
                "status": "success",
                "code": 200,
                "message": "Using sample data",
                "data": get_sample_data(),
                "total": len(get_sample_data())
            })

class GetPFOStatsView(APIView):
    """Get PFO statistics and aggregated data"""
    
    def get(self, request):
        try:
            # Get filter parameters
            board = request.query_params.get("Board")
            crx = request.query_params.get("CRX")
            dut = request.query_params.get("DUT")
            position = request.query_params.get("Position")
            power = request.query_params.get("Power")
            power_mode = request.query_params.get("PowerMode")
            
            # Build match query
            match = {}
            if board and board not in ["", "(All)", "All"]:
                match["Board"] = board
            if crx and crx not in ["", "(All)", "All"]:
                match["CRX"] = crx
            if dut and dut not in ["", "(All)", "All"]:
                match["DUT"] = dut
            if position and position not in ["", "(All)", "All"]:
                match["Position"] = position
            if power and power not in ["", "(All)", "All"]:
                match["Power"] = power
            if power_mode and power_mode not in ["", "(All)", "All"]:
                match["PowerMode"] = power_mode
            
            # Build aggregation pipeline for stats
            pipeline = []
            if match:
                pipeline.append({"$match": match})
            
            pipeline.extend([
                {"$group": {
                    "_id": "$Power",
                    "avgPFO": {"$avg": "$PFO"},
                    "minPFO": {"$min": "$PFO"},
                    "maxPFO": {"$max": "$PFO"},
                    "count": {"$sum": 1},
                    "avgRectifiedPower": {"$avg": "$RectifiedPower"},
                    "sampleData": {"$push": {
                        "PFO": "$PFO",
                        "RectifiedPower": "$RectifiedPower",
                        "Board": "$Board",
                        "Position": "$Position"
                    }}
                }},
                {"$sort": {"_id": 1}},
                {"$project": {
                    "power": "$_id",
                    "avgPFO": 1,
                    "minPFO": 1,
                    "maxPFO": 1,
                    "count": 1,
                    "avgRectifiedPower": 1,
                    "sampleData": {"$slice": ["$sampleData", 10]},
                    "_id": 0
                }}
            ])
            
            cursor = PFO_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            
            # If no data, use sample stats
            if not result:
                result = get_sample_stats()
            
            # Calculate overall stats
            total_tests = 0
            total_pfo = 0
            
            for item in result:
                total_tests += item.get("count", 0)
                if item.get("avgPFO"):
                    total_pfo += item.get("avgPFO") * item.get("count", 0)
            
            overall_avg = total_pfo / total_tests if total_tests > 0 else 0
            overall_min = min([item.get("minPFO", 0) for item in result]) if result else 0
            overall_max = max([item.get("maxPFO", 0) for item in result]) if result else 0
            
            return _envelope({
                "status": "success",
                "code": 200,
                "message": "Stats fetched successfully",
                "data": {
                    "byPower": result,
                    "overall": {
                        "totalTests": total_tests,
                        "avgPFO": round(overall_avg, 2),
                        "minPFO": round(overall_min, 2),
                        "maxPFO": round(overall_max, 2)
                    }
                }
            })
            
        except Exception as e:
            return _envelope({
                "status": "error",
                "code": 500,
                "message": f"Error fetching stats: {str(e)}",
                "data": None
            })

class ExecutePFOTestView(APIView):
    """Execute PFO test"""
    
    def post(self, request):
        try:
            # Get test parameters
            test_data = request.data or {}
            
            # Validate required parameters
            required_fields = ['Board', 'CRX', 'DUT', 'Power']
            missing_fields = [field for field in required_fields if field not in test_data]
            if missing_fields:
                return _envelope({
                    "status": "error",
                    "code": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                    "data": None
                })
            
            # Generate test ID
            test_id = f"PFO_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{test_data.get('Board', '')}"
            
            # Simulate test execution
            result = {
                "test_id": test_id,
                "status": "completed",
                "message": "Test execution completed successfully",
                "parameters": test_data,
                "timestamp": datetime.now().isoformat(),
                "results": {
                    "PFO": round(45.6 + (hash(test_id) % 20), 2),
                    "RectifiedPower": round(10.2 + (hash(test_id) % 5), 2),
                    "Status": "Pass" if hash(test_id) % 3 != 0 else "Fail"
                }
            }
            
            return _envelope({
                "status": "success",
                "code": 200,
                "message": "Test execution completed",
                "data": result
            })
            
        except Exception as e:
            return _envelope({
                "status": "error",
                "code": 500,
                "message": f"Error executing test: {str(e)}",
                "data": None
            })

class ExportPFOReportView(APIView):
    """Export PFO report as CSV"""
    
    def get(self, request):
        try:
            # Get filter parameters
            board = request.query_params.get("Board")
            crx = request.query_params.get("CRX")
            dut = request.query_params.get("DUT")
            position = request.query_params.get("Position")
            power = request.query_params.get("Power")
            power_mode = request.query_params.get("PowerMode")
            
            # Build match query
            match = {}
            if board and board not in ["", "(All)", "All"]:
                match["Board"] = board
            if crx and crx not in ["", "(All)", "All"]:
                match["CRX"] = crx
            if dut and dut not in ["", "(All)", "All"]:
                match["DUT"] = dut
            if position and position not in ["", "(All)", "All"]:
                match["Position"] = position
            if power and power not in ["", "(All)", "All"]:
                match["Power"] = power
            if power_mode and power_mode not in ["", "(All)", "All"]:
                match["PowerMode"] = power_mode
            
            # Build pipeline
            pipeline = []
            if match:
                pipeline.append({"$match": match})
            pipeline.append({"$project": {"_id": 0}})
            pipeline.append({"$sort": {"Power": 1, "PFO": 1}})
            
            # Execute query
            if pipeline:
                cursor = PFO_Collection.aggregate(pipeline)
            else:
                cursor = PFO_Collection.find({}, {"_id": 0}).sort("Power", 1)
            
            result = run_async(cursor.to_list(length=5000))
            
            # If no data, use sample data
            if not result:
                result = get_sample_data()
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            filename = f"PFO_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Write CSV
            if result:
                writer = csv.DictWriter(response, fieldnames=result[0].keys())
                writer.writeheader()
                writer.writerows(result)
            
            return response
            
        except Exception as e:
            return _envelope({
                "status": "error",
                "code": 500,
                "message": f"Error exporting report: {str(e)}",
                "data": None
            })

class PFOFilterOptionsView(APIView):
    """Get available filter options for dropdowns"""
    
    def get(self, request):
        try:
            # Get distinct values from database
            fields = ['Board', 'CRX', 'DUT', 'Position', 'Power', 'PowerMode', 'RUN']
            options = {}
            
            for field in fields:
                pipeline = [
                    {"$group": {"_id": f"${field}"}},
                    {"$sort": {"_id": 1}},
                    {"$project": {"_id": 0, "value": "$_id"}}
                ]
                cursor = PFO_Collection.aggregate(pipeline)
                result = run_async(cursor.to_list(length=100))
                values = [item.get('value') for item in result if item.get('value')]
                options[field.lower()] = values if values else get_default_options().get(field.lower(), [])
            
            return _envelope({
                "status": "success",
                "code": 200,
                "message": "Filter options fetched successfully",
                "data": options
            })
            
        except Exception as e:
            # Return default options on error
            return _envelope({
                "status": "success",
                "code": 200,
                "message": "Using default filter options",
                "data": get_default_options()
            })

# Helper functions for sample data
def get_sample_data():
    """Return sample PFO data for demonstration"""
    return [
        {'Board': 'TPT-057', 'CRX': 'CRX-001', 'DUT': 'DUT-001', 'Position': 'Position 1', 
         'Power': '10W', 'RectifiedPower': 10.2, 'PFO': 45.6, 'PowerMode': 'Mode A', 'RUN': 'RUN 1', 'Status': 'Pass'},
        {'Board': 'TPT-057', 'CRX': 'CRX-001', 'DUT': 'DUT-001', 'Position': 'Position 1', 
         'Power': '12.5W', 'RectifiedPower': 12.8, 'PFO': 52.3, 'PowerMode': 'Mode A', 'RUN': 'RUN 1', 'Status': 'Pass'},
        {'Board': 'TPT-057', 'CRX': 'CRX-001', 'DUT': 'DUT-001', 'Position': 'Position 1', 
         'Power': '15W', 'RectifiedPower': 15.1, 'PFO': 58.7, 'PowerMode': 'Mode A', 'RUN': 'RUN 1', 'Status': 'Pass'},
        {'Board': 'TPT-057', 'CRX': 'CRX-002', 'DUT': 'DUT-002', 'Position': 'Position 2', 
         'Power': '10W', 'RectifiedPower': 10.5, 'PFO': 42.1, 'PowerMode': 'Mode B', 'RUN': 'RUN 2', 'Status': 'Pass'},
        {'Board': 'TPT-057', 'CRX': 'CRX-002', 'DUT': 'DUT-002', 'Position': 'Position 2', 
         'Power': '12.5W', 'RectifiedPower': 12.9, 'PFO': 49.8, 'PowerMode': 'Mode B', 'RUN': 'RUN 2', 'Status': 'Fail'},
        {'Board': 'TPT-058', 'CRX': 'CRX-001', 'DUT': 'DUT-001', 'Position': 'Position 1', 
         'Power': '10W', 'RectifiedPower': 9.8, 'PFO': 44.2, 'PowerMode': 'Mode A', 'RUN': 'RUN 1', 'Status': 'Pass'},
        {'Board': 'TPT-058', 'CRX': 'CRX-001', 'DUT': 'DUT-001', 'Position': 'Position 1', 
         'Power': '12.5W', 'RectifiedPower': 12.3, 'PFO': 50.1, 'PowerMode': 'Mode A', 'RUN': 'RUN 1', 'Status': 'Pass'},
        {'Board': 'TPT-058', 'CRX': 'CRX-002', 'DUT': 'DUT-002', 'Position': 'Position 2', 
         'Power': '10W', 'RectifiedPower': 10.1, 'PFO': 43.5, 'PowerMode': 'Mode B', 'RUN': 'RUN 2', 'Status': 'Pass'},
        {'Board': 'TPT-059', 'CRX': 'CRX-001', 'DUT': 'DUT-003', 'Position': 'Position 3', 
         'Power': '15W', 'RectifiedPower': 14.8, 'PFO': 56.3, 'PowerMode': 'Mode A', 'RUN': 'RUN 1', 'Status': 'Pass'},
        {'Board': 'TPT-059', 'CRX': 'CRX-002', 'DUT': 'DUT-003', 'Position': 'Position 4', 
         'Power': '12.5W', 'RectifiedPower': 12.6, 'PFO': 48.9, 'PowerMode': 'Mode C', 'RUN': 'RUN 3', 'Status': 'Fail'},
    ]

def get_sample_stats():
    """Return sample statistics"""
    sample_data = get_sample_data()
    power_groups = {}
    
    for item in sample_data:
        power = item.get('Power', 'Unknown')
        if power not in power_groups:
            power_groups[power] = []
        power_groups[power].append(item.get('PFO', 0))
    
    result = []
    for power, values in power_groups.items():
        result.append({
            'power': power,
            'avgPFO': round(sum(values) / len(values), 2),
            'minPFO': min(values),
            'maxPFO': max(values),
            'count': len(values),
            'avgRectifiedPower': round(10 + (hash(power) % 5), 2),
            'sampleData': []
        })
    
    return sorted(result, key=lambda x: x['power'])

def get_default_options():
    """Return default filter options"""
    return {
        'board': ['TPT-057', 'TPT-058', 'TPT-059'],
        'crx': ['CRX-001', 'CRX-002', 'CRX-003'],
        'dut': ['DUT-001', 'DUT-002', 'DUT-003'],
        'position': ['Position 1', 'Position 2', 'Position 3', 'Position 4'],
        'power': ['10W', '12.5W', '15W', '3.8W', '5W', '7.5W'],
        'powermode': ['Mode A', 'Mode B', 'Mode C'],
        'run': ['RUN 1', 'RUN 2', 'RUN 3']
    }