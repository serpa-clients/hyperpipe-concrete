from typing import List

from .base_extractor import BaseExtractor
from hyperpipe_core import Result
from hyperpipe_core.kg import Entity
from ..utils.extraction_models import EntitiesListResponse
from ..utils.prompts import EntityExtractionPrompts
  

class AsyncEntityExtractor(BaseExtractor):
    
    def __init__(self, 
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.1,
                 name: str = "AsyncEntityExtractor",
                 **kwargs):
        
        super().__init__(
            model=model,
            temperature=temperature,
            name=name,
            **kwargs
        )
        self.name = name
        self.iteration = 0
        self.system_prompt = EntityExtractionPrompts.SYSTEM
        self.user_prompt_template = EntityExtractionPrompts.USER_TEMPLATE    

    
    async def execute(self, data: Result) -> List[Entity]:
        
        chunks = data.initial_input.chunks
        if self.iteration >= len(chunks):
            return []
        
        chunk = chunks[self.iteration]
        text = chunk.text
        
        
        current_entities = await self.async_extract_from_llm(
            template=self.user_prompt_template,
            response_model=EntitiesListResponse,
            converter=lambda model: self.convert_to_domain(model, chunk),
            text=text,
        )
        
        self.log.info(f"Extracted {len(current_entities)}")
        

        
        
        return current_entities
    
    
    
    def convert_to_domain(self, parsed_model: EntitiesListResponse, chunk) -> List[Entity]:
        
        entities = []
        for entity_data in parsed_model.entities:
            try:
                if not self.is_valid_entity_name(entity_data.name):
                    continue
                    
                if not self.is_valid_entity_label(entity_data.label):
                    continue
                
                entity = self.create_entity_with_metadata(
                    entity_data.name,
                    entity_data.label,
                    chunk.text,
                    chunk_id=chunk.uid,
                    source="qTracker",
                    summary=entity_data.summary
                )
                entities.append(entity)
                
            except Exception as e:
                continue
        
        return entities
    
    def save_result(self, step_result: List[Entity], result: Result) -> None:
        if result.entity_extraction is None:
            result.entity_extraction = step_result
        else:
            result.entity_extraction.output.extend(step_result)
            
    
    
