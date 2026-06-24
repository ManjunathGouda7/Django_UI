import os
import sys
import traceback
from FastAPI_MongoDB.SRC.Util import DBmodule,JsonOperations,RedisServices,GeneralFunctions
from fastapi import APIRouter,HTTPException,Query
from typing import Optional, List
from FastAPI_MongoDB.Modules.UIchecks.models import TestcaseHeader,UpdateTestcaseHeader,TestSteps,UpdateTestSteps,StepActions,ProjectData,ProjectUpdateData,TestData_run
import uuid,json,copy
from FastAPI_MongoDB.SRC.Exceptions import (APIException,api_exception_handler,validation_exception_handler,global_exception_handler)

RedisObj = RedisServices()
DBmod = DBmodule()
inputs_Collection = DBmod.get_collection("UIDB","Inputs")
Testcases_Collection = DBmod.get_collection("UIDB","Testcases")
POM_Collection = DBmod.get_collection("UIDB","POM")
Status_collection = DBmod.get_collection("UIDB","Status")
UIResults_collection = DBmod.get_collection("UIDB","UIResults")

JIP = JsonOperations(GeneralFunctions.get_path("FastAPI_MongoDB/Modules/UIchecks/pipelines.json"))
JIPdata = JIP.read_file()

JPro = JsonOperations(GeneralFunctions.get_path("assets/Project.json"))
JProData = JPro.read_file()

JIP2 = JsonOperations(GeneralFunctions.get_path("assets/Input.json"))
JIPData2 = JIP2.read_file()

router = APIRouter(
    prefix="/UIChecks"
)
################### General APIs    ############################################
@router.get("/GetProducts/",summary="Get all available products",tags=["UIchecks.General"])
async def GetProducts():
    pipeline =JIPdata['UIChecks']['General']['GetProducts']
    cursor = inputs_Collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise APIException(message="TestTags not found", code=404)
    return{"status":"success","code":200,"message":"Products Fetched Sucessfully","Details":{"data": result[0]['products']}}
@router.get("/GetCategory/{product_name}",summary="Get all available categories for selected product",tags=["UIchecks.General"])
async def GetCategory(product_name:str):
    pipeline = JIPdata['UIChecks']['General']['GetCategories']
    #update parameter
    pipeline[2]['$match']['details.Header']=product_name
    cursor = inputs_Collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise APIException(message=f"Categories not found for Product : {product_name}", code=404)
    return{"status":"success","code":200,"message":"Products Fetched Sucessfully","Details":{"data": result[0]['Categories']}}
@router.post("/UpdateProductCategoryJSON/{Product}/{Category}",summary="Update Product and Category name in Input JSON File",tags=["UIchecks.General"])
async def UpdateProductCategoryJSON(Product:str,Category:str):
    JIPData2 = JIP2.read_file()
    JIPData2['UIChecks']['UI_Product']=Product
    JIPData2['UIChecks']['UI_Category']=Category
    JIP2.update_file(JIPData2)
    return{"status":"success","code":200,"message":f"Product:{Product} and Category:{Category} updated succesfully in JSON","Details":{}}
################### Testcase setup releated APIs ################################
### TestTags------------------------------------------------------------------------
@router.get("/GetTestTags/",summary="Return all available Testcase tags",tags=["UIchecks.Testcase Setup"])
async def GetTestTags():
    pipeline =JIPdata['UIChecks']['TestcaseSetup']['GetTestcaseTags']
    cursor = inputs_Collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise APIException(message="Testcase Tags not found", code=404)
    return{"status":"success","code":200,"message":"Testcase Tags fetched sucessfully","Details":{"data": result[0]['TestTags']}}
@router.post("/PostTestTag/{tag_name}",summary="Insert new tag name",tags=["UIchecks.Testcase Setup"])
async def PostNewTestTag(tag_name:str):
    existing = await inputs_Collection.find_one({'Header':'TestTags','details':tag_name})
    if existing:
        raise APIException(message=f"Tag {tag_name} already exists", code=409)
    await inputs_Collection.update_one({"Header":"TestTags"},{'$push':{'details':tag_name}})
    return{"status":"success","code":200,"message":f"Tag {tag_name} added successfully","Details":{'data':tag_name}}
### TestSuits-------------------------------------------------------------------------
@router.get("/GetTestSuits/",summary="Return all available Testsuits",tags=["UIchecks.Testcase Setup"])
async def GetTestSuits():
    pipeline =JIPdata['UIChecks']['TestcaseSetup']['GetTestSuits']
    cursor = inputs_Collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise APIException(message="Testsuits not found", code=404)
    return{"status":"success","code":200,"message":"Testsuits fetched sucessfully","Details":{"data": result[0]['TestSuits']}}
@router.post("/PostTestsuit/{testsuit}",summary="Insert new Testsuit",tags=["UIchecks.Testcase Setup"])
async def PostNewTestsuit(testsuit:str):
    existing = await inputs_Collection.find_one({'Header':'TestSuits','details':testsuit})
    if existing:
        raise APIException(message=f"Tag {testsuit} already exists", code=409)
    await inputs_Collection.update_one({"Header":"TestSuits"},{'$push':{'details':testsuit}})
    return{"status":"success","code":200,"message":f"Tag {testsuit} added successfully","Details":{'data':testsuit}}
### TestHeaders--------------------------------------------------------------------------
@router.post("/PostTestHeader/",summary="Add new Testcase header details",tags=["UIchecks.Testcase Setup"])
async def PostTestcaseHeader(TCheader:TestcaseHeader):
    TCheaderData = TCheader.dict()
    #TBD : check that the TestID is already taken
    existing = await Testcases_Collection.find_one({'Header.Test':TCheaderData['TestID']})
    if existing is None:
        result = await Testcases_Collection.insert_one(TCheaderData)
        return{"status":"success","code":200,"message":"Testcase Step updated sucessfully","Details":{"data":str(result.inserted_id) }}
    raise APIException(message=f"TestID {TCheaderData['TestID']} already exists", code=409)
@router.put("/PutTestHeader/{TestID}/{Product}/{Category}",summary="Update Testcase header by TestID",tags=["UIchecks.Testcase Setup"])
async def PutTestcaseHeader(TestID:str,Product:str,Category:str,data :UpdateTestcaseHeader):
    # Remove fields that are None
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise APIException(message="No fields provided for update", code=400)
    result = await Testcases_Collection.update_one(
        {"TestID": TestID,"Product":Product,"Category":Category},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise APIException(message="Testcase not found to update", code=404)
    return{"status":"success","code":200,"message":"Testcase updated successfully","Details":{"data": list(update_data.keys())}}
@router.get("/GetTestHeader/",summary="Get All applicable testcases beased on the filters",tags=["UIchecks.Testcase Setup"])
async def GetTestcases(Product:str,Category:str,TestSuits:Optional[List[str]]=Query(None),Tags:Optional[List[str]]=Query(None),TestID:Optional[str]=Query(None)):
    projection={
        "_id":0,    
        "TestID":1,
        "TestName":1,
        "Description":1,
        "Testsuits":1,
        "TestTags":1
    }
    qryFilter = {}
    if Product:
        qryFilter["Product"]=Product
    if Category:
        qryFilter["Category"]=Category
    if TestSuits:
        qryFilter["Testsuits"] = {"$in":TestSuits}
    if Tags:
        qryFilter["TestTags"] = {"$in":Tags}
    if TestID:
        qryFilter["TestID"]=TestID
    cursor = Testcases_Collection.find(qryFilter,projection)
    testcases = await cursor.to_list(length=100)
    if testcases is None:
        raise APIException(message="Testcase not found.!", code=404)
    return{"status":"success","code":200,"message":"Testcases fetched sucessfully","Details":{"data":testcases }}
@router.delete("/DeleteTestHeader/",summary="Delete the Testcases from the list of TestID",tags=["UIchecks.Testcase Setup"])
async def DeleteTestHeader(Product:str,Category:str,TestIDs:List[str]=Query(...)):
    result = await Testcases_Collection.delete_many({"Product":Product,"Category":Category,"TestID":{"$in":TestIDs}})
    if result.deleted_count ==0:
        raise APIException(message="No matching TestIDs found", code=404)
    return{"status":"success","code":200,"message":f"{result.deleted_count} testcase(s) deleted successfully","Details":{"data":TestIDs}}
### Test Steps---------------------------------------------------------------------------------
@router.put("/PutTCStep/{TestID}/{Product}/{Category}",summary="add new testcase step for the existing testcase",tags=["UIchecks.Testcase Setup"])
async def PutTCStep(TestID:str,Product:str,Category:str,data :TestSteps):
    updateData = data.dict()
    print(TestID,Product,Category,updateData)
    result = await Testcases_Collection.update_one(
        {"TestID": TestID,"Product":Product,"Category":Category},
        {"$push": {"Details":updateData}}
    )
    if result.matched_count == 0:
        raise APIException(message="Testcase step not found", code=404)
    return{"status":"success","code":200,"message":"Testcase Step updated sucessfully","Details":{"data": list(updateData.keys())}}
@router.get("/GetTCSteps/",summary="Get all applicable steps for the testcase",tags=["UIchecks.Testcase Setup"])
async def GetTCSteps(Product:str,Category:str,TestID:str,StepID:Optional[str]=Query(None)):
    pipeline =JIPdata['UIChecks']['TestcaseSetup']['GetTCStep'] if StepID else JIPdata['UIChecks']['TestcaseSetup']['GetTCStepsAll']
    #update parameter
    pipeline[0]['$match']['Product']=Product
    pipeline[0]['$match']['Category']=Category
    pipeline[0]['$match']['TestID']=TestID
    if StepID:  pipeline[2]['$match']['Details.StepID']=StepID
    cursor = Testcases_Collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise APIException(message=f"Steps not found for the Testcase :{TestID}", code=404)
    return{"status":"success","code":200,"message":f"Steps loaded sucessfully for the Testcase:{TestID}","Details":{"data":result[0]['TCSteps']}}
@router.put("/PutUpdateTCStep/{Product}/{Category}/{TestID}/{StepID}",summary="Update existing test setp by stepID",tags=["UIchecks.Testcase Setup"])
async def PutUpdateTCStep(Product:str,Category:str,TestID:str,StepID:str,data:UpdateTestSteps):
    #  Remove fields that are None
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise APIException(message=f"No fields provided for update the TestID:{StepID}", code=400)
    # Convert fields to nested array update
    update_fields = {f"Details.$.{k}": v for k, v in update_data.items()}
    result = await Testcases_Collection.update_one(
        {"TestID": TestID,"Details.StepID":StepID ,"Product":Product,"Category":Category},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise APIException(message=f"StepID:{StepID} for TestID:{TestID} not found", code=404)
    return{"status":"success","code":200,"message":f"Test Step:{StepID} updated successfully for Testcase:{TestID}","Details":{"data": list(update_data.keys())}}
@router.get("/GetGenerateStepID/{TestID}",summary="Auto generate stepID from TestID by reffering the existing steps",tags=["UIchecks.Testcase Setup"])
async def GetStepID(TestID:str):
    TCs = await Testcases_Collection.find_one({'TestID':TestID})
    if TCs:
        stepcnt = len(TCs['Details'])+1
        StepID = f"{TestID}_{str(stepcnt).zfill(3)}"
        while True:
            stepsexist = await Testcases_Collection.find_one({"TestID": TestID,"Details.StepID": StepID})
            if stepsexist is None:
                break
            else:
                StepID = f"{TestID}_{str(stepcnt+1).zfill(3)}"
        return{"status":"success","code":200,"message":"Actions loaded sucessfully","Details":{"data":StepID}}
    raise APIException(message=f"Testcase {TestID} not found", code=404)
@router.delete("/DeleteTCSteps/",summary="Delete Testcase stpes by  list of tetcase setpIDs and TestID",tags=['UIchecks.Testcase Setup'])
async def DeleteTCSteps(Product:str,Category:str,TestID:str,StepIDs:List[str]=Query(...)):
    result = await Testcases_Collection.update_one(
        {
            "Product":Product,
            "Category":Category,
            "TestID":TestID,
        },
        {
            "$pull":{
                "Details":{"StepID":{"$in":StepIDs}}
            }
        }
    )
    if result.matched_count==0:
        raise APIException(message=f"TestID:{TestID} not found", code=404)
    if result.modified_count == 0:
        raise APIException(message=f"Step(s) already deleted for TestID:{TestID}", code=404)
    return {"status":"success","code":200,"message":f"TestID :{TestID} successfully deleted","Details":{"data":StepIDs}}
### Actons ------------------------------------------------------------------------------------
@router.get("/GetActionsList/",summary="Get all actions to perform on the elements",tags=["UIchecks.Testcase Setup"])
async def GetActionsList():
    pipeline =JIPdata['UIChecks']['TestcaseSetup']['GetActionsList']
    cursor = inputs_Collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise APIException(message="Actions not found", code=404)
    return{"status":"success","code":200,"message":"Actions loaded sucessfully","Details":{"data":result[0]['Actions']}}
@router.put("/PutActions/{Product}/{Category}/{TestID}/{StepID}",summary="Add New action for the element of the step",tags=["UIchecks.Testcase Setup"])
async def PutActions(Product:str,Category:str,TestID:str,StepID:str,data:StepActions):
    try:
        updateData = data.dict()
        #check that the action is already added
        ActionExist = Testcases_Collection.find({"Product":Product,"Category":Category,"TestID":TestID,"Details":{"$elemMatch":{"StepID":StepID,"Details":{"$elemMatch":{"Action":updateData['Action']}}}}})
        Actions = await ActionExist.to_list(length=100)
        if len(Actions)>0:
            return{"status":"error","code":404,"message":f"The Action:{updateData['Action']} is already available for the SetpID:{StepID}","Details":{}}
        else:
            result = await Testcases_Collection.update_one(
                {"TestID": TestID,"Details.StepID": StepID,"Product":Product,"Category":Category},
                {"$push": {"Details.$.Details":updateData}}
            )
            if result.matched_count == 0:
                return{"status":"error","code":404,"message":"Test Step not found","Details":{}}
            return{"status":"success","code":200,"message":f"Action added sucessfully","Details":{"data": list(updateData.keys())}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetActions/",summary="Get all the actions defined for the test steps",tags=["UIchecks.Testcase Setup"])
async def GetActions(Product:str,Category:str,TestID:str,StepID:str):
    try:
        pipeline =JIPdata['UIChecks']['TestcaseSetup']['GetActions']
        #update parameter
        pipeline[0]['$match']['Product']=Product
        pipeline[0]['$match']['Category']=Category
        pipeline[0]['$match']['TestID']=TestID
        pipeline[2]['$match']['Details.StepID']=StepID
        cursor = Testcases_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        # print(result)
        if not result:
            return{"status":"error","code":404,"message":f"Steps not found for the Testcase :{TestID}","Details":{}}
        return{"status":"success","code":200,"message":f"Steps loaded sucessfully for the Testcase:{TestID}","Details":{"data":result[0]['Actions']}}
    except Exception as e:
        return {"status":"exception","code":500,"message":f"Exception occurred : {str(e)}","Details":{}}
@router.delete("/DeleteActions/",summary="Delete the list of actions for the StepID",tags=["UIchecks.Testcase Setup"])
async def DeleteActions(Product:str,Category:str,StepID:str,Actions:List[str]=Query(...)):  
    try:
        result = await Testcases_Collection.update_one(
            {
                "Product":Product,
                "Category":Category,
                "Details.StepID":StepID,
            },
            {
                "$pull":{
                    "Details.$.Details":{"Action":{"$in":Actions}}
                }
            }
        )
        if result.matched_count==0:
            return {"status":"error","code":404,"message":f"stepID:{StepID} not found","Details":{}}
        return {"status":"success","code":200,"message":f"Action(s) deleted successfully for the stepID :{StepID} successfully","Details":{"data":Actions}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
########################## POM ##########################################################
@router.put("/AddWebPage/",summary="Add new webpage for selected product and category",tags=["UIchecks.POM"])
async def AddWebPage():
    try:
        pass
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetWebpages/{Product}/{Category}",summary="Get all available webpages for selected Product and Category for POM",tags=["UIchecks.POM"])
async def GetWebpages(Product:str,Category:str):
    try:
        pipeline = JIPdata['UIChecks']['POM']['GetWebpages2']
        #update parameter
        pipeline[2]['$match']['details.Header']=Product
        pipeline[4]['$match']['details.details.Header']=Category
        cursor = inputs_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        print(result)
        if not result:
            return{"status":"error","code":404,"message":f"Webpage not found for Product : {Product} and Category: {Category}","Details":{}}
        return{"status":"success","code":200,"message":"Webpages loaded sucessfully","Details":{"data":result[0]['WebPages'] }}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetFrames/{Product}/{Category}/{Webpage}",summary="Get all available Frames for the selected Product, Category and Webpage for POM",tags=["UIchecks.POM"])
async def GetFrames(Product:str,Category:str,Webpage:str):
    try:
        pipeline = JIPdata['UIChecks']['POM']['GetFrames2']
        #update parameter
        pipeline[2]['$match']['details.Header']=Product
        pipeline[4]['$match']['details.details.Header']=Category
        pipeline[8]['$match']['details.details.details.UIData.details.WebPage']=Webpage
        cursor = inputs_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return{"status":"error","code":404,"message":f"Webpage not found for Product : {Product}, Category: {Category} and Webpage:{Webpage}","Details":{}}
        return{"status":"success","code":200,"message":"Frames loaded sucessfully","Details":{"data":result[0]['Frames'] }}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetElements/{Product}/{Category}/{Webpage}/{Frame}",summary="Get all available elements for the selected product,category,Webpage and Frame for POM",tags=["UIchecks.POM"])
async def GetElements(Product:str,Category:str,Webpage:str,Frame:str):
    try:
        pipeline = JIPdata['UIChecks']['POM']['GetElements']
        #update parameter
        pipeline[0]['$match']['Product']=Product
        pipeline[2]['$match']['Details.Category']=Category
        pipeline[4]['$match']['Details.Details.WebPage']=Webpage
        pipeline[6]['$match']['Details.Details.Details.Frame']=Frame
        # print(pipeline)
        cursor = POM_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=100)
        if not result:
            return{"status":"error","code":404,"message":f"Elements not found for Product : {Product}, Category: {Category}, TestID:{Webpage}","Details":{}}
        return{"status":"success","code":200,"message":"Elements loaded sucessfully","Details":{"data":result[0]['Elements']}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetAllElements/",summary="Export all element data from POM",tags=["UIchecks.POM"])
async def GetAllElements(Product:str,Category:str,WebPages:Optional[List[str]]=Query(None),Frames:Optional[list[str]]=Query(None)):
    try:
        pipeline = copy.deepcopy(JIPdata['UIChecks']['POM']['GetAllElements'])
        #update parameter
        pipeline[0]['$match']['Product']=Product
        pipeline[2]['$match']['Details.Category']=Category
        if WebPages:pipeline.append({"$match": {"WebPage": {"$in": WebPages}}})
        if Frames:pipeline.append({"$match": {"Frame": {"$in": Frames}}})
        # print(pipeline)

        cursor = POM_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=100)
        if not result:
            return{"status":"error","code":404,"message":f"Elements not found for Product : {Product}, Category: {Category}","Details":{}}
        return{"status":"success","code":200,"message":"Elements loaded sucessfully","Details":{"data":result}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetElementType/",summary="Return all available Element types",tags=["UIchecks.POM"])
async def GetElementType():
    try:
        pipeline =JIPdata['UIChecks']['POM']['GetElementType']
        cursor = inputs_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return{"status":"error","code":404,"message":"Element types not found","Details":{}}
        return{"status":"success","code":200,"message":"Element types fetched sucessfully","Details":{"data": result[0]['TestTags']}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.post("/PostElement/",summary="Add new element to Page Object Model",tags=["UIchecks.POM"])
async def PostElement(Product:str,Category:str,Webpage:str,Frame:str,ElementName:str,Xpath:str,Type:str):
    try:
        existing = await POM_Collection.find_one({"Product": Product,"Details": {"$elemMatch": {"Category": Category,"Details": {"$elemMatch": {"WebPage": Webpage,
                    "Details": {"$elemMatch": {"Frame": Frame,"Details": {"$elemMatch": {"Element": ElementName}}}}}}}}})
        if existing:
            return{"status":"error","code":404,"message":f"Tag {ElementName} already exists for the given comibations","Details":{}}  
        else:
            await POM_Collection.update_one({"Product": Product},
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
                                                        "$position": 0   # 🔥 insert at beginning
                                                    }
                                                }
                                            },
                                            array_filters=[
                                                {"cat.Category": Category},
                                                {"wp.WebPage": Webpage},
                                                {"fr.Frame": Frame}
                                            ])
            return{"status":"success","code":200,"message":f"Element : {ElementName} added successfully","Details":{'data':ElementName}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetElement/",summary="Get the Xpath and Type of the given element",tags=["UIchecks.POM"])
async def GetElement(Product:str,Category:str,Webpage:str,Frame:str,ElementName:str):
    try:
        pipeline = copy.deepcopy(JIPdata['UIChecks']['POM']['GetElement'])
        #update parameter
        pipeline[0]['$match']['Product']=Product
        pipeline[2]['$match']['Details.Category']=Category
        pipeline[4]['$match']['Details.Details.WebPage']=Webpage
        pipeline[6]['$match']['Details.Details.Details.Frame']=Frame
        pipeline[8]['$match']['Details.Details.Details.Details.Element']=ElementName
        cursor = POM_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return{"status":"error","code":404,"message":f"Elements not found for given combination","Details":{}}
        return{"status":"success","code":200,"message":"Elements loaded sucessfully","Details":{"data":result[0]}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.put("/UpdateElement/",summary="Update Xpath and Type of the Element for given combination",tags=["UIchecks.POM"])
async def UpdateElement(Product:str,Category:str,Webpage:str,Frame:str,ElementName:str,Xpath:str,Type:str):
    try:
        result = await POM_Collection.update_one(
        {
            "Product": Product
        },
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
        )
        if result.matched_count == 0:
            return {"status": "error", "message": "Element not found to update","Details":{}}

        if result.modified_count == 0:
            return {"status": "warning", "message": "No changes made","Details":{}}
        return{"status":"success","code":200,"message":"Element updated sucessfully","Details":{"data":ElementName}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.delete("/DeleteElement/",summary="Delete POM Element",tags=["UIchecks.POM"])
async def DeleteElement(Product:str,Category:str,Webpage:str,Frame:str,ElementName:str):
    try:
        result = await POM_Collection.update_one(
                {"Product": Product},
                {
                    "$pull": {
                        "Details.$[cat].Details.$[web].Details.$[frame].Details": {
                            "Element":ElementName
                        }
                    }
                },
                array_filters=[
                    {"cat.Category": Category},
                    {"web.WebPage": Webpage},
                    {"frame.Frame": Frame}
                ]
            )
        if result.matched_count==0:
            return {"status":"error","code":404,"message":f"Element :{ElementName} not found","Details":{}}
        if result.modified_count == 0:
            return {"status":"error","code":200,"message":f"Element :{ElementName} allready deleted"}
        return {"status":"success","code":200,"message":f"Element :{ElementName} successfully deleted","Details":{"data":ElementName}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
###### Test Runner ###############################################
@router.get("/GetTestData/",summary="Prepare the test data from TestID to assign the UI check JOB to worker",tags=["UIchecks.Runner"])
async def GetTestData(Product:str,Category:str,TestIDs:list[str]=Query(...,min_length=1)):
    try:
        # print(TestIDs)
        pipeline = JIPdata['UIChecks']['UIRunner']['GetTestData']
        pipeline2 = JIPdata['UIChecks']['POM']['GetElementXpath']
        #update parameter
        pipeline[0]['$match']['Product']=Product
        pipeline[0]['$match']['Category']=Category
        pipeline[0]['$match']['TestID']["$in"]=TestIDs
        cursor = Testcases_Collection.aggregate(pipeline)
        result = await cursor.to_list(length=100)
        # print(result)
        if not result:
            return{"status":"error","code":404,"message":f"TestIDs:{','.join(TestIDs)} not found for Product : {Product} and Category: {Category}","Details":{}}
        else:   
            #Update xpath from POM
            index = 0
            tcindex = 0
            for TC in result:
                # print(tcindex)
                for steps in TC['Details']:
                    # print(index)
                    PathArgs = str(steps['Header']['ElementPath']).split("->")
                    #update parameters
                    pipeline2[0]['$match']['Product']=PathArgs[0]
                    pipeline2[2]['$match']['Details.Category']=PathArgs[1]
                    pipeline2[4]['$match']['Details.Details.WebPage']=PathArgs[2]
                    pipeline2[6]['$match']['Details.Details.Details.Frame']=PathArgs[3]
                    pipeline2[8]['$match']['Details.Details.Details.Details.Element']=PathArgs[4]
                    cursor2 = POM_Collection.aggregate(pipeline2)
                    result2 = await cursor2.to_list(length=100)
                    # print(result2)
                    result[tcindex]['Details'][index]['Header']['Xpath']=result2[0]['Element'] if result2 else None
                    result[tcindex]['Details'][index]['Header']['Type']=result2[0]['Type'] if result2 else None
                    # print(result)
                    index+=1
                tcindex+=1
                index=0
                # print(result)
            return{"status":f"success","code":200,"message":f"TestData created succesfully with xpath reference for the testcase {','.join(TestIDs)}","Details":{"data":result}}
            # #push job to redis queue
            # job={
            #     "JObID":str(uuid.uuid4),
            #     "TestData":result[0]
            # }
            # RedisObj.push_jobs(job)
            # return{"status":"success-Job queued","code":200,"message":"TestID loaded sucessfully","Details":{"data":result[0]}}
    except Exception as e:
        # traceback.print_exc()
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetJobList/",summary="Get all active jobs list from redis server",tags=["UIchecks.Runner"])
async def GetJobList():
    try:
        jobs = RedisObj.get_jobs()
        parsed_jobs = [json.loads(job) for job in jobs]
        return{"status":"success","code":200,"message":f"{len(parsed_jobs)}:Jobs fetched sucessfully","Details":{'data':parsed_jobs}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)

@router.delete("DeleteJob",summary="Delete the job by job ID from redis queue",tags=["UIchecks.Runner"])
async def deleteJob(JobID:Optional[str]=Query(None)):
    try:
        if JobID:
            res = RedisObj.delete_job_by_id(JobID)
            if res:
                return{"status":"success","code":200,"message":f"JobID:{JobID} deleted sucessfully","Details":{}}
            return{"status":"error","code":404,"message":f"JobID:{JobID} not found","Details":{}}
        else:
            RedisObj.delete_all_jobs()
            return{"status":"success","code":200,"message":f"All the jobs are deleted sucessfully","Details":{}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)

#Project __________________________
@router.put("/CreateProject/",summary="Create new project for UI execution",tags=["UIchecks.Project"])
async def CreateProject(data:ProjectData):
    try:
        # Remove fields that are None
        # update_data = data.model_dump(exclude_none=True)
        # print(update_data)
        # if not update_data:
        #     return {"status":"error","code":400,"message":"No fields provided for update","Details":{}}
        # result = await Status_collection.update_one(
        #     {"Header": "UIProject"},
        #     {"$set":{'Details':update_data}}
        # )
        # if result.matched_count == 0:
        #     return{"status":"error","code":404,"message":"Header info not found to update","Details":{}}

        #1.Get Project data
        JProData=JPro.read_file()
        updateData = data.dict()
        #2.get UI Project and update new Project fileds
        index = 0
        while index <= len(JProData):
            if JProData[index]['Header']=="UIProject":
                JProData[index]['Details']=updateData
                JPro.update_file(JProData)
                return{"status":"success","code":200,"message":"Project created successfully","Details":{"data": list(updateData.keys())}}
            index+=1
        if index==len(JProData):return {"status":"error","code":400,"message":"No provison for UI Project in JSON Structre","Details":{}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetProject/",summary="Get UI project Details",tags=["UIchecks.Project"])
async def GetProject():
    try:
        # pipeline = JIPdata['UIChecks']['UIRunner']['GetProject']
        # cursor = Status_collection.aggregate(pipeline)
        # result = await cursor.to_list(length=1)
        # if not result:
        #     return{"status":"error","code":404,"message":f"Project not found for UI checks","Details":{}}
        # return{"status":"success","code":200,"message":f"Project data fetched sucessfully","Details":{"data":result[0]}}
        JProData=JPro.read_file()
        index = 0
        while index <= len(JProData):
            if JProData[index]['Header']=="UIProject":
                if len(JProData[index]['Details'])>0:
                    data = {"ProjectName":JProData[index]['Details']['ProjectName'],
                            "TestEngineer":JProData[index]['Details']['TestEngineer'],
                            "TestLab":JProData[index]['Details']['TestLab'],
                            "SWversion1":JProData[index]['Details']['SWversion1'],
                            "SWversion2":JProData[index]['Details']['SWversion2'],
                            "FF1":JProData[index]['Details']['FF1'],
                            "FF2":JProData[index]['Details']['FF2'],
                            "FF3":JProData[index]['Details']['FF3'],
                            "FF4":JProData[index]['Details']['FF4'],
                            "Remarks":JProData[index]['Details']['Remarks'],
                            }
                    return{"status":"success","code":200,"message":f"Project data fetched sucessfully","Details":{"data":data}}
                else:return{"status":"error","code":404,"message":f"Project not found for UI checks","Details":{}}
                break
            index+=1
        if index==len(JProData):return {"status":"error","code":400,"message":"No provison for UI Project in JSON Structre","Details":{}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.delete("/DeleteProject/",summary="Clear the Project for UI checks",tags=["UIchecks.Project"])
async def DeleteProject():
    try:
        # result = await Status_collection.update_one(
        #     {
        #         "Header":"UIProject"
        #     },
        #     {
        #         "$set":{"Details":{}}
        #     }
        # )
        # if result.matched_count==0:
        #     return {"status":"error","code":404,"message":f"Project not found","Details":{}}
        # if result.modified_count == 0:
        #     return {"status":"error","code":200,"message":f"Project already deleted,no update needed "}
        # return {"status":"success","code":200,"message":f"Project deleted successfully","Details":{"data":"UIProject"}}
        JProData=JPro.read_file()
        index = 0
        while index <= len(JProData):
            if JProData[index]['Header']=="UIProject":
                JProData[index]['Details']=[]
                JPro.update_file(JProData)
                return{"status":"success","code":200,"message":f"Project deleted successfully","Details":{"data":"UIProject"}}
            index+=1
        if index==len(JProData):return {"status":"error","code":400,"message":"No provison for UI Project in JSON Structre","Details":{}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.put("/UpdateProject/",summary="Update project data",tags=["UIchecks.Project"])
async def UpdateProject(data:ProjectUpdateData):
    try:
        # # Remove fields that are None
        # update_data = data.model_dump(exclude_none=True)
        # # print(update_data)
        # if not update_data:
        #     return {"status":"error","code":400,"message":"No fields provided for update project","Details":{}}
        # result = await Status_collection.update_one(
        #     {"Header": "UIProject"},
        #     {"$set":{'Details':update_data}}
        # )
        # if result.matched_count == 0:
        #     return{"status":"error","code":404,"message":"Header info not found to update","Details":{}}
        # return{"status":"success","code":200,"message":"Project updated successfully","Details":{"data": list(update_data.keys())}}
    
        #1.Get Project data
        JProData=JPro.read_file()
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return {"status":"error","code":400,"message":"No fields provided for update project","Details":{}}
        #2.get UI Project and update new Project fileds
        index = 0
        while index <= len(JProData):
            if JProData[index]['Header']=="UIProject":
                for rec in update_data.keys():
                    JProData[index]['Details'][rec]=update_data[rec]
                # print(JProData)
                JPro.update_file(JProData)
                return{"status":"success","code":200,"message":"Project updated successfully","Details":{"data": list(update_data.keys())}}
            index+=1
        if index==len(JProData):return {"status":"error","code":400,"message":"No provison for UI Project in JSON Structre","Details":{}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
    
#Project__ Testcases execution

@router.put("/AddTestDataRun/",summary="Add TestData to project for execution",tags=["UIchecks.Project"])
async def AddTestDataRun(data:TestData_run):
    try:
        #1. check if the Testcase is already available
        # updateData = data.dict()
        # existing = await Status_collection.find_one({'Header':'UIProject',"Details.Details.Header.TestID":updateData['Header']['TestID']})
        # if existing:
        #     return{"status":"error","code":404,"message":f"Testcase {updateData['Header']['TestID']} already exists","Details":{}}
        # else:
        #     await Status_collection.update_one({"Header":"UIProject"},{'$push':{'Details.Details':updateData}})
        #     return{"status":"success","code":200,"message":f"Testcase {updateData['Header']['TestID']} added successfully","Details":{'data':[]}}
        #2. add testcase 

        JProData=JPro.read_file()
        index = 0
        updateData = data.dict()
        while index <= len(JProData):
            if JProData[index]['Header']=="UIProject":
                #Check project created 
                if len(JProData[index]['Details'])>0:
                    #check if the Testcase is already available
                    if len(JProData[index]['Details'])>0:
                        for TC in JProData[index]['Details']['Details']:
                            if TC['Header']['TestID']==updateData['Header']['TestID']:
                                return{"status":"error","code":404,"message":f"Testcase {updateData['Header']['TestID']} already exists","Details":{}}
                        JProData[index]['Details']['Details'].append(updateData)
                        JPro.update_file(JProData)
                        return{"status":"success","code":200,"message":f"Testcase {updateData['Header']['TestID']} added successfully","Details":{'data':[]}}
                    else:
                        JProData[index]['Details']['Details'].append(updateData)
                        JPro.update_file(JProData)
                        return{"status":"success","code":200,"message":f"Testcase {updateData['Header']['TestID']} added successfully","Details":{'data':[]}}
                else:return{"status":"error","code":404,"message":f"Project Not created to add the testcases","Details":{}}
            index+=1
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.delete("/DeleteTestDataRun/",summary="Delete testdata from the project",tags=["UIchecks.Project"])
async def DeleteTestDataRun(TestIDs:list[str]=Query(...)):
    try:
        JProData=JPro.read_file()
        index = 0
        while index <= len(JProData):
            if JProData[index]['Header']=="UIProject":
                if len(JProData[index]['Details'])>0:
                    Tcs = [item for item in JProData[index]['Details']['Details'] if item['Header']['TestID'] not in TestIDs]
                    JProData[index]['Details']['Details'] = Tcs
                    JPro.update_file(JProData)
                    return{"status":"success","code":200,"message":f"TestID(s):{','.join(TestIDs)} deleted successfully","Details":{'data':[]}}
                else:return{"status":"error","code":404,"message":f"Testcases are not available to delete","Details":{}}
            index+=1
        if index==len(JProData):return{"status":"error","code":404,"message":f"Project Not created to delete the testcases","Details":{}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
@router.get("/GetTestDataRun/",summary="Get all testID from project",tags=["UIchecks.Project"])
async def GetTestDataRun():
    try:
        JProData=JPro.read_file()
        index = 0
        while index <= len(JProData):
            if JProData[index]['Header']=="UIProject":
                #Check project created 
                if len(JProData[index]['Details'])>0:
                    TClist = {"TestID":[]}
                    for TC in JProData[index]['Details']['Details']:
                        TClist['TestID'].append(TC['Header']['TestID'])
                    return{"status":"success","code":200,"message":f"Testcase fetched successfully from project","Details":{'data':TClist}}
                else:return{"status":"error","code":404,"message":f"Project Not created to fetch the testcases","Details":{}}
            index+=1
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)


#Reports______________________________________________
@router.get("/ReportTestHeaders/",summary="Return Test headers details for passed parameters",tags=["UIchecks.Reports"])
async def ReportTestHeaders():
    try:
        pipeline = JIPdata['UIChecks']['UIReports']['TestHeaders']
        cursor = UIResults_collection.aggregate(pipeline)
        result = await cursor.to_list(length=100)
        # print(result)
        if not result:
            return{"status":"error","code":404,"message":f"Data not found","Details":{}}
        return{"status":"success","code":200,"message":f"Data found","Details":{'data':result}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
    
@router.get("/ReportTestSteps/{TestID}",summary="Return Test headers details for passed parameters",tags=["UIchecks.Reports"])
async def ReportTestSteps(TestID:str):
    try:
        pipeline = JIPdata['UIChecks']['UIReports']['TestSteps']
        #Update Parameters
        pipeline[1]['$match']['Details.TestID']=TestID
        cursor = UIResults_collection.aggregate(pipeline)
        result = await cursor.to_list(length=100)
        # print(result)
        if not result:
            return{"status":"error","code":404,"message":f"Data not found","Details":{}}
        return{"status":"success","code":200,"message":f"Data found","Details":{'data':result}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
    
@router.get("/ReportStepActions/{TestID}/{StepID}",summary="Return Actions for passed parameters",tags=["UIchecks.Reports"])
async def ReportStepActions(TestID:str,StepID:str):
    try:
        pipeline = JIPdata['UIChecks']['UIReports']['StepsActions']
        #Update Parameters
        pipeline[1]['$match']['Details.TestID']=TestID
        pipeline[3]['$match']['Details.Details.StepID']=StepID
        cursor = UIResults_collection.aggregate(pipeline)
        result = await cursor.to_list(length=100)
        # print(result)
        if not result:
            return{"status":"error","code":404,"message":f"Data not found","Details":{}}
        return{"status":"success","code":200,"message":f"Data found","Details":{'data':result}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)
    
@router.get("/DetailedUIReport/",summary="Return Detailed report data for passed parameters",tags=["UIchecks.Reports"])
async def DetailedUIReport():
    try:
        pipeline = JIPdata['UIChecks']['UIReports']['DetailedReport']
        cursor = UIResults_collection.aggregate(pipeline)
        result = await cursor.to_list(length=100)
        # print(result)
        if not result:
            return{"status":"error","code":404,"message":f"Data not found","Details":{}}
        return{"status":"success","code":200,"message":f"Data found","Details":{'data':result}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)

@router.get("/UploadResultJSON/",summary="Upload Result Json from project file to MOngoDB",tags=["UIchecks.Reports"])
async def UploadResultJSON(FilePath:str):
    try:
        if not os.path.exists(FilePath):
            return{"status":"error","code":404,"message":f"File not found","Details":{}}
        with open(FilePath, "r") as f:
            data = json.load(f)
        result = await UIResults_collection.insert_one(data)
        return{"status":"success","code":200,"message":f"File uploaded scuessfully","Details":{}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)