from typing import List, Tuple

from ...hyperengine import qChunk
from ..models import Triplet, TripletMetadata, Relationship, Entity, GraphBuilderResult

from .base_extractor import BaseExtractor
from ..utils.prompts import RelationExtractionPrompts
from ..utils.extraction_models import RelationsListResponse




class AsyncRelationExtractor(BaseExtractor):
    
    def __init__(self, 
                 model: str = "gpt-4o-mini",
                 embeddings_model=None,
                 rel_threshold: float = 0.7,
                 name: str = "AsyncRelationExtractor",
                 system_prompt: str = None,
                 user_prompt_template: str = None,
                 iteration: int = 0,
                 **kwargs):
        super().__init__(
            model=model, 
            name=name, 
            embeddings_model=embeddings_model,
            iteration=iteration,
            **kwargs
        )
        
        self.rel_threshold = rel_threshold
        
        self.system_prompt = system_prompt or RelationExtractionPrompts.SYSTEM
        self.user_prompt_template = user_prompt_template or RelationExtractionPrompts.USER_TEMPLATE

    def calculate_triplet_positions(self, content: str, head_entity_name: str, tail_entity_name: str, relation_name: str) -> Tuple[int, int]:
   
        positions = self.find_text_positions(content, [head_entity_name, tail_entity_name, relation_name])
        if not positions:
            return 0, len(content)
        start = min(pos[0] for pos in positions)
        end = max(pos[1] for pos in positions)
        return start, end

    def convert_to_domain(self, parsed_model: RelationsListResponse, chunk: qChunk, entities: List[Entity]) -> List[Triplet]:

        triplets = []
        
        for i, llm_relation in enumerate(parsed_model.relations):
            try:
                if not self.is_valid_entity_name(llm_relation.head.name):
                    continue
                    
                if not self.is_valid_entity_label(llm_relation.head.label):
                    continue
                
                if not self.is_valid_entity_name(llm_relation.tail.name):
                    continue
                    
                if not self.is_valid_entity_label(llm_relation.tail.label):
                    continue
                
                if not self.is_valid_relation_name(llm_relation.relation.name):
                    continue
                
                
                head_label = llm_relation.head.label
                tail_label = llm_relation.tail.label
                
                generic_labels = {"entity", "entity type", "entitytype", "generic", "unknown", ""}
                
                if (head_label.lower().strip() in generic_labels or 
                    tail_label.lower().strip() in generic_labels):
                    continue
                
                head_entity = self.create_entity_with_metadata(
                    llm_relation.head.name,
                    head_label,
                    chunk.text,
                    chunk_id=chunk.uid,
                    source="qTracker",
                    summary=llm_relation.head.summary
                )
                
                tail_entity = self.create_entity_with_metadata(
                    llm_relation.tail.name,
                    tail_label,
                    chunk.text,
                    chunk_id=chunk.uid,
                    source="qTracker",
                    summary=llm_relation.tail.summary
                )
                
                relationship = Relationship(
                    name=llm_relation.relation.name,
                    label=llm_relation.relation.label
                )
                
                start_pos, end_pos = self.calculate_triplet_positions(
                    chunk.text, llm_relation.head.name, llm_relation.tail.name, llm_relation.relation.name
                )
                
                metadata = TripletMetadata(
                    context=chunk.text,
                    start_position=start_pos,
                    end_position=end_pos
                )
                
                triplet = Triplet(
                    head=head_entity,
                    relation=relationship,
                    tail=tail_entity,
                    metadata=metadata
                )
                triplets.append(triplet)
                self.log.debug(f"Triplet validated: {llm_relation.head.name} -[{llm_relation.relation.name}]-> {llm_relation.tail.name}")
                
            except Exception as e:
                self.log.debug(f"Error processing relation: {str(e)[:50]}")
                continue
        
        return triplets
    
    async def extract_relations_from_chunk(self, chunk: qChunk, entities: List[Entity]) -> List[Triplet]:
        
        entity_info = []
        for e in entities:
            if e.label and e.label.strip():
                entity_info.append(f"{e.name} ({e.label})")
            else:
                entity_info.append(e.name)
        
        entity_list = ", ".join(entity_info) if entity_info else "No entities provided"
        
        text = self.prepare_text_with_alternatives(chunk.text, entities)

        triplets = await self.async_extract_from_llm(
            template=self.user_prompt_template,
            response_model=RelationsListResponse,
            converter=lambda model: self.convert_to_domain(model, chunk, entities),
            text=text,
            entity_list=entity_list,
        )
        
        return triplets
    
    async def execute(self, data: GraphBuilderResult) -> List[Triplet]:
        
        
        entities = data.entity_extraction or []
        current_chunk = data.initial_input.chunks[self.iteration]

        final_triplets = await self.extract_relations_from_chunk(current_chunk, entities)
        
        self.log.info(f"Extracted {len(final_triplets)}")
            
        return final_triplets


    def save_result(self, step_result: List[Triplet], result: GraphBuilderResult) -> None:
        result.relation_extraction.extend(step_result)
                
        