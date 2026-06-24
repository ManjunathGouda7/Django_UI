import asyncio
from functools import wraps
import ast, os, json
from datetime import datetime
from PIL import Image, ImageChops
import numpy as np
from FastAPI_MongoDB.SRC.Util import JsonOperations,GeneralFunctions
import FastAPI_MongoDB.Modules.UIchecks.router  as UIcheckRtr
from FastAPI_MongoDB.SRC.logger import logger

def HandleActionExceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return {"result": "Fail","Input":"NA","Remarks": str(e)}
    return wrapper

class UIActionsModule():
    def __init__(self,BaseObj):
        self.BaseObj = BaseObj

    #1. Simply click the UI Element 
    @HandleActionExceptions
    async def ElementClick(self,Xpath:str):
        await self.BaseObj.page.locator(Xpath).click()
        return {"result":"Pass","Input":"NA","Remarks":"NA"}
    
    #2. Simply clear the UI Element  contenet
    @HandleActionExceptions
    async def ElementClear(self,Xpath:str):
        await self.BaseObj.page.locator(Xpath).clear()
        return {"result":"Pass","Input":"NA","Remarks":"NA"}
    
    #3. Speciically for the checkbox , if the element is uncheck the action will make the element checked
    @HandleActionExceptions
    async def ElementCheck(self,Xpath:str,UIElement:str,Value:str):
        elemnt = await self.BaseObj.page.locator(Xpath).is_checked()
        if Value=="True":
            if not elemnt:
                await self.BaseObj.page.locator(Xpath).check()
                return {"result":"Pass","Input":"Check","Remarks":"Element checked sucessfully"}
            else:return {"result":"Pass","Input":"Check","Remarks":"Element found checked"}
        elif Value=="False":
            if elemnt:
                await self.BaseObj.page.locator(Xpath).uncheck()
                return {"result":"Pass","Input":"Check","Remarks":"Element unchecked sucessfully"}
            else:return {"result":"Pass","Input":"Check","Remarks":"Element found unchecked"}

    #4.Verfiy that the provided text is matching with Element content
    @HandleActionExceptions
    async def VerifyText(self,Xpath:str,Value:str):
        txt = await self.BaseObj.page.locator(Xpath).input_value()
        if Value == txt:
            return {"result":"Pass","Input":Value,"Remarks":f"Expected value:{Value}| Available Value:{txt}"}
        else: return {"result":"Fail","Input":Value,"Remarks":f"Expected value:{Value}| Available Value:{txt}"}

    #5. Verify that the provided list of text is matching with the Element contents, pattern matching
    @HandleActionExceptions
    async def VerifyText_Multiple(self,Xpath:str,UIElement:str,Values:list):
        #Verify list of selected dropdown(checkbox) values match with expected
        logger.info(f"VerifyText_Multiple :{Values}")
        if UIElement == "DropDown_Checkbox":
            inputs = self.BaseObj.page.locator(f"{Xpath}//input")
            count = await inputs.count()
            ckdValues=[]
            j = 1
            while j <= count:
                if await self.BaseObj.page.locator(f"({Xpath}//input)[{j}]").is_checked():
                    ckdValues.append(await self.BaseObj.page.locator(f"({Xpath}//label)[{j}]").inner_text())
                j+=1
            if len(ckdValues)>0:
                if all(res in ckdValues for res in Values):
                    return {"result":"Pass","Input":','.join(map(str,Values)),"Remarks":f"Dropdown selected values::{','.join(map(str,ckdValues))}|Patterns to be verified:{','.join(map(str,Values))}"}
                else:return {"result":"Fail","Input":','.join(map(str,Values)),"Remarks":f"Dropdown selected values::{','.join(map(str,ckdValues))}|Patterns to be verified:{','.join(map(str,Values))}"}
            else:return {"result":"Fail","Input":','.join(map(str,Values)),"Remarks":f"Dropdown selected values::{','.join(map(str,ckdValues))}|Patterns to be verified:{','.join(map(str,Values))}"}
        else:
            txt = await self.BaseObj.page.locator(Xpath).inner_text()
            if all(res in txt for res in Values):
                return {"result":"Pass","Input":','.join(map(str,Values)),"Remarks":f"Element Text={txt} and Patterns to be verified:{','.join(map(str,Values))}"}
            else:return {"result":"Fail","Input":','.join(map(str,Values)),"Remarks":f"Element Text={txt} and Patterns to be verified:{','.join(map(str,Values))}"}

    #6. Set wait time in ns , which will use after performing any action on Element.
    @HandleActionExceptions
    async def TimeOut(self,Xpath:str,Value:int):
        await self.BaseObj.page.wait_for_timeout(Value)
        return {"result":"Pass","Input":Value,"Remarks":f"Set wait time for {Value}ms."}

    #7. Wait until the Element disabled or unavailable. Using mostly with spin element.
    @HandleActionExceptions
    async def TimeOut_Element(self,Xpath:str):
        await self.BaseObj.page.locator(Xpath).wait_for(state="detached")
        return {"result":"Pass","Input":"NA","Remarks":f"Applied wait for the element."}
    
    #8. Fill the provided value on a element
    @HandleActionExceptions
    async def FillValue(self,Xpath:str,Value:str):
        await self.BaseObj.page.locator(Xpath).fill(Value)
        return {"result":"Pass","Input":Value,"Remarks":f"Filled the value: {Value}"}

    #9. Value = True : if  the Element is avilable on webpage set the result as Pass
    #   Value = False : if the Element is not available on Webpage set the result as Pass
    @HandleActionExceptions
    async def IsVisible(self,Xpath:str,UIElement:str,Value:str):
        elemnt = await self.BaseObj.page.locator(Xpath).is_visible()
        if Value=="True":
            return {"result":"Pass","Input":"Visible","Remarks":f"Element visible as expected"} if elemnt else {"result":"Fail","Input":"Visible","Remarks":f"Element Invisible, expected to be visible"}
        elif Value=="False":
            return {"result":"Fail","Input":"Invisible","Remarks":f"Element visible, expected to be invisible"} if elemnt else {"result":"Pass","Input":"Invisible","Remarks":f"Element Invisible as expected"}
    #10.    Value = True : if  the Element is Eabled on webpage set the result as Pass
    #       Value = False : if the Element is Enabled on Webpage set the result as Pass
    @HandleActionExceptions
    async def IsDisabled(self,Xpath:str,UIElement:str,Value:str):
        if UIElement=="DropDown_Checkbox":
            elemnt = await self.BaseObj.page.locator(f"{Xpath}//button").is_disabled()
        else:
            elemnt = await self.BaseObj.page.locator(Xpath).is_disabled()
        if Value=="True":
            return {"result":"Pass","Input":"Disabled","Remarks":f"Element found disabled as expected"} if elemnt else {"result":"Fail","Input":"Disabled","Remarks":f"Element found Enabled, expected to be disabled"}
        elif Value=="False":
            return {"result":"Fail","Input":"Enabled","Remarks":f"Element found disabled, expected to be enabled"} if elemnt else {"result":"Pass","Input":"Enabled","Remarks":f"Element found enabled as expected"}
    
    #11.    Value = True : if  the checkbox is marked as checked then set the result set as Pass
    #       Value = False : if the checkbox is marked as unchecked  then the result set as Pass
    @HandleActionExceptions
    async def IsChecked(self,Xpath:str,UIElement:str,Value:str):
        elemnt = await self.BaseObj.page.locator(Xpath).is_checked()
        if Value=="True":
            return {"result":"Pass","Input":"Checked","Remarks":f"Element found checked as expected"} if elemnt else {"result":"Fail","Input":"Checked","Remarks":f"Element found unchecked, expected to be checked"}
        elif Value=="False":
            return {"result":"Fail","Input":"Unchecked","Remarks":f"Element found checked, expected to be unchecked"} if elemnt else {"result":"Pass","Input":"Unchecked","Remarks":f"Element found unchecked as expected"}

    #12. Verify that the provided list of values are present in the dropdown
    @HandleActionExceptions
    async def VerifyDropdownValues(self,Xpath:str,UIElement:str,Values:list):
        if UIElement=="DropDown_Checkbox":
            options = await self.BaseObj.page.locator(Xpath+"//label").all_text_contents()
        elif UIElement=="DropDown":
            options = await self.BaseObj.page.locator(Xpath+"/option").all_text_contents()
        #Ensure that the dropdown has smiler values as ex[pected
        if sorted(Values)==  sorted(options):
            return {"result":"Pass","Input":','.join(map(str,Values)),"Remarks":f"Expected values:{','.join(map(str,Values))}| Available Values:{','.join(map(str,options))}"}
        else:return {"result":"Fail","Input":','.join(map(str,Values)),"Remarks":f"Expected values:{','.join(map(str,Values))}| Available Values:{','.join(map(str,options))}"}
    
    #13. choose the single dropdown Item from the dropdown
    @HandleActionExceptions
    async def SelectDropdownItem(self,Xpath:str,UIElement:str,Value:str):
        if UIElement=="DropDown":
            await self.BaseObj.page.locator(Xpath).select_option(label=Value)
            return {"result":"Pass","Input":Value,"Remarks":f"selected {Value}"}
        elif '//span' in Xpath:
            await self.BaseObj.page.locator(Xpath).click()
            await self.BaseObj.page.locator(f"{Xpath}/following-sibling::div[1]/a[text()='{Value}']").click()
            return {"result":"Pass","Input":Value,"Remarks":f"selected {Value}"}

    #14. choose list of items on the dropdown, specially for the checkbox dropdown
    @HandleActionExceptions
    async def SelectDropdownItem_Multiple(self,Xpath:str,UIElement:str,Values:list):
        if UIElement == "DropDown_Checkbox":
            await self.BaseObj.page.locator(f"{Xpath}/button").click()
            for val in Values:
                await self.BaseObj.page.locator(f"{Xpath}//label[text()='{val}']").click()
            await self.BaseObj.page.locator(f"{Xpath}/button").click()
            return {"result":"Pass","Input":','.join(map(str,Values)),"Remarks":f"selected values {','.join(map(str,Values))}"}
    
    #15. Ensure that the provided API (SW) is being called while performing the any action on the element
    @HandleActionExceptions
    async def APIValidation(self,Xpath:str,UIElement:str,Value:str):
        with self.BaseObj.page.expect_response(Value) as res_info:
            #for now button click API validation is added. if required based on other actions API validation can be added
            await self.BaseObj.page.locator(Xpath).click()
        if res_info.value.status !=200:
            return {"result":"Pass","Input":Value,"Remarks":f"API:{Value}"}
        else:{"result":"Fail","Input":Value,"Remarks":f"API not triggered:{Value}"}
    
    #16. Ensure that the provided API (SW) along with the payload is being called while performing the any action on the element
    @HandleActionExceptions
    async def APIValidation_Payload(self,Xpath:str,UIElement:str,Value:str):
        InputData = json.loads(Value)
        apiurl = InputData['Function']
        payload_str = InputData['Payload']
        payload_str = payload_str.replace("true", "True").replace("false", "False")
        payload = json.loads(payload_str)
        with self.BaseObj.page.expect_request(apiurl) as req_info,\
                self.BaseObj.page.expect_response(apiurl) as res_info:
                    await self.BaseObj.page.locator(Xpath).click()
        #verify API
        if res_info.value.status !=200 or req_info.value.post_data_json != payload:
            return {"result":"Pass","Input":Value,"Remarks":f"API success with payload"} 
        else:return {"result":"Fail","Input":Value,"Remarks":f"API unsuccess with payload"} 
        # ActionRes['Remarks']=f"API called : status:{res_info.value.status}|Payload Received:{json.dumps(req_info.value.post_data_json)}"


    #17. Take the current element SS and match with provided SS
    @HandleActionExceptions
    async def CompareElementImage(self,Xpath:str,Value:str,ReportFolder:str,ImageName:str,FileStorage_Mode:str):
        element = self.BaseObj.page.locator(Xpath)
        #Save current SS in report folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await element.evaluate("""
            el => {
                el.style.height = el.scrollHeight + 'px';
                el.style.overflow = 'visible';
            }""")
        await self.BaseObj.page.wait_for_timeout(1000)
        currentPath =os.path.join(ReportFolder,"IMG",f"{ImageName}_{timestamp}.png")
        await element.screenshot(path=currentPath)
        #Generate Golden Image path with FileStorage Mode, if it's local refere it by as it is. if it's Cloud / NAS move the image to temp and share the path
        if FileStorage_Mode =="Local":
            GoldenPath = f"SRC/LocalStorage/FileStorage/UIChecks/{Value}"
        Remarks, result = self.CompareImages(GoldenPath,currentPath,f"{ReportFolder}/IMG/",ImageName)
        return {"result":result,"Input":Value,"Remarks":Remarks} 
    
    #18. to perform the custom validation cases, where the automation API provided alogn with payload to perform the 
    @HandleActionExceptions
    async def CustomValidation(self,Xpath:str,Value:dict):
        payload_str = Value['Payload']
        payload_str = payload_str.replace("true", "True").replace("false", "False")
        Payload = json.loads(payload_str)
        method = Value['Function']
        custUIAct = CustomUIActionsModule(self.BaseObj)
        if method == 'VerifyUIElementValueFromJSON':
            return await custUIAct.VerifyUIElementValueFromJSON(payload=Payload)

    #19.Helps to upload the files 
    @HandleActionExceptions
    async def SendFiles(self,Xpath:str,Value:str):
        await self.BaseObj.page.locator(Xpath).set_input_files(Value)
        return {"result":"Pass","Input":Value,"Remarks":f"File {Value} uploaded sucessfully."}
    def CompareImages(self,Golden_IMG,Current_IMG,IMGpath,Filename):
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


class CustomUIActionsModule():
    def __init__(self,BaseObj):
        self.BaseObj = BaseObj

    #.1 Verify that the UI Element values are matching with the JOSN file values
    @HandleActionExceptions
    async def VerifyUIElementValueFromJSON(self,payload:dict):
        #1.Load the JSON data
        Jobj = JsonOperations(payload['JSONFilePath'])
        if Jobj:
            Jdata = Jobj.read_file()
            pathli = payload['UIElement_Path'].split('->')
            elmtres = await UIcheckRtr.GetElement(Product=pathli[0],Category=pathli[1],Webpage=pathli[2],Frame=pathli[3],ElementName=pathli[4])
            if elmtres['status']=='success':
                UIobj = UIActionsModule(self.BaseObj)
                expval = GeneralFunctions.GetValuefromJSON(path=payload['Expvalue_JSONPath'],Jdata=Jdata)
                if expval:
                    if payload['UIAction'] == "VerifyText": return await UIobj.VerifyText(Xpath=elmtres['Details']['data']['Xpath'],Value=str(expval))
                    elif payload['UIAction'] == "VerifyText_Multiple": return await UIobj.VerifyText_Multiple(Xpath=elmtres['Details']['data']['Xpath'],UIElement=elmtres['Details']['data']['Type'],Values=list(map(str,expval)))
                else:return {"result":"Fail","Input":"NA","Remarks":f"Expected value not found in the JOSN file, for the path:{payload['Expvalue_JSONPath']}"}
            else:return {"result":"Fail","Input":"NA","Remarks":f"UI Element not found for the path:{payload['UIElement_Path']}"}
        else:return {"result":"Fail","Input":"NA","Remarks":f"UI Element not found for the path:{payload['UIElement_Path']}"}

# Payload={
#             "JSONFilePath" : "assets\\LocalStorage\\FileStorage\\UIChecks\\MPP\\TPR\\SampleESDF_MPP_TPR.json",
#             "UIElement_Path":"MPP->TPR->TestConfiguration->CreateProject_SDFSelection->SpecificationSupported_Dropdown",
#             "Expvalue_JSONPath":"SpecificationSupported",
#             "UIAction":"VerifyText"}

# obj = CustomUIActionsModule()

# asyncio.run(CustomUIActionsModule.VerifyUIElementValueFromJSON(Payload))