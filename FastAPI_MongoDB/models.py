from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class ResultHeader(BaseModel):
    UID: str
    TestEngineer: str
    TestLab: str
    Product : str
    Category:str
    SWversion1:str
    SWversion2:str
    FF1:str
    FF2:str
    FF3:str
    FF4:str
    Remarks:str
    ProjectName:str
class ResultHeaderResponse(ResultHeader):
    id: str

class TestcaseHeader(BaseModel):
    UID:str
    HeaderUID:str
    TestID:str
    TestName:str
    Description:str
    Tags:str
    TestSuits:str
    StartTime:str
    EndTime:str
    RunTime:str
    Result:str
    PassPercentage:str
    Remarks:str

class TestcaseSteps(BaseModel):
    TestUID:str
    StepID:str
    SeqID:str
    Description:str
    Result:str
    Remarks:str