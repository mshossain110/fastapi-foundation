from typing import Dict
from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dependency_injector.providers import Configuration
from pydantic import TypeAdapter

from fastapi_foundation.models.auth_models import UserClaims


LOG_OUT_STATUS_CODE = 410
TOKEN_EXPIRED_STATUS_CODE = 401

class AuthUtils:
    settings: Configuration
    
    def __init__(self, settings:Configuration):
        self.settings = settings
    
    @property
    def secret_key(self)->str:
        return self.settings['jwt_secret_key']
     
    @property
    def algorithm(self)->str:
        return self.settings['algorithm']
    
    @property
    def access_token_expire_minutes(self)->int:
        return int(self.settings['access_token_expire_minutes'])
    @property
    def refresh_token_expire_days(self)->int:
        return int(self.settings['refresh_token_expire_days'])
    
    def __init__(self,settings:Configuration):
        self.settings = settings

    def create_access_token(self,data: dict):
        expire = datetime.now() + timedelta(minutes=self.access_token_expire_minutes)
        return self.get_encoded_jwt(data,expire,"access_token")

    def create_refresh_token(self,data: dict):
        expire = datetime.now() + timedelta(days=self.refresh_token_expire_days)
        return self.get_encoded_jwt(data,expire,"refresh_token")
    
    def get_encoded_jwt(self,data: dict,expire: timedelta,scope: str):
        to_encode = data.copy()
        to_encode.update({"exp": expire, "scope": scope})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def validate_refresh_token(self,refresh_token:str)->tuple[str,str]:
        payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
        client_id: str = payload.get("sub")
        token_scope = payload.get("scope")
        print(f"client_id: {client_id}, token_scope: {token_scope}")
        if client_id is None or token_scope != "refresh_token":
            raise HTTPException(status_code= LOG_OUT_STATUS_CODE, detail="Invalid token")
        return client_id,token_scope
    
    def validate_access_token(self, access_token:str, secret: Dict[str, str] = {})->str:
        """
        Validates a JWT access token.
        Args:
            access_token (str): The JWT access token to validate.
            secret (Dict[str, str], optional): A dictionary containing optional `secret_key` and `algorithm`
                for decoding the token. Defaults to an empty dict, which falls back to instance attributes.
        """
        try:
            payload = jwt.decode(
                token=access_token, 
                key=secret.get('secret_key') or self.secret_key, 
                algorithms=[secret.get('algorithm') or self.algorithm],
                options={"verify_exp": False}  # Don't check expiration yet
            )
            user_id = payload.get("sub")
            token_scope = payload.get("scope")
            if user_id is None or token_scope != "access_token":
                raise HTTPException(status_code= LOG_OUT_STATUS_CODE, detail="Invalid token")
            exp = payload.get('exp', 0)
            is_expired = datetime.now().timestamp() > exp
            if is_expired:
                raise HTTPException(status_code= TOKEN_EXPIRED_STATUS_CODE, detail="Token expired")
            return user_id
        except JWTError as e:
            raise HTTPException(status_code= LOG_OUT_STATUS_CODE, detail=f"Invalid token: {e}")

    def decode_jwt(self, token: str, secret: Dict[str, str] = {}) -> UserClaims:
        """
        Validates a JWT access token and return the UserClaims.
        Args:
            token (str): The JWT access token to validate.
            secret (Dict[str, str], optional): A dictionary containing optional `secret_key` and `algorithm`
                for decoding the token. Defaults to an empty dict, which falls back to instance attributes.
        """
        return UserClaims(user_id=self.validate_access_token(access_token=token, secret=secret), access_token=token)
