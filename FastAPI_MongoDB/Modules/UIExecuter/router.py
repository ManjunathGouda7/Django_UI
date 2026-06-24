import traceback,asyncio
from datetime import datetime
from fastapi import APIRouter,HTTPException,Query,BackgroundTasks
from typing import Optional, List
from FastAPI_MongoDB.SRC.Util import DBmodule,JsonOperations,GeneralFunctions
# from Modules.UIExecuter.service import UIRunner_Playwright
from FastAPI_MongoDB.Modules.UIExecuter.playwrightModule import BasePage
from FastAPI_MongoDB.Modules.UIExecuter.APIValidator import PacketModule
from FastAPI_MongoDB.Modules.UIExecuter.UIActions import UIActionsModule
import FastAPI_MongoDB.Modules.UIchecks.router  as UIcheckRtr
import time, uuid, json,os,ast,requests
import numpy as np
from PIL import Image, ImageChops
from FastAPI_MongoDB.SRC.logger import logger
from FastAPI_MongoDB.SRC.Exceptions import APIException

BaseObj = BasePage()
APIVal = PacketModule()
UIAct = UIActionsModule(BaseObj)

DBmod = DBmodule()
# UIRunnnerPW = UIRunner_Playwright()
inputs_Collection = DBmod.get_collection("UIDB","Inputs")
router = APIRouter(
    prefix="/UIRunner"
)
JPipe = JsonOperations(GeneralFunctions.get_path("FastAPI_MongoDB/Modules/UIExecuter/pipelines.json"))
JPipedata = JPipe.read_file()
JPro = JsonOperations(GeneralFunctions.get_path("assets/Project.json"))
JProData = JPro.read_file()
JIP = JsonOperations(GeneralFunctions.get_path("assets/Input.json"))
JIPData = JIP.read_file()
FileStorage_Mode= JIPData['UIChecks']['FileStorage']
progress_store = {}

############################## Support function ##############################################
def JSONemptyReport(ProName="DefaultProject"):
        JIPData = JIP.read_file()
        directory = f"{JIPData['UIChecks']['ReportPath']}/GRL_Automation"
        os.makedirs(directory,exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        FolderPath =  os.path.join(directory, f"{ProName}_{JIPData['UIChecks']['UI_Product']}_{JIPData['UIChecks']['UI_Category']}_{timestamp}")
        os.makedirs(FolderPath, exist_ok=True)
        os.makedirs(f"{FolderPath}/IMG", exist_ok=True)
        file_path = os.path.join(FolderPath, f"{timestamp}.json")  
        ReportPath = FolderPath
        with open(file_path, "w") as f:
            json.dump({"Header":{},"Details":[]}, f, indent=4)
        return ReportPath,file_path
async def run_ui_tests(job_id, testcases, ProjData):
    try:
        #1. Create report folder
        # print(progress_store)
        ReportFolder, Reportpath = JSONemptyReport(ProName=ProjData['ProjectName'])
        if Reportpath:
            #2. add Project info
            finalrep = JsonOperations(Reportpath)
            finalrepData = finalrep.read_file()
            finalrepData['Header']=ProjData
            finalrepData['Header']['UID'] = str(uuid.uuid4())
            #.start Test Execution one by one
            total = len(testcases)
            for i, test in enumerate(testcases, start=1):
                #Check stop flag
                if progress_store[job_id]["stop"]:
                    progress_store[job_id]["status"] = "stopped"
                    return
                # Execute Playwright test here,
                TCstartTime = datetime.now()
                TestRes = {
                    "UID":str(uuid.uuid4()),
                    "TestID":test['Header']['TestID'],
                    "TestName":test['Header']['TestName'],
                    "Description":test['Header']['Description'],
                    "Tags":test['Header']['Tags'],
                    "TestSuits":test['Header']['TestSuits'],
                    "Details":[],
                    "Remarks":"",
                    "StartTime":TCstartTime.isoformat(),
                    "EndTime":"",
                    "RunTime":"",
                    "Result":"NA"
                    }
                #Get the TCsteps____________________________________
                if len(test['Details'])>0:
                    await BaseObj.setup()
                    for TCStep in test['Details']:
                        StepsRes={"StepID":TCStep['Header']['StepID'],"SeqID":"NA","Description":TCStep['Header']['Description'],"Result":"Fail","Remarks":"","Details":[]}
                        #get actions for the TCstep_____________________________
                        for Action in TCStep['Details']:
                            #Results store for steps
                            ActionRes={"Action":Action['Action'],"Input":"NA","Result":"NA","Remarks":""}
                            UIRes={"result":"NA","Input":"NA","Remarks":"NA"}
                            #Basic paramets to perform ui checks
                            Xpath = TCStep['Header']['Xpath']
                            UIElement = TCStep['Header']['Type']
                            #Values
                            ActionValues =  json.loads(Action['Value'])
                            expected=None
                            if ActionValues['Type'] in ["Direct","NA"]:
                                expected=json.loads(ActionValues['Value']) if any(res in ActionValues['Value'] for res in ['{','[']) else ActionValues['Value']
                            elif ActionValues['Type'] == "Dynamic":expected=GetValuefromJSON(ActionValues['Value'])
                            if Action['Action'] =="Click":  UIRes = await UIAct.ElementClick(Xpath=Xpath)
                            elif Action['Action'] == "VerifyDropdownValues": UIRes = await UIAct.VerifyDropdownValues(Xpath=Xpath,UIElement=UIElement,Values=expected)
                            elif Action['Action'] == "SelectDropdownItem": UIRes = await UIAct.SelectDropdownItem(Xpath=Xpath,UIElement=UIElement,Value=expected)
                            elif Action['Action']== "SelectDropdownItem_Multiple": UIRes = await UIAct.SelectDropdownItem_Multiple(Xpath=Xpath,UIElement=UIElement,Values=expected)
                            elif Action['Action']== "VerifyText_Multiple": UIRes = await UIAct.VerifyText_Multiple(Xpath=Xpath,UIElement=UIElement,Values=expected)
                            elif Action['Action'] == "CompareElementImage": 
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                UIRes = await UIAct.CompareElementImage(Xpath=Xpath,Value=expected,ReportFolder=ReportFolder,ImageName=f"{test['Header']['TestID']}_{TCStep['Header']['StepID']}_{timestamp}.png",FileStorage_Mode=FileStorage_Mode)
                            elif Action['Action'] == "TimeOut": UIRes = await UIAct.TimeOut(Xpath=Xpath,Value=int(expected))
                            elif Action['Action'] == "APIValidation": UIRes = await UIAct.APIValidation(Xpath=Xpath,UIElement=UIElement,Value=expected)
                            elif Action['Action'] == "APIValidation_Payload": UIRes = await UIAct.APIValidation_Payload(Xpath=Xpath,UIElement=UIElement,Value=expected)
                            elif Action['Action'] == "TimeOut_Element": UIRes = await UIAct.TimeOut_Element(Xpath=Xpath)
                            elif Action['Action'] == "VerifyText": UIRes = await UIAct.VerifyText(Xpath=Xpath,Value=expected)
                            elif Action['Action'] == "FillValue": UIRes = await UIAct.FillValue(Xpath=Xpath,Value=expected)
                            elif Action['Action'] == "IsDisabled": UIRes = await UIAct.IsDisabled(Xpath=Xpath,UIElement=UIElement,Value=expected)
                            elif Action['Action'] == "IsVisible": UIRes = await UIAct.IsVisible(Xpath=Xpath,UIElement=UIElement,Value=expected)
                            elif Action['Action'] == "IsChecked": UIRes = await UIAct.IsChecked(Xpath=Xpath,UIElement=UIElement,Value=expected)
                            elif Action['Action'] == "Check": UIRes = await UIAct.ElementCheck(Xpath=Xpath,UIElement=UIElement,Value=expected)
                            elif Action['Action'] == 'CustomValidation': 
                                UIRes = await UIAct.CustomValidation(Xpath=Xpath,Value=expected)
                            elif Action['Action'] == 'SendFiles':
                                UIRes = await UIAct.SendFiles(Xpath=Xpath,Value=expected)
                            ActionRes['Result'] = UIRes['result']
                            ActionRes['Remarks'] = UIRes['Remarks']
                            ActionRes['Input'] = UIRes['Input']
                            StepsRes['Details'].append(ActionRes)
                        StepsRes['Result']='Fail' if 'Fail' in [res['Result'] for res in StepsRes['Details']] else 'Pass'
                        TestRes['Details'].append(StepsRes)
                else:TestRes['Remarks']=f"Test steps are not defined for the TestID:{test['Header']['TestID']}"
                await BaseObj.page.wait_for_timeout(2000)
                await BaseObj.teardown()
                
                progress_store[job_id]["current"] = i
                TestRes['EndTime']=datetime.now().isoformat()
                TestRes['RunTime'] = (datetime.now()-TCstartTime).total_seconds()
                stepRes = [res['Result'] for res in TestRes['Details']]
                TestRes['Result']="Fail" if "Fail" in stepRes  else "Pass"
                TestRes['PassPercentage'] = round((stepRes.count("Pass")/len(stepRes))*100,2)
                finalrepData['Details'].append(TestRes)
            progress_store[job_id]["status"] = "completed"   
            finalrep.update_file(finalrepData)
            #Upload Results to DB
            UploadRe = await UIcheckRtr.UploadResultJSON(FilePath=Reportpath)
    except Exception as e:
            traceback.print_exc()    
def CompareImages(Golden_IMG,Current_IMG,IMGpath,Filename):
    try:
        img1 = Image.open(Golden_IMG).convert("RGB")
        img2 = Image.open(Current_IMG).convert("RGB")
        # Resize img2 to match img1 size
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.LANCZOS)
        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        # Calculate absolute difference
        diff = np.abs(arr1 - arr2)
        # Calculate similarity
        max_diff = 255
        similarity = 100 - (np.mean(diff) / max_diff * 100)

        if similarity <95:
            diff = ImageChops.difference(img1, img2)
            diff.save(f"{IMGpath}/{Filename}_DIFF.png")
            return f"Match Percentage: {similarity:.2f}%", "Fail"
        else:return f"Match Percentage: {similarity:.2f}%", "Pass"
    except Exception as e:
        return f"Exception:{e}","Fail"
def GetValuefromJSON(path:str):
    try:
        JIPData=JIP.read_file()
        pathlist = path.split('->')
        value = JIPData
        for key in pathlist:
            value = value[key]
        return value
    except Exception as e:
        return None

#Generic fun for ensure the values of elements from the SW side API results, multiple elements can be veriyfied by maping the key. and type of the element.
def VerifyElementsWithAPIResults(Payload:dict):
    try:
        pass
    except Exception as e:
        print(e)
#_____________________________________________________________
#can be deleleted URL are getting from env
@router.get("/GetBaseURL/",summary="Get Base URL for Product and Category",tags=["UIRunner.General"])
async def GetBaseURL(Product:str,Catgory:str):
    pipeline =JPipedata['UIRunner']['General']['GetBaseURL']
    cursor = inputs_Collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise APIException(message=f"URL not found for {Product}, {Catgory}", code=404)
    return{"status":"success","code":200,"message":"URL Fetched Sucessfully","Details":{"data": result[0]['URL']}}
    
@router.post("/ExecuteUITest/",summary="Execute UI tests defined from the project",tags=["UIRunner.Execution"])
def ExecuteUITests(background_tasks: BackgroundTasks):
    #1. Get the Testcases from JSON
    JProData = JPro.read_file()
    index = 0
    while index < len(JProData):
        if JProData[index]['Header']=="UIProject":
            #Check project created 
            if len(JProData[index]['Details'])>0:
                if len(JProData[index]['Details']['Details'])>0:
                    #2. update in progress
                    job_id = str(uuid.uuid4())
                    progress_store[job_id] = {
                        "current": 0,
                        "total": len(JProData[index]['Details']['Details']),
                        "status": "running",
                        "stop": False
                    }
                    project = JProData[index]['Details'].copy()
                    del project['Details']
                    #3.send testcase to background process
                    background_tasks.add_task(run_ui_tests, job_id, JProData[index]['Details']['Details'],project)
                    return{"status":"success","code":200,"message":f"Execution started","Details":{"data": job_id}}
                else:raise APIException(message="Testcases are not defined for the project to execute.!", code=404)
            else:raise APIException(message="Project Not created to fetch the testcases", code=404)
        index+=1
    raise APIException(message="Project structure not created", code=404)
        
@router.get("/UIExecutionStatus/{JobID}/",summary="Get the UI Test Execution Status",tags=["UIRunner.Execution"])
async def UIExecutionStatus(JobID:str):
    if len(progress_store)>0:
        if JobID in progress_store:
            return{"status":"success","code":200,"message":f"successfully fetched the details of JobID:{JobID}","Details":{"data":progress_store[JobID]}}
        else:raise APIException(message=f"JOBID:{JobID} not found", code=404)
    else:raise APIException(message="JOB queue is empty", code=404)

@router.post("/ForceStop/{JOB_ID}",summary="Force stop the current UI execution",tags=["UIRunner.Execution"])
async def ForceStop(JOB_ID:str):
    if len(progress_store)>0:
        if JOB_ID in progress_store:
            progress_store[JOB_ID]['status'] = "stopped"
            return{"status":"success","code":200,"message":f"JOBID:{JOB_ID} Stoppped","Details":{'data':JOB_ID}}
        else:raise APIException(message=f"JOBID:{JOB_ID} not found", code=404)
    else:raise APIException(message="JOB queue is empty", code=404)
#SW API Validation##############
@router.get("/CheckPowerModePacket/{PowerMode}",summary="Check that the mentioned power mode has been applied in trace",tags=["SWAPI.Validation"])
def CheckPowerModePacket(PowerMode:str):
    #1.get the Packets data
    PacketData = APIVal.GetPacketData()
    if not PacketData:
        raise APIException(message="Packet data not found", code=404, details={'data':{'Result':'Fail'}})
    #2.Get the Active mode packet to check the power mode
    matchpkt = APIVal.GetMatchingPacketDetails(data=PacketData,Packet=["Active_Power_Mode",None])
    if not matchpkt:
        raise APIException(message="Active_Power_Mode packet not found", code=404, details={'data':{'Result':'Fail'}})
    #3.ensure the packet contains powerMode
    if PowerMode in matchpkt[1]:
        return {"status":"success","code":200,"message":f"Recived Packet:{matchpkt[1]}","Details":{'data':{'Result':'Pass','Packet':matchpkt[1]}}}
    else:return {"status":"success","code":200,"message":f"Recived Packet:{matchpkt[1]}","Details":{'data':{'Result':'Fail','Packet':matchpkt[1]}}}
    
@router.get("/GetScanedIPAddress/{Product}/{Category}",summary="Get list of Ipaddress from Network scanned",tags=["SWAPI.Validation"])
async def GetScanedIPAddress(Product:str,Category:str):
    values = APIVal.GetScannedIPaddress(Product,Category)
    if values:
        return{"status":"success","code":200,"message":f"Found IPaddress","Details":{'data':{'IPs':values}}}
    else:raise APIException(message="IPaddress not found", code=404)
    
# @router.get("/VerifyTesterConnectionStatus/",summary="Verfiy the connection status",tags=["SWAPI.Validation"])
# async def VerifyTesterConnectionStatus(Product:str,Category:str): 