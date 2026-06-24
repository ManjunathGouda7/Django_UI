from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from bson import ObjectId

class TestcaseHeader(BaseModel):
    TestID:str =Field(max_length=9,min_length=9)
    TestName: str = Field(min_length=2)
    Description: Optional[str] = None
    Product: str = Field(min_length=2)
    Category: str = Field(min_length=2)
    Testsuits: List[str]
    TestTags: List[str]
    Details: List[dict]

class UpdateTestcaseHeader(BaseModel):
    TestName: Optional[str] = Field(default=None, min_length=2)
    Description: Optional[str] = None
    Product: Optional[str] = Field(default=None, min_length=2)
    Category: Optional[str] = Field(default=None, min_length=2)
    Testsuits: Optional[List[str]] = None
    TestTags: Optional[List[str]] = None
    # Details: Optional[List[dict]] = None

class TestSteps(BaseModel):
    StepID:str = Field(min_length=13,max_length=13)
    Description:str=Field(min_length=3)
    WebpPage:str=Field(min_length=3)
    Frame:str=Field(min_length=3)
    Element:str=Field(min_length=3)
    ElementPath:str=Field(min_length=3)
    Details:List[dict]

class UpdateTestSteps(BaseModel):
    Description:str=Field(min_length=3)
    WebpPage:str=Field(min_length=3)
    Frame:str=Field(min_length=3)
    Element:str=Field(min_length=3)
    ElementPath:str=Field(min_length=3)

class StepActions(BaseModel):
    Action:str
    Value:str

class ProjectData(BaseModel):

    ProjectName:str=Field(min_length=3)
    TestEngineer:Optional[str]=None
    TestLab:Optional[str]=None
    SWversion1:Optional[str]=None
    SWversion2:Optional[str]=None
    FF1:Optional[str]=None
    FF2:Optional[str]=None
    FF3:Optional[str]=None
    FF4:Optional[str]=None
    Remarks:Optional[str]=None
    Product:str
    Category:str
    Details :list[dict]

class ProjectUpdateData(BaseModel):
    ProjectName:str=Field(min_length=3)
    TestEngineer:Optional[str]=None
    TestLab:Optional[str]=None
    SWversion1:Optional[str]=None
    SWversion2:Optional[str]=None
    FF1:Optional[str]=None
    FF2:Optional[str]=None
    FF3:Optional[str]=None
    FF4:Optional[str]=None
    Remarks:Optional[str]=None

#### Models for TestData for execution
class TestHeader_run(BaseModel):
    TestID:str
    TestName:str
    Description:str
    Tags: Optional[List[str]] = None
    TestSuits: Optional[List[str]] = None
class Steps_run(BaseModel):
    StepID:str
    Description:str
    ElementPath:str
    Xpath:str
    Type:str
class Actions_run(BaseModel):
    Action:str
    Value:str
class AllSteps_run(BaseModel):
    Header:Steps_run
    Details:List[Actions_run]

class TestData_run(BaseModel):
    Header:TestHeader_run
    Details:List[AllSteps_run]