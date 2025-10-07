from typing import List, Dict, Tuple
import re

from .base_llm_step import BaseLLMStep
from ..models import Entity, EntityMetadata


class BaseExtractor(BaseLLMStep):
    
    def __init__(self, 
                 **kwargs):
        super().__init__(**kwargs)
        
    

    @staticmethod
    def find_text_positions(content: str, components: List[str]) -> List[Tuple[int, int]]:
        content_lower = content.lower()
        positions = []
        
        for component in components:
            component_lower = component.lower()
            pos = content_lower.find(component_lower)
            if pos != -1:
                positions.append((pos, pos + len(component)))
        
        return positions

    def calculate_entity_position(self, content: str, entity_name: str) -> int:
        positions = self.find_text_positions(content, [entity_name])
        return positions[0][0] if positions else 0

    def create_entity_with_metadata(self, name: str, label: str, content: str, chunk_id: str = None, source: str = None, summary: str = None) -> Entity:
        start_index = self.calculate_entity_position(content, name)
        
        entity = Entity(
            name=name,
            label=label,
            summary=summary,
            metadata=EntityMetadata(
                context=content,
                start_index=start_index,
                sentence_id=None,
                chunk_id=chunk_id,
                source=source
            ),
            alternatives=[]
        )
        
        return entity
    
    
    @staticmethod
    def is_valid_entity_name(name: str) -> bool:
        if not name or not isinstance(name, str):
            return False
        
        cleaned_name = name.strip()
        if not cleaned_name or len(cleaned_name) == 0:
            return False
        
        problematic = {"none", "null", "undefined", "", " ", "  "}
        if cleaned_name.lower() in problematic:
            return False
        
        if not any(c.isalnum() for c in cleaned_name):
            return False
            
        return True
    
    @staticmethod 
    def is_valid_entity_label(label: str) -> bool:
        if not label or not isinstance(label, str):
            return False
            
        cleaned_label = label.strip()
        if not cleaned_label or len(cleaned_label) == 0:
            return False
        
        problematic = {"none", "null", "undefined", "", " ", "  "}
        if cleaned_label.lower() in problematic:
            return False
            
        generic_labels = {
            "entity", "entity type", "entitytype", "generic", "unknown", 
            "type", "label", "name", "object", "thing", "item", "text"
        }
        if cleaned_label.lower() in generic_labels:
            return False
            
        return True
    
    @staticmethod
    def is_valid_relation_name(name: str) -> bool:
        if not name or not name.strip():
            return False
        
        cleaned_name = name.strip().lower()
        
        # Basic length check - relationships should be concise
        if len(cleaned_name) > 50:
            return False
        
        
        underscore_count = cleaned_name.count('_')
        if underscore_count > 3:  # Too many parts/sections
            return False
        
        # Check for numerical values in relationship names (should be avoided)
        import re
        if re.search(r'\d+\.?\d*%?', cleaned_name):  # Matches numbers, decimals, percentages
            return False
        
        
        return True
    
    @staticmethod
    def reduce_text_with_alternatives(text: str, alternatives_map: Dict[str, List[str]]) -> str:
        if not alternatives_map:
            return text
        
        alt_key_pairs = [
            (alt, key)
            for key, alts in alternatives_map.items()
            for alt in alts
        ]
        alt_key_pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
        
        for alt, key in alt_key_pairs:
            pattern = re.compile(r'(?<!\w){}(?!\w)'.format(re.escape(alt)))
            text = pattern.sub(key, text)
        
        return text
    
    def build_entity_alternatives_map(self, entities: List[Entity]) -> Dict[str, List[str]]:
        alternatives_map = {}
        
        for entity in entities:
            alternatives = entity.alternatives
            if not alternatives:
                continue
                
            representative_name = next(iter(sorted([a.name for a in alternatives], key=len)), None)
            
            if representative_name is None:
                continue
            
            alternatives_list = [entity.name] + [a.name for a in alternatives]
            alternatives_map.setdefault(representative_name, list(set(alternatives_list)))
        
        return alternatives_map
    
    def prepare_text_with_alternatives(self, text: str, entities: List[Entity]) -> str:
        
        alternatives_map = self.build_entity_alternatives_map(entities)
        
        if not alternatives_map:
            entity_names = [e.name for e in entities]
        else:
            pass
        
        return self.reduce_text_with_alternatives(text, alternatives_map)
    
 