from pydantic import BaseModel
from typing import List


class EntityLLMOutput(BaseModel):
    name: str
    label: str
    summary: str


class RelationshipLLMOutput(BaseModel):
    name: str
    label: str


class TripletLLMOutput(BaseModel):
    head: EntityLLMOutput
    relation: RelationshipLLMOutput
    tail: EntityLLMOutput


class EntitiesListResponse(BaseModel):
    entities: List[EntityLLMOutput]


class RelationsListResponse(BaseModel):
    relations: List[TripletLLMOutput]