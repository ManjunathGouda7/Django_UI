from grl_api.db_helper import run_async
from grl_api.api.serializers import TestcaseHeaderSerializer
import uuid
import json
import os
import copy
from typing import Optional, List

from rest_framework.response import Response
from rest_framework.views import APIView

from FastAPI_MongoDB.SRC.Util import DBmodule, JsonOperations, RedisServices, GeneralFunctions
from FastAPI_MongoDB.SRC.Exceptions import APIException
from FastAPI_MongoDB.Modules.UIchecks.models import (
    TestcaseHeader,
    UpdateTestcaseHeader,
    TestSteps,
    UpdateTestSteps,
    StepActions,
    ProjectData,
    ProjectUpdateData,
    TestData_run,
)


# Mongo + JSON pipelines (ported from FastAPI implementation)
RedisObj = RedisServices()
DBmod = DBmodule()
inputs_Collection = DBmod.get_collection("UIDB", "Inputs")
Testcases_Collection = DBmod.get_collection("UIDB", "Testcases")
POM_Collection = DBmod.get_collection("UIDB", "POM")
Status_collection = DBmod.get_collection("UIDB", "Status")
UIResults_collection = DBmod.get_collection("UIDB", "UIResults")

# --- Lazy-loading JSON configs ---
# These files are required for pipeline construction. Import-time loading causes
# Django StatReloader to repeatedly log errors and can break development reloads
# when files are temporarily missing.

from django.conf import settings

_UICHECKS_CONFIG_CACHE = None


def _load_uichecks_json_configs():
    global _UICHECKS_CONFIG_CACHE
    if _UICHECKS_CONFIG_CACHE is not None:
        return _UICHECKS_CONFIG_CACHE

    pipelines_path = settings.GRL_REPO_ROOT / "FastAPI_MongoDB" / "Modules" / "UIchecks" / "pipelines.json"
    project_path = settings.GRL_ASSETS_DIR / "Project.json"
    input_path = settings.GRL_ASSETS_DIR / "Input.json"

    missing = [
        str(pipelines_path) if not pipelines_path.exists() else None,
        str(project_path) if not project_path.exists() else None,
        str(input_path) if not input_path.exists() else None,
    ]
    missing = [m for m in missing if m is not None]
    if missing:
        raise FileNotFoundError(
            "Required UIchecks JSON config file(s) not found: " + ", ".join(missing)
        )

    JIP = JsonOperations(str(pipelines_path))
    JPro = JsonOperations(str(project_path))
    JIP2 = JsonOperations(str(input_path))

    JIPdata = JIP.read_file()
    JProData = JPro.read_file()
    JIPData2 = JIP2.read_file()

    _UICHECKS_CONFIG_CACHE = {
        "JIPdata": JIPdata,
        "JProData": JProData,
        "JIPData2": JIPData2,
    }
    return _UICHECKS_CONFIG_CACHE



def _envelope(payload: dict):
    return Response(payload)


class GetProductsView(APIView):
    def get(self, request):
        cfg = _load_uichecks_json_configs()
        pipeline = copy.deepcopy(cfg["JIPData2"]["UIChecks"]["General"]["GetProducts"])
        cursor = inputs_Collection.aggregate(pipeline)

        # motor cursor is async; in Django sync view we use to_list via asyncio
        import asyncio
        result = run_async(cursor.to_list(length=1))
        if not result:
            return _envelope({"status": "error", "code": 404, "message": "TestTags not found", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Products Fetched Sucessfully", "Details": {"data": result[0]['products']}})


class GetCategoryView(APIView):
    def get(self, request, product_name: str):
        cfg = _load_uichecks_json_configs()
        pipeline = copy.deepcopy(cfg["JIPData2"]["UIChecks"]["General"]["GetCategories"])
        pipeline[2]['$match']['details.Header'] = product_name

        import asyncio
        cursor = inputs_Collection.aggregate(pipeline)
        result = run_async(cursor.to_list(length=1))
        if not result:
            return _envelope({"status": "error", "code": 404, "message": f"Categories not found for Product : {product_name}", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Products Fetched Sucessfully", "Details": {"data": result[0]['Categories']}})


class PostTestHeaderView(APIView):
    def post(self, request):
        serializer = TestcaseHeaderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "code": 400, "message": "Invalid request payload", "Details": serializer.errors}, status=400)
            
        validated_data = serializer.validated_data
        TCheader = TestcaseHeader(**validated_data)
        TCheaderData = TCheader.dict()  # pydantic v1 style in original code
        existing = run_async(Testcases_Collection.find_one({'Header.Test': TCheaderData['TestID']}))
        if existing is None:
            result = run_async(Testcases_Collection.insert_one(TCheaderData))
            return _envelope({"status": "success", "code": 200, "message": "Testcase Step updated sucessfully", "Details": {"data": str(result.inserted_id)}})
        return _envelope({"status": "error", "code": 409, "message": f"TestID {TCheaderData['TestID']} already exists", "Details": {}})


class UpdateProductCategoryJSONView(APIView):
    def post(self, request, Product: str, Category: str):
        input_path = str(settings.GRL_ASSETS_DIR / "Input.json")
        JIP2 = JsonOperations(input_path)
        JIPData2 = JIP2.read_file()
        JIPData2['UIChecks']['UI_Product'] = Product
        JIPData2['UIChecks']['UI_Category'] = Category
        JIP2.update_file(JIPData2)
        global _UICHECKS_CONFIG_CACHE
        _UICHECKS_CONFIG_CACHE = None
        return _envelope({"status": "success", "code": 200, "message": f"Product:{Product} and Category:{Category} updated succesfully in JSON", "Details": {}})


class GetTestTagsView(APIView):
    def get(self, request):
        cfg = _load_uichecks_json_configs()
        pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['TestcaseSetup']['GetTestcaseTags'])
        import asyncio
        cursor = inputs_Collection.aggregate(pipeline)
        result = run_async(cursor.to_list(length=1))
        if not result:
            return _envelope({"status": "error", "code": 404, "message": "Testcase Tags not found", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Testcase Tags fetched sucessfully", "Details": {"data": result[0]['TestTags']}})


class PostNewTestTagView(APIView):
    def post(self, request, tag_name: str):
        import asyncio
        existing = run_async(inputs_Collection.find_one({'Header': 'TestTags', 'details': tag_name}))
        if existing:
            return _envelope({"status": "error", "code": 409, "message": f"Tag {tag_name} already exists", "Details": {}})
        run_async(inputs_Collection.update_one({"Header": "TestTags"}, {'$push': {'details': tag_name}}))
        return _envelope({"status": "success", "code": 200, "message": f"Tag {tag_name} added successfully", "Details": {'data': tag_name}})


class GetTestSuitsView(APIView):
    def get(self, request):
        cfg = _load_uichecks_json_configs()
        pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['TestcaseSetup']['GetTestSuits'])
        import asyncio
        cursor = inputs_Collection.aggregate(pipeline)
        result = run_async(cursor.to_list(length=1))
        if not result:
            return _envelope({"status": "error", "code": 404, "message": "Testsuits not found", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Testsuits fetched sucessfully", "Details": {"data": result[0]['TestSuits']}})


class PostNewTestsuitView(APIView):
    def post(self, request, testsuit: str):
        import asyncio
        existing = run_async(inputs_Collection.find_one({'Header': 'TestSuits', 'details': testsuit}))
        if existing:
            return _envelope({"status": "error", "code": 409, "message": f"Tag {testsuit} already exists", "Details": {}})
        run_async(inputs_Collection.update_one({"Header": "TestSuits"}, {'$push': {'details': testsuit}}))
        return _envelope({"status": "success", "code": 200, "message": f"Tag {testsuit} added successfully", "Details": {'data': testsuit}})


class PutTestHeaderView(APIView):
    def put(self, request, TestID: str, Product: str, Category: str):
        serializer = TestcaseHeaderSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"status": "error", "code": 400, "message": "Invalid request payload", "Details": serializer.errors}, status=400)
            
        update_data = serializer.validated_data
        if not update_data:
            return _envelope({"status": "error", "code": 400, "message": "No fields provided for update", "Details": {}})
        result = run_async(Testcases_Collection.update_one(
            {"TestID": TestID, "Product": Product, "Category": Category},
            {"$set": update_data}
        ))
        if result.matched_count == 0:
            return _envelope({"status": "error", "code": 404, "message": "Testcase not found to update", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Testcase updated successfully", "Details": {"data": list(update_data.keys())}})


class GetTestHeaderView(APIView):
    def get(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        TestSuits = request.query_params.getlist('TestSuits') or request.query_params.getlist('TestSuits[]')
        Tags = request.query_params.getlist('Tags') or request.query_params.getlist('Tags[]')
        TestID = request.query_params.get('TestID')
        projection = {
            "_id": 0,
            "TestID": 1,
            "TestName": 1,
            "Description": 1,
            "Testsuits": 1,
            "TestTags": 1
        }
        qryFilter = {}
        if Product:
            qryFilter["Product"] = Product
        if Category:
            qryFilter["Category"] = Category
        if TestSuits:
            qryFilter["Testsuits"] = {"$in": TestSuits}
        if Tags:
            qryFilter["TestTags"] = {"$in": Tags}
        if TestID:
            qryFilter["TestID"] = TestID
        cursor = Testcases_Collection.find(qryFilter, projection)
        testcases = run_async(cursor.to_list(length=100))
        if testcases is None:
            return _envelope({"status": "error", "code": 404, "message": "Testcase not found.!", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Testcases fetched sucessfully", "Details": {"data": testcases}})


class DeleteTestHeaderView(APIView):
    def delete(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        TestIDs = request.query_params.getlist('TestIDs') or request.query_params.getlist('TestIDs[]')
        result = run_async(Testcases_Collection.delete_many({
            "Product": Product,
            "Category": Category,
            "TestID": {"$in": TestIDs}
        }))
        if result.deleted_count == 0:
            return _envelope({"status": "error", "code": 404, "message": "No matching TestIDs found", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": f"{result.deleted_count} testcase(s) deleted successfully", "Details": {"data": TestIDs}})


class PutTCStepView(APIView):
    def put(self, request, TestID: str, Product: str, Category: str):
        import asyncio
        tc_step = TestSteps(**request.data)
        updateData = tc_step.dict()
        result = run_async(Testcases_Collection.update_one(
            {"TestID": TestID, "Product": Product, "Category": Category},
            {"$push": {"Details": updateData}}
        ))
        if result.matched_count == 0:
            return _envelope({"status": "error", "code": 404, "message": "Testcase step not found", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Testcase Step updated sucessfully", "Details": {"data": list(updateData.keys())}})


class GetTCStepsView(APIView):
    def get(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        TestID = request.query_params.get('TestID')
        StepID = request.query_params.get('StepID')
        cfg = _load_uichecks_json_configs()
        pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['TestcaseSetup']['GetTCStep'] if StepID else cfg["JIPdata"]['UIChecks']['TestcaseSetup']['GetTCStepsAll'])
        pipeline[0]['$match']['Product'] = Product
        pipeline[0]['$match']['Category'] = Category
        pipeline[0]['$match']['TestID'] = TestID
        if StepID:
            pipeline[2]['$match']['Details.StepID'] = StepID
        cursor = Testcases_Collection.aggregate(pipeline)
        result = run_async(cursor.to_list(length=1))
        if not result:
            return _envelope({"status": "error", "code": 404, "message": f"Steps not found for the Testcase :{TestID}", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": f"Steps loaded sucessfully for the Testcase:{TestID}", "Details": {"data": result[0]['TCSteps']}})


class PutUpdateTCStepView(APIView):
    def put(self, request, Product: str, Category: str, TestID: str, StepID: str):
        import asyncio
        parsed_data = UpdateTestSteps(**request.data)
        if hasattr(parsed_data, 'model_dump'):
            update_data = parsed_data.model_dump(exclude_none=True)
        else:
            update_data = parsed_data.dict(exclude_none=True)
        if not update_data:
            return _envelope({"status": "error", "code": 400, "message": f"No fields provided for update the TestID:{StepID}", "Details": {}})
        update_fields = {f"Details.$.{k}": v for k, v in update_data.items()}
        result = run_async(Testcases_Collection.update_one(
            {"TestID": TestID, "Details.StepID": StepID, "Product": Product, "Category": Category},
            {"$set": update_fields}
        ))
        if result.matched_count == 0:
            return _envelope({"status": "error", "code": 404, "message": f"StepID:{StepID} for TestID:{TestID} not found", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": f"Test Step:{StepID} updated successfully for Testcase:{TestID}", "Details": {"data": list(update_data.keys())}})


class GetStepIDView(APIView):
    def get(self, request, TestID: str):
        import asyncio
        TCs = run_async(Testcases_Collection.find_one({'TestID': TestID}))
        if TCs:
            stepcnt = len(TCs['Details']) + 1
            StepID = f"{TestID}_{str(stepcnt).zfill(3)}"
            while True:
                stepsexist = run_async(Testcases_Collection.find_one({"TestID": TestID, "Details.StepID": StepID}))
                if stepsexist is None:
                    break
                else:
                    stepcnt += 1
                    StepID = f"{TestID}_{str(stepcnt).zfill(3)}"
            return _envelope({"status": "success", "code": 200, "message": "Actions loaded sucessfully", "Details": {"data": StepID}})
        return _envelope({"status": "error", "code": 404, "message": f"Testcase {TestID} not found", "Details": {}})


class DeleteTCStepsView(APIView):
    def delete(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        TestID = request.query_params.get('TestID')
        StepIDs = request.query_params.getlist('StepIDs') or request.query_params.getlist('StepIDs[]')
        result = run_async(Testcases_Collection.update_one(
            {
                "Product": Product,
                "Category": Category,
                "TestID": TestID,
            },
            {
                "$pull": {
                    "Details": {"StepID": {"$in": StepIDs}}
                }
            }
        ))
        if result.matched_count == 0:
            return _envelope({"status": "error", "code": 404, "message": f"TestID:{TestID} not found", "Details": {}})
        if result.modified_count == 0:
            return _envelope({"status": "error", "code": 404, "message": f"Step(s) already deleted for TestID:{TestID}", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": f"TestID :{TestID} successfully deleted", "Details": {"data": StepIDs}})


class GetActionsListView(APIView):
    def get(self, request):
        cfg = _load_uichecks_json_configs()
        pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['TestcaseSetup']['GetActionsList'])
        import asyncio
        cursor = inputs_Collection.aggregate(pipeline)
        result = run_async(cursor.to_list(length=1))
        if not result:
            return _envelope({"status": "error", "code": 404, "message": "Actions not found", "Details": {}})
        return _envelope({"status": "success", "code": 200, "message": "Actions loaded sucessfully", "Details": {"data": result[0]['Actions']}})


class PutActionsView(APIView):
    def put(self, request, Product: str, Category: str, TestID: str, StepID: str):
        import asyncio
        data_parsed = StepActions(**request.data)
        updateData = data_parsed.dict()
        try:
            ActionExist = Testcases_Collection.find({
                "Product": Product,
                "Category": Category,
                "TestID": TestID,
                "Details": {"$elemMatch": {"StepID": StepID, "Details": {"$elemMatch": {"Action": updateData['Action']}}}}
            })
            Actions = run_async(ActionExist.to_list(length=100))
            if len(Actions) > 0:
                return _envelope({"status": "error", "code": 404, "message": f"The Action:{updateData['Action']} is already available for the SetpID:{StepID}", "Details": {}})
            else:
                result = run_async(Testcases_Collection.update_one(
                    {"TestID": TestID, "Details.StepID": StepID, "Product": Product, "Category": Category},
                    {"$push": {"Details.$.Details": updateData}}
                ))
                if result.matched_count == 0:
                    return _envelope({"status": "error", "code": 404, "message": "Test Step not found", "Details": {}})
                return _envelope({"status": "success", "code": 200, "message": "Action added sucessfully", "Details": {"data": list(updateData.keys())}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetActionsView(APIView):
    def get(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        TestID = request.query_params.get('TestID')
        StepID = request.query_params.get('StepID')
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['TestcaseSetup']['GetActions'])
            pipeline[0]['$match']['Product'] = Product
            pipeline[0]['$match']['Category'] = Category
            pipeline[0]['$match']['TestID'] = TestID
            pipeline[2]['$match']['Details.StepID'] = StepID
            cursor = Testcases_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=1))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": f"Steps not found for the Testcase :{TestID}", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": f"Steps loaded sucessfully for the Testcase:{TestID}", "Details": {"data": result[0]['Actions']}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class DeleteActionsView(APIView):
    def delete(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        StepID = request.query_params.get('StepID')
        Actions = request.query_params.getlist('Actions') or request.query_params.getlist('Actions[]')
        try:
            result = run_async(Testcases_Collection.update_one(
                {
                    "Product": Product,
                    "Category": Category,
                    "Details.StepID": StepID,
                },
                {
                    "$pull": {
                        "Details.$.Details": {"Action": {"$in": Actions}}
                    }
                }
            ))
            if result.matched_count == 0:
                return _envelope({"status": "error", "code": 404, "message": f"stepID:{StepID} not found", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": f"Action(s) deleted successfully for the stepID :{StepID} successfully", "Details": {"data": Actions}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class AddWebPageView(APIView):
    def put(self, request):
        return _envelope({"status": "success", "code": 200, "message": "AddWebPage stub", "Details": {}})


class GetWebpagesView(APIView):
    def get(self, request, Product: str, Category: str):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['POM']['GetWebpages2'])
            pipeline[2]['$match']['details.Header'] = Product
            pipeline[4]['$match']['details.details.Header'] = Category
            cursor = inputs_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=1))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": f"Webpage not found for Product : {Product} and Category: {Category}", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Webpages loaded sucessfully", "Details": {"data": result[0]['WebPages']}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetFramesView(APIView):
    def get(self, request, Product: str, Category: str, Webpage: str):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['POM']['GetFrames2'])
            pipeline[2]['$match']['details.Header'] = Product
            pipeline[4]['$match']['details.details.Header'] = Category
            pipeline[8]['$match']['details.details.details.UIData.details.WebPage'] = Webpage
            cursor = inputs_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=1))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": f"Webpage not found for Product : {Product}, Category: {Category} and Webpage:{Webpage}", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Frames loaded sucessfully", "Details": {"data": result[0]['Frames']}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetElementsView(APIView):
    def get(self, request, Product: str, Category: str, Webpage: str, Frame: str):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['POM']['GetElements'])
            pipeline[0]['$match']['Product'] = Product
            pipeline[2]['$match']['Details.Category'] = Category
            pipeline[4]['$match']['Details.Details.WebPage'] = Webpage
            pipeline[6]['$match']['Details.Details.Details.Frame'] = Frame
            cursor = POM_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": f"Elements not found for Product : {Product}, Category: {Category}, TestID:{Webpage}", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Elements loaded sucessfully", "Details": {"data": result[0]['Elements']}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetAllElementsView(APIView):
    def get(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        WebPages = request.query_params.getlist('WebPages') or request.query_params.getlist('WebPages[]')
        Frames = request.query_params.getlist('Frames') or request.query_params.getlist('Frames[]')
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['POM']['GetAllElements'])
            pipeline[0]['$match']['Product'] = Product
            pipeline[2]['$match']['Details.Category'] = Category
            if WebPages:
                pipeline.append({"$match": {"WebPage": {"$in": WebPages}}})
            if Frames:
                pipeline.append({"$match": {"Frame": {"$in": Frames}}})
            cursor = POM_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": f"Elements not found for Product : {Product}, Category: {Category}", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Elements loaded sucessfully", "Details": {"data": result}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetElementTypeView(APIView):
    def get(self, request):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = cfg["JIPdata"]['UIChecks']['POM']['GetElementType']
            cursor = inputs_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=1))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": "Element types not found", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Element types fetched sucessfully", "Details": {"data": result[0]['TestTags']}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class PostElementView(APIView):
    def post(self, request):
        import asyncio
        data = request.data or request.query_params
        Product = data.get('Product')
        Category = data.get('Category')
        Webpage = data.get('Webpage')
        Frame = data.get('Frame')
        ElementName = data.get('ElementName')
        Xpath = data.get('Xpath')
        Type = data.get('Type')
        try:
            existing = run_async(POM_Collection.find_one({
                "Product": Product,
                "Details": {"$elemMatch": {"Category": Category, "Details": {"$elemMatch": {"WebPage": Webpage, "Details": {"$elemMatch": {"Frame": Frame, "Details": {"$elemMatch": {"Element": ElementName}}}}}}}}
            }))
            if existing:
                return _envelope({"status": "error", "code": 404, "message": f"Tag {ElementName} already exists for the given comibations", "Details": {}})
            else:
                run_async(POM_Collection.update_one(
                    {"Product": Product},
                    {"$push": {"Details.$[cat].Details.$[wp].Details.$[fr].Details": {
                                "$each": [
                                    {
                                        "Element": ElementName,
                                        "Details": {
                                            "Type": Type,
                                            "Locator": "xpath",
                                            "Value": Xpath
                                        }
                                    }
                                ],
                                "$position": 0
                            }
                        }
                    },
                    array_filters=[
                        {"cat.Category": Category},
                        {"wp.WebPage": Webpage},
                        {"fr.Frame": Frame}
                    ]
                ))
                return _envelope({"status": "success", "code": 200, "message": f"Element : {ElementName} added successfully", "Details": {'data': ElementName}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetElementView(APIView):
    def get(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        Webpage = request.query_params.get('Webpage')
        Frame = request.query_params.get('Frame')
        ElementName = request.query_params.get('ElementName')
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['POM']['GetElement'])
            pipeline[0]['$match']['Product'] = Product
            pipeline[2]['$match']['Details.Category'] = Category
            pipeline[4]['$match']['Details.Details.WebPage'] = Webpage
            pipeline[6]['$match']['Details.Details.Details.Frame'] = Frame
            pipeline[8]['$match']['Details.Details.Details.Details.Element'] = ElementName
            cursor = POM_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=1))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": "Elements not found for given combination", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Elements loaded sucessfully", "Details": {"data": result[0]}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class UpdateElementView(APIView):
    def put(self, request):
        import asyncio
        data = request.data or request.query_params
        Product = data.get('Product')
        Category = data.get('Category')
        Webpage = data.get('Webpage')
        Frame = data.get('Frame')
        ElementName = data.get('ElementName')
        Xpath = data.get('Xpath')
        Type = data.get('Type')
        try:
            result = run_async(POM_Collection.update_one(
                {"Product": Product},
                {
                    "$set": {
                        "Details.$[cat].Details.$[page].Details.$[frame].Details.$[elem].Details.Locator": "xpath",
                        "Details.$[cat].Details.$[page].Details.$[frame].Details.$[elem].Details.Value": Xpath,
                        "Details.$[cat].Details.$[page].Details.$[frame].Details.$[elem].Details.Type": Type
                    }
                },
                array_filters=[
                    {"cat.Category": Category},
                    {"page.WebPage": Webpage},
                    {"frame.Frame": Frame},
                    {"elem.Element": ElementName}
                ]
            ))
            if result.matched_count == 0:
                return _envelope({"status": "error", "code": 404, "message": "Element not found to update", "Details": {}})
            if result.modified_count == 0:
                return _envelope({"status": "warning", "code": 200, "message": "No changes made", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Element updated sucessfully", "Details": {"data": ElementName}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class DeleteElementView(APIView):
    def delete(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        Webpage = request.query_params.get('Webpage')
        Frame = request.query_params.get('Frame')
        ElementName = request.query_params.get('ElementName')
        try:
            result = run_async(POM_Collection.update_one(
                {"Product": Product},
                {
                    "$pull": {
                        "Details.$[cat].Details.$[web].Details.$[frame].Details": {
                            "Element": ElementName
                        }
                    }
                },
                array_filters=[
                    {"cat.Category": Category},
                    {"web.WebPage": Webpage},
                    {"frame.Frame": Frame}
                ]
            ))
            if result.matched_count == 0:
                return _envelope({"status": "error", "code": 404, "message": f"Element :{ElementName} not found", "Details": {}})
            if result.modified_count == 0:
                return _envelope({"status": "error", "code": 200, "message": f"Element :{ElementName} allready deleted", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": f"Element :{ElementName} successfully deleted", "Details": {"data": ElementName}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetTestDataView(APIView):
    def get(self, request):
        import asyncio
        Product = request.query_params.get('Product')
        Category = request.query_params.get('Category')
        TestIDs = request.query_params.getlist('TestIDs') or request.query_params.getlist('TestIDs[]')
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['UIRunner']['GetTestData'])
            pipeline2 = copy.deepcopy(cfg["JIPdata"]['UIChecks']['POM']['GetElementXpath'])
            pipeline[0]['$match']['Product'] = Product
            pipeline[0]['$match']['Category'] = Category
            pipeline[0]['$match']['TestID']["$in"] = TestIDs
            cursor = Testcases_Collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": f"TestIDs:{','.join(TestIDs)} not found for Product : {Product} and Category: {Category}", "Details": {}})
            
            tcindex = 0
            for TC in result:
                index = 0
                for steps in TC['Details']:
                    PathArgs = str(steps['Header']['ElementPath']).split("->")
                    pipeline2[0]['$match']['Product'] = PathArgs[0]
                    pipeline2[2]['$match']['Details.Category'] = PathArgs[1]
                    pipeline2[4]['$match']['Details.Details.WebPage'] = PathArgs[2]
                    pipeline2[6]['$match']['Details.Details.Details.Frame'] = PathArgs[3]
                    pipeline2[8]['$match']['Details.Details.Details.Details.Element'] = PathArgs[4]
                    cursor2 = POM_Collection.aggregate(pipeline2)
                    result2 = run_async(cursor2.to_list(length=100))
                    result[tcindex]['Details'][index]['Header']['Xpath'] = result2[0]['Element'] if result2 else None
                    result[tcindex]['Details'][index]['Header']['Type'] = result2[0]['Type'] if result2 else None
                    index += 1
                tcindex += 1
            return _envelope({"status": "success", "code": 200, "message": f"TestData created succesfully with xpath reference for the testcase {','.join(TestIDs)}", "Details": {"data": result}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetJobListView(APIView):
    def get(self, request):
        try:
            jobs = RedisObj.get_jobs()
            parsed_jobs = [json.loads(job) for job in jobs]
            return _envelope({"status": "success", "code": 200, "message": f"{len(parsed_jobs)}:Jobs fetched sucessfully", "Details": {'data': parsed_jobs}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class DeleteJobView(APIView):
    def delete(self, request):
        JobID = request.query_params.get('JobID')
        try:
            if JobID:
                res = RedisObj.delete_job_by_id(JobID)
                if res:
                    return _envelope({"status": "success", "code": 200, "message": f"JobID:{JobID} deleted sucessfully", "Details": {}})
                return _envelope({"status": "error", "code": 404, "message": f"JobID:{JobID} not found", "Details": {}})
            else:
                RedisObj.delete_all_jobs()
                return _envelope({"status": "success", "code": 200, "message": "All the jobs are deleted sucessfully", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class CreateProjectView(APIView):
    def put(self, request):
        try:
            project_path = str(settings.GRL_ASSETS_DIR / "Project.json")
            JPro = JsonOperations(project_path)
            JProData = JPro.read_file()
            data_parsed = ProjectData(**request.data)
            updateData = data_parsed.dict()
            index = 0
            while index < len(JProData):
                if JProData[index]['Header'] == "UIProject":
                    JProData[index]['Details'] = updateData
                    JPro.update_file(JProData)
                    global _UICHECKS_CONFIG_CACHE
                    _UICHECKS_CONFIG_CACHE = None
                    return _envelope({"status": "success", "code": 200, "message": "Project created successfully", "Details": {"data": list(updateData.keys())}})
                index += 1
            return _envelope({"status": "error", "code": 400, "message": "No provison for UI Project in JSON Structure", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetProjectView(APIView):
    def get(self, request):
        try:
            cfg = _load_uichecks_json_configs()
            JProData = cfg["JProData"]
            index = 0
            while index < len(JProData):
                if JProData[index]['Header'] == "UIProject":
                    details = JProData[index].get('Details', {})
                    if len(details) > 0:
                        data = {
                            "ProjectName": details.get('ProjectName'),
                            "TestEngineer": details.get('TestEngineer'),
                            "TestLab": details.get('TestLab'),
                            "SWversion1": details.get('SWversion1'),
                            "SWversion2": details.get('SWversion2'),
                            "FF1": details.get('FF1'),
                            "FF2": details.get('FF2'),
                            "FF3": details.get('FF3'),
                            "FF4": details.get('FF4'),
                            "Remarks": details.get('Remarks'),
                        }
                        return _envelope({"status": "success", "code": 200, "message": "Project data fetched sucessfully", "Details": {"data": data}})
                    else:
                        return _envelope({"status": "error", "code": 404, "message": "Project not found for UI checks", "Details": {}})
                index += 1
            return _envelope({"status": "error", "code": 400, "message": "No provison for UI Project in JSON Structure", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class DeleteProjectView(APIView):
    def delete(self, request):
        try:
            project_path = str(settings.GRL_ASSETS_DIR / "Project.json")
            JPro = JsonOperations(project_path)
            JProData = JPro.read_file()
            index = 0
            while index < len(JProData):
                if JProData[index]['Header'] == "UIProject":
                    JProData[index]['Details'] = []
                    JPro.update_file(JProData)
                    global _UICHECKS_CONFIG_CACHE
                    _UICHECKS_CONFIG_CACHE = None
                    return _envelope({"status": "success", "code": 200, "message": "Project deleted successfully", "Details": {"data": "UIProject"}})
                index += 1
            return _envelope({"status": "error", "code": 400, "message": "No provison for UI Project in JSON Structure", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class UpdateProjectView(APIView):
    def put(self, request):
        try:
            project_path = str(settings.GRL_ASSETS_DIR / "Project.json")
            JPro = JsonOperations(project_path)
            JProData = JPro.read_file()
            parsed_data = ProjectUpdateData(**request.data)
            if hasattr(parsed_data, 'model_dump'):
                update_data = parsed_data.model_dump(exclude_none=True)
            else:
                update_data = parsed_data.dict(exclude_none=True)
            if not update_data:
                return _envelope({"status": "error", "code": 400, "message": "No fields provided for update project", "Details": {}})
            index = 0
            while index < len(JProData):
                if JProData[index]['Header'] == "UIProject":
                    for rec in update_data.keys():
                        JProData[index]['Details'][rec] = update_data[rec]
                    JPro.update_file(JProData)
                    global _UICHECKS_CONFIG_CACHE
                    _UICHECKS_CONFIG_CACHE = None
                    return _envelope({"status": "success", "code": 200, "message": "Project updated successfully", "Details": {"data": list(update_data.keys())}})
                index += 1
            return _envelope({"status": "error", "code": 400, "message": "No provison for UI Project in JSON Structure", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class AddTestDataRunView(APIView):
    def put(self, request):
        try:
            project_path = str(settings.GRL_ASSETS_DIR / "Project.json")
            JPro = JsonOperations(project_path)
            JProData = JPro.read_file()
            data_parsed = TestData_run(**request.data)
            updateData = data_parsed.dict()
            index = 0
            while index < len(JProData):
                if JProData[index]['Header'] == "UIProject":
                    details = JProData[index].get('Details', {})
                    if len(details) > 0:
                        tc_list = details.get('Details', [])
                        for TC in tc_list:
                            if TC['Header']['TestID'] == updateData['Header']['TestID']:
                                return _envelope({"status": "error", "code": 404, "message": f"Testcase {updateData['Header']['TestID']} already exists", "Details": {}})
                        tc_list.append(updateData)
                        JProData[index]['Details']['Details'] = tc_list
                        JPro.update_file(JProData)
                        global _UICHECKS_CONFIG_CACHE
                        _UICHECKS_CONFIG_CACHE = None
                        return _envelope({"status": "success", "code": 200, "message": f"Testcase {updateData['Header']['TestID']} added successfully", "Details": {'data': []}})
                    else:
                        return _envelope({"status": "error", "code": 404, "message": "Project Not created to add the testcases", "Details": {}})
                index += 1
            return _envelope({"status": "error", "code": 400, "message": "No provison for UI Project in JSON Structure", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class DeleteTestDataRunView(APIView):
    def delete(self, request):
        TestIDs = request.query_params.getlist('TestIDs') or request.query_params.getlist('TestIDs[]')
        try:
            project_path = str(settings.GRL_ASSETS_DIR / "Project.json")
            JPro = JsonOperations(project_path)
            JProData = JPro.read_file()
            index = 0
            while index < len(JProData):
                if JProData[index]['Header'] == "UIProject":
                    details = JProData[index].get('Details', {})
                    if len(details) > 0:
                        tcs = [item for item in details.get('Details', []) if item['Header']['TestID'] not in TestIDs]
                        JProData[index]['Details']['Details'] = tcs
                        JPro.update_file(JProData)
                        global _UICHECKS_CONFIG_CACHE
                        _UICHECKS_CONFIG_CACHE = None
                        return _envelope({"status": "success", "code": 200, "message": f"TestID(s):{','.join(TestIDs)} deleted successfully", "Details": {'data': []}})
                    else:
                        return _envelope({"status": "error", "code": 404, "message": "Testcases are not available to delete", "Details": {}})
                index += 1
            return _envelope({"status": "error", "code": 400, "message": "No provison for UI Project in JSON Structure", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class GetTestDataRunView(APIView):
    def get(self, request):
        try:
            cfg = _load_uichecks_json_configs()
            JProData = cfg["JProData"]
            index = 0
            while index < len(JProData):
                if JProData[index]['Header'] == "UIProject":
                    details = JProData[index].get('Details', {})
                    if len(details) > 0:
                        TClist = {"TestID": []}
                        for TC in details.get('Details', []):
                            TClist['TestID'].append(TC['Header']['TestID'])
                        return _envelope({"status": "success", "code": 200, "message": "Testcase fetched successfully from project", "Details": {'data': TClist}})
                    else:
                        return _envelope({"status": "error", "code": 404, "message": "Project Not created to fetch the testcases", "Details": {}})
                index += 1
            return _envelope({"status": "error", "code": 400, "message": "No provison for UI Project in JSON Structure", "Details": {}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class ReportTestHeadersView(APIView):
    def get(self, request):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = cfg["JIPdata"]['UIChecks']['UIReports']['TestHeaders']
            cursor = UIResults_collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": "Data not found", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Data found", "Details": {'data': result}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class ReportTestStepsView(APIView):
    def get(self, request, TestID: str):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['UIReports']['TestSteps'])
            pipeline[1]['$match']['Details.TestID'] = TestID
            cursor = UIResults_collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": "Data not found", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Data found", "Details": {'data': result}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class ReportStepActionsView(APIView):
    def get(self, request, TestID: str, StepID: str):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = copy.deepcopy(cfg["JIPdata"]['UIChecks']['UIReports']['StepsActions'])
            pipeline[1]['$match']['Details.TestID'] = TestID
            pipeline[3]['$match']['Details.Details.StepID'] = StepID
            cursor = UIResults_collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": "Data not found", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Data found", "Details": {'data': result}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class DetailedUIReportView(APIView):
    def get(self, request):
        import asyncio
        try:
            cfg = _load_uichecks_json_configs()
            pipeline = cfg["JIPdata"]['UIChecks']['UIReports']['DetailedReport']
            cursor = UIResults_collection.aggregate(pipeline)
            result = run_async(cursor.to_list(length=100))
            if not result:
                return _envelope({"status": "error", "code": 404, "message": "Data not found", "Details": {}})
            return _envelope({"status": "success", "code": 200, "message": "Data found", "Details": {'data': result}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class UploadResultJSONView(APIView):
    def get(self, request):
        return self._upload(request)

    def post(self, request):
        return self._upload(request)

    def _upload(self, request):
        import asyncio
        FilePath = request.data.get('FilePath') or request.query_params.get('FilePath')
        try:
            if not FilePath or not os.path.exists(FilePath):
                return _envelope({"status": "error", "code": 404, "message": "File not found", "Details": {}})
            with open(FilePath, "r", encoding="utf-8") as f:
                data = json.load(f)
            result = run_async(UIResults_collection.insert_one(data))
            return _envelope({"status": "success", "code": 200, "message": "File uploaded successfully", "Details": {"inserted_id": str(result.inserted_id)}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})




