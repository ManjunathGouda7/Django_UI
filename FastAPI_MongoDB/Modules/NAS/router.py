import sys

from fastapi import APIRouter,UploadFile, File, HTTPException
from FastAPI_MongoDB.Modules.NAS.service import SynologyClient
from fastapi.responses import StreamingResponse
from FastAPI_MongoDB.Modules.NAS.models import FileUpload
from FastAPI_MongoDB.SRC.Exceptions import APIException
import requests,os,shutil
from dotenv import load_dotenv

load_dotenv()

nas_password = os.getenv("NAS_PASSWORD")
if not nas_password:
    raise ValueError("NAS_PASSWORD environment variable is not set")

def get_root_path():
    """Returns the directory containing the .exe or the script"""
    if hasattr(sys, '_MEIPASS'):
        # If running as EXE, return the folder WHERE THE EXE IS LOCATED
        return os.path.dirname(sys.executable)
    # If running as a script, return the current directory
    return os.path.abspath(".")
FileStorage_Mode= os.getenv("FileStorage")
router = APIRouter(
    prefix="/NAS"
)
syno = SynologyClient(
    base_url=os.getenv("NAS_BASE_URL", "https://192.168.100.45:5001/webapi"),
    username=os.getenv("NAS_USERNAME", "DineshThambi"),
    password=nas_password
)
############################## Support function ##############################################

############################## API function ##############################################
@router.post("/UploadFile/",summary="Upload the file to NAS",tags=["NAS.UI"])
async def UploadFile(data:FileUpload):
    try:
        if FileStorage_Mode == "NAS":
            syno.ensure_login()
            url = f"{syno.base_url}entry.cgi"
            files = {
                "file":(data.source_path,await data.source_path.read())
            }
            data ={
                "api": "SYNO.FileStation.Upload",
                "version": "2",
                "method": "upload",
                "path": "/home/uploads",
                "_sid": syno.sid
            }
            response = requests.post(url, data=data, files=files, verify=False)
            if not response.json().get("success"):
                return{"status":"Error","code":500,"message":response.json(),"Details":{}}
            return{"status":"sucess","code":200,"message":"File Uploaded sucessfully","Details":{}}
        elif FileStorage_Mode == "Local":
            source = data.source_path
            destination_folder = data.destination_path

            # Check if source file exists
            if not os.path.isfile(source):
                return{"status":"Error","code":500,"message":"Source file not found","Details":{}}
            # Check if destination folder exists
            if not os.path.isdir(destination_folder):
                return{"status":"Error","code":500,"message":"Destination folder not found","Details":{}}
            # Copy file (keeps same filename)
            destination_path = os.path.join(destination_folder, os.path.basename(source))
            shutil.copy2(source, destination_path)
            return{"status":"success","code":200,"message":"File copied successfully","Details":{}}
        else: return{"status":"Error","code":404,"FileStorage mode not found":"","Details":{}}
                    
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)