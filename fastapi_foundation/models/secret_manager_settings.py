import json
from typing import Dict, Any
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

import logging
logger = logging.getLogger("")


class SecretManagerSettings:
    """AWS Secrets Manager client to retrieve secrets."""
    
    def __init__(self, secret_name: str, region_name: str):
        self.secret_name = secret_name
        self.region_name = region_name
        
    def get_secret(self,aws_access_key_id:str,aws_secret_access_key:str) -> Dict[str, Any]:
        """
        Retrieve a secret from AWS Secrets Manager.
        Returns a dictionary of key-value pairs from the secret.
        """
        client = boto3.client(
            'secretsmanager',
            aws_access_key_id = aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=self.region_name
        )
        
        try:
            response = client.get_secret_value(SecretId=self.secret_name)
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                # Binary secrets need to be decoded
                return json.loads(response['SecretBinary'].decode('utf-8'))
        except Exception as e:
            
            if isinstance(e, ClientError):
                error_code = e.response.get('Error', {}).get('Code')
                
                if error_code == 'ResourceNotFoundException':
                    error_details = f"Secret {self.secret_name} not found"
                elif error_code == 'InvalidParameterException':
                    error_details = "Invalid parameter provided"
                elif error_code == 'InvalidRequestException':
                    error_details = "Invalid request"
                elif error_code == 'DecryptionFailureException':
                    error_details = "Decryption failure"
                elif error_code == 'InternalServiceErrorException':
                    error_details = "Internal service error"
                else:
                    error_details = f"Unknown error: {error_code}"
            else:
                error_code = None
                error_details = str(e)
                
            # Log errors
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "secret_name": self.secret_name,
                "region_name": self.region_name,
                "source": "SecretManagerSettings",
                "type": "error",
                "error": error_details,
                "error_code": error_code,
            }
            logger.error(json.dumps(error_log))
            
            return {}