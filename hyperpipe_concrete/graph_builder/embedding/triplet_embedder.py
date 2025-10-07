from typing import List
from ..models import Entity, Relationship, Triplet, GraphBuilderResult
from hyperpipe_core import AsyncStep
import asyncio
from ...hyperengine import Embedder

class TripletEmbedder(AsyncStep):
    def __init__(
        self,
        embedder: Embedder,
        name: str = "TripletEmbedder",
        entity_name_weight: float = 0.6,
        entity_label_weight: float = 0.4,
    ):
        super().__init__()
        self.name = name
        self.embedder = embedder
        self.entity_name_weight = entity_name_weight
        self.entity_label_weight = entity_label_weight

            

    

    def extract_entities_from_triplets(self, triplets: List[Triplet]) -> List[Entity]:
        entities_list = []
        for triplet in triplets:
            if triplet.head.embedding is None:
                entities_list.append(triplet.head)
            if triplet.tail.embedding is None:
                entities_list.append(triplet.tail)
        return entities_list

    def extract_relationships_from_triplets(self, triplets: List[Triplet]) -> List[Relationship]:
        relationships_list = []
        for triplet in triplets:
            if triplet.relation.embedding is None:
                relationships_list.append(triplet.relation)
        return relationships_list

    def deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        unique_entities = []
        for entity in entities:
            if entity not in unique_entities:
                unique_entities.append(entity)
        return unique_entities

    def deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        unique_relationships = []
        for relationship in relationships:
            if relationship not in unique_relationships:
                unique_relationships.append(relationship)
        return unique_relationships



    async def embed_entities(self, entities: List[Entity]) -> List[Entity]:
        
        entities_to_process = [entity for entity in entities if entity.embedding is None and entity.name and entity.label]
        
        if not entities_to_process:
            return entities
        
        names = [entity.name.lower() for entity in entities_to_process]
        labels = [entity.label.lower() for entity in entities_to_process]

            
        name_task = self.embedder.embed(names)
        label_task = self.embedder.embed(labels)
        name_embeddings, label_embeddings = await asyncio.gather(name_task, label_task)
        
        
        for i, entity in enumerate(entities_to_process):
            if name_embeddings[i] is not None and label_embeddings[i] is not None:
                combined_embedding = (
                    self.entity_name_weight * name_embeddings[i] +
                    self.entity_label_weight * label_embeddings[i]
                )
                entity.embedding = combined_embedding.tolist()
                entity.label_embedding = label_embeddings[i].tolist()
                entity.name_embedding = name_embeddings[i].tolist()
     
        return entities

    async def embed_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        
        relationships_to_process = [rel for rel in relationships if rel.embedding is None and rel.name]
        
        if not relationships_to_process:
            return relationships
        
        names = [rel.name.lower() for rel in relationships_to_process]
        name_embeddings = await self.embedder.embed(names)
        
        for i, relationship in enumerate(relationships_to_process):
            if name_embeddings[i] is not None:
                relationship.embedding = name_embeddings[i].tolist()
     
        return relationships

    async def execute(self, result: GraphBuilderResult) -> GraphBuilderResult:     
        
        entities_from_triplets = self.extract_entities_from_triplets(result.relation_extraction)
        relationships_from_triplets = self.extract_relationships_from_triplets(result.relation_extraction)
        
        self.log.info(f"Processing {len(entities_from_triplets)} entities and {len(relationships_from_triplets)} relationships for embedding")
    
        unique_entities = []
        entity_groups = [] 
        
        for entity in entities_from_triplets:
            found_group = None
            for i, unique_entity in enumerate(unique_entities):
                if entity == unique_entity:
                    found_group = i
                    break
            
            if found_group is not None:
                entity_groups[found_group].append(entity)
            else:
                unique_entities.append(entity)
                entity_groups.append([entity])
        
        unique_relationships = []
        relationship_groups = []
        
        for relationship in relationships_from_triplets:
            found_group = None
            for i, unique_relationship in enumerate(unique_relationships):
                if relationship == unique_relationship:
                    found_group = i
                    break
            
            if found_group is not None:
                relationship_groups[found_group].append(relationship)
            else:
                unique_relationships.append(relationship)
                relationship_groups.append([relationship])
        


        
        
        entity_task = self.embed_entities(unique_entities)
        relationship_task = self.embed_relationships(unique_relationships)
        
        await asyncio.gather(entity_task, relationship_task)
        
        embedded_entities = 0
        embedded_relationships = 0
        
        for i, unique_entity in enumerate(unique_entities):
            if unique_entity.embedding: 
                for entity in entity_groups[i]:
                    entity.embedding = unique_entity.embedding
                    entity.label_embedding = unique_entity.label_embedding
                    entity.name_embedding = unique_entity.name_embedding
                embedded_entities += 1
        
        for i, unique_relationship in enumerate(unique_relationships):
            if unique_relationship.embedding: 
                for relationship in relationship_groups[i]:
                    relationship.embedding = unique_relationship.embedding
                embedded_relationships += 1
        
        self.log.info(f"Embedding completed: {embedded_entities} entities, {embedded_relationships} relationships embedded")
        return result

    def save_result(self, step_result: GraphBuilderResult, result: GraphBuilderResult):
        result = step_result
        return result
