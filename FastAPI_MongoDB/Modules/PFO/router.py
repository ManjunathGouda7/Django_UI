from FastAPI_MongoDB.SRC.Util import DBmodule,JsonOperations,GeneralFunctions
from fastapi import APIRouter
from FastAPI_MongoDB.SRC.Exceptions import APIException

DBmod = DBmodule()
# UIRunnnerPW = UIRunner_Playwright()
PFOData_Collection = DBmod.get_collection("UIDB","PFOData")
router = APIRouter(
    prefix="/PFO"
)
JPipe = JsonOperations(GeneralFunctions.get_path("FastAPI_MongoDB/Modules/PFO/pipelines.json"))
JPipedata = JPipe.read_file()

############################## Support function ##############################################


@router.get("/GetPFOData/",summary="Get PFO data RP and PFO to plot the charts",tags=["PFO.ChartData"])
async def GetPFOData():
    try:
        pipeline =JPipedata['PFOData']['PFOMain']
        cursor = PFOData_Collection.aggregate(pipeline)
        result = await cursor.to_list()
        if not result:
            return{"status":"error","code":404,"message":f"Data not found for the passed filters","Details":{}}
        return{"status":"success","code":200,"message":"PFO Data fetched Sucessfully","Details":{"data": result}}
    except Exception as e:
        raise APIException(message=f"Exception occurred: {str(e)}", code=500)