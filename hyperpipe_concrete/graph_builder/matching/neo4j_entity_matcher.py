from typing import List, Dict, Optional, Tuple
from hyperpipe_core import Step, Result
from hyperpipe_core.kg import Triplet, Entity


class Neo4jEntityMatcher(Step[Result, None]):
    
    def __init__(
        self,
        neo4j_graph,
        name: str = "Neo4jEntityMatcher",
        similarity_threshold: float = 0.85,
        top_k: int = 1,
        vector_index_name: str = "embedded_entities_index"
    ):
        self.name = name
        self.neo4j_graph = neo4j_graph
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.vector_index_name = vector_index_name
        
    def _extract_unique_entities(self, triplets: List[Triplet]) -> Dict[str, Entity]:
        unique_entities = {}
        
        for triplet in triplets:
            head_key = triplet.head.name.lower()
            tail_key = triplet.tail.name.lower()
            
            if head_key not in unique_entities:
                unique_entities[head_key] = triplet.head
                
            if tail_key not in unique_entities:
                unique_entities[tail_key] = triplet.tail
                
        return unique_entities
    

    
    def _find_similar_entity_in_neo4j(self, entity: Entity) -> Optional[Tuple[str, str, float]]:
        
        if not entity.embedding:
            return None
        
        try:
            query = """
            CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
            YIELD node, score
            WHERE score >= $threshold
            RETURN node.name as name, node.label as label, score
            ORDER BY score DESC
            LIMIT 1
            """
            
            params = {
                "index_name": self.vector_index_name,
                "top_k": self.top_k,
                "embedding": entity.embedding,
                "threshold": self.similarity_threshold
            }
            
            results = self.neo4j_graph.read_query(query, params)
            
            if results:
                result = results[0]
                name = result['name']
                label = result['label']
                score = result['score']
                
                return (name, label, score)
            else:
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.log.error(f"Neo4j vector query failed for entity '{entity.name}': {error_msg}")
            
            # Log specific Neo4j error details
            if hasattr(e, 'code'):
                self.log.error(f"Neo4j error code: {e.code}")
            if hasattr(e, 'message'):
                self.log.error(f"Neo4j error message: {e.message}")
                
            # Log embedding context for debugging
            embedding_info = f"type: {type(entity.embedding)}, length: {len(entity.embedding) if entity.embedding else 0}"
            self.log.error(f"Query failed - index: '{self.vector_index_name}', embedding {embedding_info}")
            
            return None
    
    def _create_replacement_entity(self, original_entity: Entity, neo4j_name: str, neo4j_label: str) -> Entity:
        
        replacement_entity = Entity(
            name=neo4j_name,
            label=neo4j_label,
            embedding=original_entity.embedding,
            metadata=original_entity.metadata
        )
        
        replacement_entity.alternatives.append(original_entity)
        
        return replacement_entity

    
    def _replace_entities_in_triplets(self, triplets: List[Triplet], entity_mapping: Dict[str, Entity]) -> List[Triplet]:
        replaced_count = 0
        
        for triplet in triplets:
            original_head_key = triplet.head.name.lower()
            original_tail_key = triplet.tail.name.lower()
            
            if original_head_key in entity_mapping:
                old_head = triplet.head
                triplet.head = entity_mapping[original_head_key]
                replaced_count += 1
            
            if original_tail_key in entity_mapping:
                old_tail = triplet.tail
                triplet.tail = entity_mapping[original_tail_key]
                replaced_count += 1
        
        return triplets
    
    def execute(self, result: Result) -> None:
        
        if not result.relationship_extraction or not result.relationship_extraction.output:
            return None
        
        triplets = result.relationship_extraction.output
        unique_entities = self._extract_unique_entities(triplets)
        self.log.info(f"Matching {len(unique_entities)} entities against Neo4j")
        
        entity_mapping = {}
        matches_found = 0
        
        for entity_key, entity in unique_entities.items():
            if entity.special_type == 'DATE':
                continue
            
            elif entity.special_type == 'PRICE':
                continue
            
            similar_result = self._find_similar_entity_in_neo4j(entity)
            if similar_result:
                neo4j_name, neo4j_label, score = similar_result
                self.log.debug(f"Neo4j match found: {entity.name} -> {neo4j_name} (score: {score:.3f})")
                
                if entity.name.lower() != neo4j_name.lower():
                    replacement_entity = self._create_replacement_entity(
                        entity, neo4j_name, neo4j_label
                    )
                    entity_mapping[entity_key] = replacement_entity
                    matches_found += 1
        
        if entity_mapping:

            self._replace_entities_in_triplets(triplets, entity_mapping)
        
        self.log.info(f"Neo4j matching completed: {matches_found} entities replaced")
        return None
    
    def save_result(self, step_result: Result, result: Result) -> None:
        pass

