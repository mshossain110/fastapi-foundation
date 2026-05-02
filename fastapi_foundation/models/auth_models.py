from pydantic import BaseModel

class UserClaims(BaseModel):
    user_id: str
    access_token: str