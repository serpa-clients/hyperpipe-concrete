from typing import List
from hyperpipe_core import Step
from ..models import Entity, Triplet, GraphBuilderResult
from rapidfuzz import process,fuzz

class TripletEntityMerger(Step):
    def __init__(
        self,
        name: str = "TripletEntityMerger",
        similarity_threshold: float = 0.9
    ):
        
        self.name = name
        self.similarity_threshold = similarity_threshold

    def _find_matching_entity(self, entity: Entity, existing_entities: List[Entity]) -> Entity:
 
        if entity.special_type in ['DATE', 'PRICE']:
            return entity
 
        match = process.extractOne(
            entity.name, 
            [e.name for e in existing_entities], 
            scorer=fuzz.ratio,
        )
        if match and (match[1]/100) >= self.similarity_threshold:
            matching_entity = next(e for e in existing_entities if e.name == match[0])
            self.log.debug(f"Entity match found: {entity.name} -> {matching_entity.name} (similarity: {match[1]/100:.2f})")
            return matching_entity
        
        return entity

    def _merge_triplets_with_entities(self, triplets: List[Triplet], entities: List[Entity]) -> List[Triplet]:
        if not triplets:
            return []
            
        merged_triplets = []
        
        for triplet in triplets:
            matching_head = self._find_matching_entity(triplet.head, entities)
            matching_tail = self._find_matching_entity(triplet.tail, entities)
            
            triplet.head = matching_head
            triplet.tail = matching_tail
            
            merged_triplets.append(triplet)
            
                        
        return merged_triplets

    def execute(self, result: GraphBuilderResult) -> GraphBuilderResult:
        
        if not result.relation_extraction:
            return result

        if not result.entity_extraction:
            return result

        initial_count = len(result.relation_extraction)
        self.log.info(f"Merging {initial_count} triplets")

        merged_triplets = self._merge_triplets_with_entities(
            result.relation_extraction, 
            result.entity_extraction
        )
        
        result.relation_extraction = merged_triplets
        self.log.info(f"Triplet-entity merging completed: {len(merged_triplets)} triplets")
        
        return result
        
    def save_result(self, step_result: GraphBuilderResult, result: GraphBuilderResult):
        result.relation_extraction = step_result.relation_extraction
        return result
