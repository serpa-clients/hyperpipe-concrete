from typing import List, Dict, Any
from ..models import Triplet, GraphBuilderResult
from .base_exporter import Exporter
import json
import re

class Neo4jExporter(Exporter):
    MAX_IDENTIFIER_LENGTH = 16383
    TRUNCATE_SUFFIX = '_trunc'
    DEFAULT_NAMES = {"node": "Entity", "rel": "RELATES", "prop": "property"}
    PROGRESS_LOG_INTERVAL = 100
    
    def __init__(self, neo4j_graph, name: str = None, batch_size: int = 100, embedded_label: str = "Embedded"):
        super().__init__(name)
        self.neo4j_graph = neo4j_graph
        self.batch_size = batch_size
        self.embedded_label = embedded_label
    
    def _normalize_identifier(self, text: str, id_type: str) -> str:

        if not text:
            default_name = self.DEFAULT_NAMES.get(id_type, "default")
            return default_name
        
        normalizers = {
            "node": self._to_pascal_case,
            "rel": self._to_upper_case,
            "prop": self._to_snake_case
        }
        
        clean = normalizers[id_type](text)
        final_result = self._ensure_valid_identifier(clean, id_type)
        return final_result
    
    def _to_pascal_case(self, text: str) -> str:
        if text and text[0].isupper() and not any(c in text for c in [' ', '-', '_', '.', ',', '!', '?', ';', ':', '"', "'"]):
            return text
        
        words = [word.capitalize() for word in re.split(r'[-_\s]+', text.strip()) if word]
        return ''.join(c for c in ''.join(words) if c.isalnum())
    
    def _to_upper_case(self, text: str) -> str:
        text_spaced = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        words = [word.upper() for word in re.split(r'[-_\s]+', text_spaced.strip()) if word]
        clean = '_'.join(words) if words else "RELATES"
        return ''.join(c for c in clean if c.isalnum() or c == '_')
    
    def _to_snake_case(self, text: str) -> str:
        text_spaced = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        words = [word for word in re.split(r'[-\s]+', text_spaced.strip().lower()) if word]
        clean = '_'.join(words) if words else "property"
        return ''.join(c for c in clean if c.isalnum() or c == '_')
    
    def _ensure_valid_identifier(self, clean: str, id_type: str) -> str:
        if not clean or not clean[0].isalpha():
            clean = self.DEFAULT_NAMES[id_type] + clean
        
        if len(clean) > self.MAX_IDENTIFIER_LENGTH:
            truncate_pos = self.MAX_IDENTIFIER_LENGTH - len(self.TRUNCATE_SUFFIX)
            clean = clean[:truncate_pos] + self.TRUNCATE_SUFFIX
        
        return clean
    
    def _serialize_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, list):
            return value if value and isinstance(value[0], (int, float)) else json.dumps(value)
        if isinstance(value, dict):
            return json.dumps(value)
        if hasattr(value, 'dict'):
            return json.dumps(value.dict())
        return value
    
    def _flatten_object_properties(self, obj: Any, prefix: str = "") -> Dict[str, Any]:
        if obj is None:
            return {}
        
        properties = {}
        
        if hasattr(obj, 'dict'):
            obj_dict = obj.dict()
        elif isinstance(obj, dict):
            obj_dict = obj
        else:
            return {}
        
        for field_name, field_value in obj_dict.items():
            if field_value is None:
                continue
                
            clean_name = self._normalize_identifier(field_name, "prop")
            prop_name = f"{prefix}{clean_name}" if prefix else clean_name
            
            if hasattr(field_value, 'dict'):
                nested_props = self._flatten_object_properties(field_value, "")
                properties.update(nested_props)
            elif isinstance(field_value, dict):
                nested_props = self._flatten_object_properties(field_value, "")
                properties.update(nested_props)
            elif isinstance(field_value, list):
                if field_value and hasattr(field_value[0], 'dict'):
                    alternatives_tuples = []
                    for item in field_value:
                        if hasattr(item, 'dict'):
                            item_dict = item.dict()
                            name = item_dict.get('name', 'unknown')
                            source = item_dict.get('source', 'unknown')
                            chunk_id = item_dict.get('chunk_id', 'unknown')
                            alternatives_tuples.append((name, source, chunk_id))
                    properties[prop_name] = json.dumps(alternatives_tuples)
                else:
                    properties[prop_name] = self._serialize_value(field_value)
            else:
                properties[prop_name] = field_value
        
        return properties
    
    def _build_entity_query(self, entity: Any, var_name: str) -> tuple[str, Dict[str, Any]]:
        properties = self._flatten_object_properties(entity)
        parameters = {}
        prop_strings = []
        
        for prop_name, prop_value in properties.items():
            param_name = f"{var_name}_{prop_name}"
            prop_strings.append(f"{prop_name}: ${param_name}")
            parameters[param_name] = prop_value
        
        props_str = ", ".join(prop_strings) if prop_strings else ""
        
        label = properties.get('label', 'Entity')
        if not label:
            label = "Entity"
        
        label = self._normalize_identifier(label, "node")
        query_part = f"({var_name}:{label} {{{props_str}}})"
        
        return query_part, parameters
    
    def _build_relationship_query(self, relation: Any, var_name: str) -> tuple[str, Dict[str, Any]]:
        properties = self._flatten_object_properties(relation)
        parameters = {}
        prop_strings = []
        
        for prop_name, prop_value in properties.items():
            param_name = f"{var_name}_{prop_name}"
            prop_strings.append(f"{prop_name}: ${param_name}")
            parameters[param_name] = prop_value
        
        props_str = ", ".join(prop_strings) if prop_strings else ""
        
        rel_name = properties.get('name', 'RELATES')
        if not rel_name:
            rel_name = "RELATES"
        
        rel_type = self._normalize_identifier(rel_name, "rel")
        query_part = f"[{var_name}:{rel_type} {{{props_str}}}]"
        
        return query_part, parameters
    
    def _normalize_name(self, name: str) -> str:
        if not name:
            return name
        return name.strip().title()
    
    def _extract_data(self, result: GraphBuilderResult) -> List[Triplet]:
        if not result.relation_extraction:
            return []
        
        triplets = result.relation_extraction
        
        return triplets
    
    def _export_batch(self, triplets_batch: List[Triplet]) -> int:
        if not triplets_batch:
            return 0
        
        try:
            batch_data = []
            
            for triplet in triplets_batch:
                head_props = self._flatten_object_properties(triplet.head)
                tail_props = self._flatten_object_properties(triplet.tail)
                rel_props = self._flatten_object_properties(triplet.relation)
                
                if triplet.metadata:
                    triplet_props = self._flatten_object_properties(triplet.metadata, "")
                    rel_props.update(triplet_props)
                
                if 'name' in head_props:
                    head_props['name'] = self._normalize_name(head_props['name'])
                if 'name' in tail_props:
                    tail_props['name'] = self._normalize_name(tail_props['name'])
                
                head_labels = [self._normalize_identifier(head_props.get('label', 'Entity'), "node")]
                tail_labels = [self._normalize_identifier(tail_props.get('label', 'Entity'), "node")]
                
                if triplet.head.embedding:
                    head_labels.append(self.embedded_label)
                else:
                    continue
                if triplet.tail.embedding:
                    tail_labels.append(self.embedded_label)
                else:
                    continue
                
                batch_item = {
                    "head_props": head_props,
                    "tail_props": tail_props,
                    "rel_props": rel_props,
                    "head_labels": head_labels,
                    "tail_labels": tail_labels,
                    "rel_type": self._normalize_identifier(rel_props.get('name', 'RELATES'), "rel")
                }
                
                batch_data.append(batch_item)
            
            query = """
            UNWIND $batch AS item
            
            CALL apoc.merge.node(item.head_labels, {name: item.head_props.name}, item.head_props, item.head_props) YIELD node as h
            
            WITH item, h
            
            CALL apoc.merge.node(item.tail_labels, {name: item.tail_props.name}, item.tail_props, item.tail_props) YIELD node as t
            
            WITH item, h, t
            
            CALL apoc.merge.relationship(h, item.rel_type, {}, item.rel_props, t) YIELD rel as r
            RETURN count(r) as created
            """
            
            result = self.neo4j_graph.write_query(query, params={"batch": batch_data})
            exported_count = len(triplets_batch)
            self.log.debug(f"Batch export successful: {exported_count} triplets")
            return exported_count
            
        except Exception as e:
            error_msg = str(e)
            self.log.error(f"Neo4j batch export failed: {error_msg}")
            
            # Log specific Neo4j error details
            if hasattr(e, 'code'):
                self.log.error(f"Neo4j error code: {e.code}")
            if hasattr(e, 'message'):
                self.log.error(f"Neo4j error message: {e.message}")
                
            self.log.error(f"Failed batch context - size: {len(triplets_batch)}, embedded_label: '{self.embedded_label}'")
            return 0
    
    def _export_data(self, triplets: List[Triplet]) -> int:
        if not triplets:
            return 0
        
        total_exported = 0
        total_batches = (len(triplets) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(triplets), self.batch_size):
            batch = triplets[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            self.log.debug(f"Processing export batch {batch_num}/{total_batches}: {len(batch)} triplets")
            
            batch_exported = self._export_batch(batch)
            total_exported += batch_exported
        
        return total_exported
    
    def execute(self, result: GraphBuilderResult) -> None:
        triplets = self._extract_data(result)
        if not triplets:
            self.log.info("No triplets to export")
            return None
        
        self.log.info(f"Exporting {len(triplets)} triplets to Neo4j")
        self._export_data(triplets)
        self.log.info(f"Export completed")
        
        return None
