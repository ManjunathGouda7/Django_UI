from grl_api.db_helper import run_async
# grl_api/PFO.py
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import asyncio

# Import database module for dynamic options
try:
    from FastAPI_MongoDB.SRC.Util import DBmodule
except Exception:
    DBmodule = None

def pfo_view(request):
    """Render the PFO Automation page"""
    context = {
        'page_title': 'PFO Automation Dashboard',
        'api_base_url': '/api/v1/PFO/',  # Matches your URL structure
    }
    return render(request, 'grl_api/PFO.html', context)

@csrf_exempt
def pfo_filter_options(request):
    """Get filter options for dropdowns - uses database if available, else fallback to defaults"""
    try:
        # Try to get options from database
        if DBmodule:
            DBmod = DBmodule()
            collection = DBmod.get_collection("PFO_DB", "PFOData")
            
            fields = ['Board', 'CRX', 'DUT', 'Position', 'Power', 'PowerMode', 'RUN']
            options = {}
            
            for field in fields:
                pipeline = [
                    {"$group": {"_id": f"${field}"}},
                    {"$sort": {"_id": 1}}
                ]
                cursor = collection.aggregate(pipeline)
                result = run_async(cursor.to_list(length=100))
                values = [item.get('_id') for item in result if item.get('_id')]
                options[field.lower()] = values if values else ['(All)']
        else:
            # Fallback default options
            options = {
                'board': ['TPT-057', 'TPT-058', 'TPT-059'],
                'crx': ['CRX-001', 'CRX-002', 'CRX-003'],
                'dut': ['DUT-001', 'DUT-002', 'DUT-003'],
                'position': ['Position 1', 'Position 2', 'Position 3', 'Position 4'],
                'power': ['10W', '12.5W', '15W', '3.8W', '5W', '7.5W'],
                'powermode': ['Mode A', 'Mode B', 'Mode C'],
                'run': ['RUN 1', 'RUN 2', 'RUN 3']
            }
        
        return JsonResponse({
            'status': 'success',
            'data': options
        })
    except Exception as e:
        # Return default options on error
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'data': {
                'board': ['TPT-057', 'TPT-058', 'TPT-059'],
                'crx': ['CRX-001', 'CRX-002', 'CRX-003'],
                'dut': ['DUT-001', 'DUT-002', 'DUT-003'],
                'position': ['Position 1', 'Position 2', 'Position 3', 'Position 4'],
                'power': ['10W', '12.5W', '15W', '3.8W', '5W', '7.5W'],
                'powermode': ['Mode A', 'Mode B', 'Mode C'],
                'run': ['RUN 1', 'RUN 2', 'RUN 3']
            }
        })