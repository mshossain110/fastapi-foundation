from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer
from bson import ObjectId

class MongoBaseModel(BaseModel):
    """Base model with MongoDB ObjectId handling."""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    created_at:  datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @field_validator('id')
    def validate_id(cls, v):
        if not isinstance(v, ObjectId):
            if not ObjectId.is_valid(v):
                raise ValueError('Invalid ObjectId')
            v = ObjectId(v)
        return v

    @field_serializer('id', when_used='json')  # Only serialize to string when used in JSON
    def serialize_id(self, v):
        return str(v)

    def to_mongo(self) -> dict:
        """Convert to MongoDB document format."""
        # Use mode='python' to prevent field serializers from converting ObjectIds to strings
        data = self.model_dump(mode='python', by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data

    @classmethod
    def from_mongo(cls, data: dict) -> Optional['MongoBaseModel']:
        """Create model instance from MongoDB document."""
        if not data:
            return None
        return cls.model_validate(data)