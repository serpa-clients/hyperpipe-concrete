from .base_cleaner import Cleaner
from ..models import GraphBuilderResult

class TripletCleaner(Cleaner):
    def __init__(
        self,
        name: str = "TripletCleaner",
        remove_punctuation: bool = True,
        normalize_case: bool = True
    ):
        super().__init__(name=name, remove_punctuation=remove_punctuation, normalize_case=normalize_case)

    async def execute(self, result: GraphBuilderResult) -> GraphBuilderResult:
        
        if not result.relation_extraction:
            return result

        initial_count = len(result.relation_extraction)
        self.log.info(f"Cleaning {initial_count} triplets")

        for triplet in result.relation_extraction:
            self._clean_entity(triplet.head)
            
            original_relation_name = triplet.relation.name
            triplet.relation.name = self._clean_text(triplet.relation.name)
            if triplet.relation.name == "":
                triplet.relation.name = original_relation_name
            
            self._clean_entity(triplet.tail)

        self.log.info(f"Triplet cleaning completed")
        return result

    def save_result(self, step_result: GraphBuilderResult, result: GraphBuilderResult):
        result.relation_extraction = step_result.relation_extraction
        return result
