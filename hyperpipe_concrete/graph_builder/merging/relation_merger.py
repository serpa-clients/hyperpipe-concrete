from typing import List
from hyperpipe_core import Step
from ..models import Relationship, GraphBuilderResult
from rapidfuzz import process, fuzz


class RelationTextMerger(Step):
    def __init__(
        self,
        name: str = "RelationTextMerger",
        name_similarity_threshold: float = 0.9
    ):
        super().__init__()
        self.name = name
        self.name_similarity_threshold = name_similarity_threshold



    def _deduplicate_by_name(self, relationships: List[Relationship]) -> List[Relationship]:
        if not relationships:
            return relationships
            
        unique_relationships = [relationships[0]]
        
        for relationship in relationships[1:]:
            match = process.extractOne(
                relationship.name, 
                [r.name for r in unique_relationships], 
                scorer=fuzz.ratio,
            )

            if (match[1]/100) < self.name_similarity_threshold:
                unique_relationships.append(relationship)
            else:
                existing_relationship = next(r for r in unique_relationships if r.name == match[0])
                original_name = relationship.name
                relationship.name = existing_relationship.name
                self.log.debug(f"Relation merged: {original_name} -> {existing_relationship.name} (similarity: {match[1]/100:.2f})")
                
        return unique_relationships

    def execute(self, result: GraphBuilderResult) -> GraphBuilderResult:
        if not result.relation_extraction:
            self.log.info("No relationships to process for merging")
            return result
        
        relationships = [triplet.relation for triplet in result.relation_extraction]
        self.log.info(f"Merging {len(relationships)} relations")
        
        # Perform name-based deduplication
        relationships = self._deduplicate_by_name(relationships)
        self.log.info(f"Name-based deduplication completed: {len(relationships)} relationships remaining")
        
        # Update the triplets with the merged relationships
        for i, triplet in enumerate(result.relation_extraction):
            if i < len(relationships):
                triplet.relation = relationships[i]
        
        self.log.info(f"Relation merging completed: {len(relationships)} final relationships")
        return result

    def save_result(self, step_result: GraphBuilderResult, result: GraphBuilderResult):
        result = step_result
        return result
