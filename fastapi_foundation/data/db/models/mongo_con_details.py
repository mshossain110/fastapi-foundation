from pydantic import BaseModel, Field

class MongoConDetails(BaseModel):
    """
    MongoDB connection details.
    """

    # Database name
    db_name: str = Field(..., description="Database name")
    mongodb_url: str = Field(..., description="Database connection URL")