from hyperpipe_core import Result
from .base_cleaner import Cleaner

class EntityCleaner(Cleaner):
    def __init__(
        self,
        name: str = "EntityCleaner",
        remove_punctuation: bool = True,
        normalize_case: bool = True
    ):
        super().__init__(name=name, remove_punctuation=remove_punctuation, normalize_case=normalize_case)

    async def execute(self, result: Result) -> Result:
        
        if not result.entity_extraction:
            return result

        initial_count = len(result.entity_extraction.output)
        self.log.info(f"Cleaning {initial_count} entities")

        for entity in result.entity_extraction.output:
            self._clean_entity(entity)

        self.log.info(f"Entity cleaning completed")
        return result

    def save_result(self, step_result: Result, result: Result):
        result.entity_extraction = step_result.entity_extraction
        return result