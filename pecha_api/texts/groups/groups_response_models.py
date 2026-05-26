from pydantic import BaseModel
from .groups_enums import GroupType

class GroupDTO(BaseModel):
    id: str
    type: str

class CreateGroupRequest(BaseModel):
    type: GroupType