from .base_cleaner import Cleaner
from ..models import GraphBuilderResult

class EntityCleaner(Cleaner):
    def __init__(
        self,
        name: str = "EntityCleaner",
        remove_punctuation: bool = True,
        normalize_case: bool = True
    ):
        super().__init__(name=name, remove_punctuation=remove_punctuation, normalize_case=normalize_case)

    async def execute(self, result: GraphBuilderResult) -> GraphBuilderResult:
        
        if not result.entity_extraction:
            return result

        initial_count = len(result.entity_extraction)
        self.log.info(f"Cleaning {initial_count} entities")

        for entity in result.entity_extraction:
            self._clean_entity(entity)

        self.log.info(f"Entity cleaning completed")
        return result

    def save_result(self, step_result: GraphBuilderResult, result: GraphBuilderResult):
        result.entity_extraction = step_result.entity_extraction
        return result