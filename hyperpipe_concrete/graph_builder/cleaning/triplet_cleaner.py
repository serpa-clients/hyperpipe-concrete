from hyperpipe_core import Result
from .base_cleaner import Cleaner

class TripletCleaner(Cleaner):
    def __init__(
        self,
        name: str = "TripletCleaner",
        remove_punctuation: bool = True,
        normalize_case: bool = True
    ):
        super().__init__(name=name, remove_punctuation=remove_punctuation, normalize_case=normalize_case)

    async def execute(self, result: Result) -> Result:
        
        if not result.relationship_extraction:
            return result

        initial_count = len(result.relationship_extraction.output)
        self.log.info(f"Cleaning {initial_count} triplets")

        for triplet in result.relationship_extraction.output:
            self._clean_entity(triplet.head)
            
            original_relation_name = triplet.relation.name
            triplet.relation.name = self._clean_text(triplet.relation.name)
            if triplet.relation.name == "":
                triplet.relation.name = original_relation_name
            
            self._clean_entity(triplet.tail)

        self.log.info(f"Triplet cleaning completed")
        return result

    def save_result(self, step_result: Result, result: Result):
        result.relationship_extraction = step_result.relationship_extraction
        return result
