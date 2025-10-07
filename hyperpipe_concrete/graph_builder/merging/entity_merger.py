from typing import List
from hyperpipe_core import Step
from ..models import Entity, GraphBuilderResult
from rapidfuzz import process,fuzz


class EntityTextMerger(Step):
    def __init__(
        self,
        name: str = "EntityTextMerger",
        name_similarity_threshold: float = 0.7
    ):
        
        self.name = name
        self.name_similarity_threshold = name_similarity_threshold

    def _deduplicate_by_name(self, entities: List[Entity]) -> List[Entity]:
        
        unique_entities = [entities[0]]
        
        for entity in entities[1:]:
            
            match = process.extractOne(
                entity.name, 
                [n.name for n in unique_entities], 
                scorer=fuzz.ratio,
            )

            if (match[1]/100) < self.name_similarity_threshold:
                unique_entities.append(entity)
            else:
                existing_entity = next(e for e in unique_entities if e.name == match[0])
                existing_entity.alternatives.append(entity)
                self.log.debug(f"Entity merged: {entity.name} -> {match[0]} (similarity: {match[1]/100:.2f})")
                
                
                
        return unique_entities

    def _normalize_labels(self, entities: List[Entity], label_similarity_threshold: float = 0.8) -> List[Entity]:
        if not entities:
            return entities
            
        unique_labels = list(set(entity.label for entity in entities))
        
        
        label_mapping = {}
        normalized_labels = []
        
        for label in unique_labels:
            if normalized_labels:
                match = process.extractOne(
                    label,
                    normalized_labels,
                    scorer=fuzz.ratio,
                )
                
                if (match[1]/100) >= label_similarity_threshold:
                    label_mapping[label] = match[0]
                    
                else:
                    normalized_labels.append(label)
                    label_mapping[label] = label
            else:
                normalized_labels.append(label)
                label_mapping[label] = label
        
        updated_count = 0
        for entity in entities:
            if entity.label in label_mapping and entity.label != label_mapping[entity.label]:
                old_label = entity.label
                entity.label = label_mapping[entity.label]
                updated_count += 1
                self.log.debug(f"Label normalized: {old_label} -> {entity.label}")
        
        if updated_count > 0:
            self.log.debug(f"Label normalization completed: {updated_count} labels updated")
        
        
        return entities



       

    def execute(self, result: GraphBuilderResult) -> GraphBuilderResult:
        
        if not result.entity_extraction:
            return result

        initial_count = len(result.entity_extraction)
        self.log.info(f"Merging {initial_count} entities")

        unique_by_name = self._deduplicate_by_name(result.entity_extraction)
        self.log.debug(f"Name deduplication: {initial_count} -> {len(unique_by_name)} entities")
        
        normalized_entities = self._normalize_labels(unique_by_name)
        result.entity_extraction = normalized_entities
        
        self.log.info(f"Entity merging completed: {len(normalized_entities)} final entities")
        return result
        
        
    def save_result(self, step_result: GraphBuilderResult, result: GraphBuilderResult):
        result.entity_extraction = step_result.entity_extraction
        return result