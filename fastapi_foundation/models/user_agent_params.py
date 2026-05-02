from pydantic import BaseModel
from typing import Literal

class UserAgentParams(BaseModel):
    app_version:str
    version_code:int
    platform:Literal["android", "ios", "web"]
    os_version:str
    device_id:str
    device_model:str