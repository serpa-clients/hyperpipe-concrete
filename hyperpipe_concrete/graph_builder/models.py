from typing import Optional, List, Any
from pydantic import BaseModel, Field
from hyperpipe_core import Result

class EntityMetadata(BaseModel):
    context: str
    start_index: int
    sentence_id: Optional[int] = None
    chunk_id: Optional[str] = None
    source: Optional[str] = None

class Entity(BaseModel):
    name: str
    label: Optional[str] = None
    summary: Optional[str] = None
    metadata: Optional[EntityMetadata] = None
    embedding: Optional[List[float]] = Field(default=None, repr=False)
    label_embedding: Optional[List[float]] = Field(default=None, repr=False)
    name_embedding: Optional[List[float]] = Field(default=None, repr=False)
    alternatives: List['Entity'] = Field(default_factory=list)
    special_type: Optional[str] = None
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Entity):
            return self.name == other.name and self.label == other.label
        return False

class Relationship(BaseModel):
    name: str
    label: Optional[str] = None
    embedding: Optional[List[float]] = Field(default=None, repr=False)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Relationship):
            return self.name == other.name and self.label == other.label
        return False

class TripletMetadata(BaseModel):
    context: str
    start_position: int
    end_position: int
    chunk_id: Optional[str] = None

class Triplet(BaseModel):
    head: Entity
    relation: Relationship
    tail: Entity
    metadata: TripletMetadata
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Triplet):
            return (self.head == other.head and 
                    self.relation == other.relation and 
                    self.tail == other.tail)
        return False

class GraphBuilderResult(BaseModel):
    model_config = {"extra": "allow"}
    
    entity_extraction: list[Entity] = Field(default_factory=list)
    relation_extraction: list[Triplet] = Field(default_factory=list)

