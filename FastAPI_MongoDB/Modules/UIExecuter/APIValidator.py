import requests,json
from FastAPI_MongoDB.SRC.Util import JsonOperations
import FastAPI_MongoDB.Modules.UIchecks.router  as UIcheckRtr
import asyncio

class PacketModule():
    def __init__(self):
        pass
    #######General Functions
    def GetSWAPIResults(self,API:str,Payload):
        try:
            res = requests.get("http://localhost:2004/api/Plot/GetCCLinePackets")
            if res.status_code==200:
                return res.json()
            return None
        except Exception as e:
            return None
    def GetJSONDatafromAPI(self,URL:str,Params=None):
        try:
            res = requests.get(URL,params=Params)
            res.raise_for_status()
            return res.json()
        except requests.exceptions as e:
            print("API Error:",e)
            return None

    ##################
    def GetPacketData(self):
        try:
            res = requests.get("http://localhost:2004/api/Plot/GetCCLinePackets")
            if res.status_code==200:
                return res.json()
            return None
        except Exception as e:
            return None
    def GetMatchingPacketDetails(self,data:dict,Packet:list[str,str]):
        for pkt in data:
            if Packet[0] in pkt['pktType']:
                return [pkt['rowIndex'],pkt['pktType'],pkt['value'],pkt['startTime'],pkt['stopTime']]
        return None
    def GetScannedIPaddress(self,Product,Category):
        try:
            IPs = []
            if Product=="MPP":
                if Category=="TPR":
                    pass
                elif Category=="TPT":
                    res = requests.get("http://localhost:2004/api/ConnectionSetup/DiscoverIPAddress")
                    if res.status_code==200:
                        data = res.json()
                        if len(data)>0:
                            for rec in data:
                                IPs.append(rec['ipAddress'])
                            return IPs
            return None
        except Exception as e:
            return None
    
    #using connect api to verify the  connection status labels
    def VerifyConnectionStatus(self):
        try:
            #1.CALL Connection API and get the results
            res = requests.get("http://localhost:2004/api/ConnectionSetup")
            if res.status_code==200:
                print(res.json())
        except Exception as e:
            return None

class JSONBasedValidation():
    #To verify that the json values are present on the UI element
    async def VerifyUIElementsValueFromJSON(payload:dict):
        try:
            #1.Load the JSON data
            Jobj = JsonOperations(payload['JSONFilePath'])
            Jdata = Jobj.read_file()
            #2. Iterate UIElement and verify
            for UIElmnt in payload['UIElements']:
                #1.get the Xpath
                pathli = UIElmnt['UIElement'].split('->')
                elmtres = await UIcheckRtr.GetElement(Product=pathli[0],Category=pathli[1],Webpage=pathli[2],Frame=pathli[3],ElementName=pathli[4])

                print(elmtres)
        except Exception as e:
            return None
# obj = PacketModule()
# obj.VerifyConnectionStatus()

# packets = obj.GetPacketData()
# res = obj.GetMatchingPacketDetails(data=packets,Packet=["Active_Power_Mode",None])
# print(res)

Payload={
	"JSONFilePath" : "D:\\Fullstack\\assets\\LocalStorage\\FileStorage\\UIChecks\\MPP\\TPR\\SampleESDF_MPP_TPR.json",
	"UIElements" :[
		{
            "JSONFilePath" : "assets\\LocalStorage\\FileStorage\\UIChecks\\MPP\\TPR\\SampleESDF_MPP_TPR.json",
            "UIElement_Path":"MPP->TPR->TestConfiguration->CreateProject_SDFSelection->SpecificationSupported_Dropdown",
            "Expvalue_JSONPath":"SpecificationSupported",
            "UIAction":""}
	]
}
# obj = JSONBasedValidation()
# asyncio.run(JSONBasedValidation.VerifyUIElementsValueFromJSON(Payload))



