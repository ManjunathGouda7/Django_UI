from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from bson import ObjectId

class FileUpload(BaseModel):
    source_path :str
    destination_path : str