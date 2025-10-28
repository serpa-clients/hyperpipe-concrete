from typing import List

from hyperpipe_core import AsyncBatchPipeline, Pipeline,PipelineRunner

from .extraction import AsyncEntityExtractor, AsyncRelationExtractor 
from .merging import EntityTextMerger, RelationTextMerger, TripletEntityMerger
from .exporting import Neo4jExporter
from .cleaning import EntityCleaner, TripletCleaner
from .embedding import TripletEmbedder
from .matching import Neo4jEntityMatcher
from .models import GraphBuilderResult
from hyperpipe_core.logger import set_logger

def get_default_config():
    return {
        'batch_size': 6,
        'pipeline': {
            'entity_cleaner': {
                'remove_punctuation': True,
                'normalize_case': True
            },
            'triplet_cleaner': {
                'remove_punctuation': True,
                'normalize_case': True
            },
            'entity_text_merger': {
                'name_similarity_threshold': 0.9,
            },
            'relation_text_merger': {
                'name_similarity_threshold': 0.9,
            },
            'triplet_entity_merger': {
                'similarity_threshold': 0.9
            },
            'neo4j_matcher': {
                'similarity_threshold': 0.85,
                'vector_index_name': 'embedded_entities_index',
                'embedding_dimension': 1536,
            },
            'neo4j_exporter': {
                'batch_size': 100,
                'embedded_label': 'Embedded',
            },
            'entity_extractor': {
                'temperature': 0.1,
            },
            'relation_extractor': {
                'temperature': 0.1,
            }
        }
    }

def merge_config(user_config: dict = None) -> dict:
    default_config = get_default_config()
    if not user_config:
        return default_config
    
    merged = default_config.copy()
    for key, value in user_config.items():
        if key == 'pipeline' and isinstance(value, dict):
            merged['pipeline'] = {**default_config['pipeline'], **value}
            for component_key, component_config in value.items():
                if component_key in merged['pipeline'] and isinstance(component_config, dict):
                    merged['pipeline'][component_key] = {**merged['pipeline'][component_key], **component_config}
        else:
            merged[key] = value
    return merged

async def build_graph(qtracker,
                neo4j_graph,
                llm,
                embedder,
                config: dict = None,
                logger = None):
    
    config = merge_config(config)

    num_chunks = len(qtracker.chunks)
    pipeline_config = config['pipeline']
    
    entity_cleaner = EntityCleaner(**pipeline_config['entity_cleaner'])
    triplet_cleaner = TripletCleaner(**pipeline_config['triplet_cleaner'])
    
    entity_text_merger = EntityTextMerger(**pipeline_config['entity_text_merger'])
    relation_text_merger = RelationTextMerger(**pipeline_config['relation_text_merger'])
    triplet_embedder = TripletEmbedder(embedder=embedder)
    triplet_entity_merger = TripletEntityMerger(**pipeline_config['triplet_entity_merger'])
    
    neo4j_matcher = Neo4jEntityMatcher(
        neo4j_graph=neo4j_graph,
        **pipeline_config['neo4j_matcher']
    )
    neo4j_exporter = Neo4jExporter(
        neo4j_graph=neo4j_graph, 
        **pipeline_config['neo4j_exporter']
    )

    def create_entity_pipeline(chunk_idx: int) -> AsyncBatchPipeline:
        extractor = AsyncEntityExtractor(
            llm=llm,
            **pipeline_config['entity_extractor'],
        )
        extractor.iteration = chunk_idx
        return AsyncBatchPipeline([extractor, entity_cleaner],name=f"Entity {chunk_idx}")
    
    def create_relation_pipeline(chunk_idx: int) -> AsyncBatchPipeline:
        extractor = AsyncRelationExtractor(
            llm=llm,
            **pipeline_config['relation_extractor'],
        )
        extractor.iteration = chunk_idx
        return AsyncBatchPipeline([extractor, triplet_cleaner],name=f"Relation{chunk_idx}")
    
    steps_entity_extractor = [create_entity_pipeline(i) for i in range(num_chunks)]
    steps_relation_extractor = [create_relation_pipeline(i) for i in range(num_chunks)]

    def create_batch_pipeline(entity_pipes: List, relation_pipes: List) -> Pipeline:
        
        components = [
            AsyncBatchPipeline(
                entity_pipes, name="Entity"
            ),
            entity_text_merger,
            AsyncBatchPipeline(
                relation_pipes, name="Relation"
            ),
            triplet_entity_merger,
            triplet_embedder,
            relation_text_merger,
            neo4j_matcher,
            neo4j_exporter,
        ]
        
        return Pipeline(components)
    
    pipelines = []
    for batch_start in range(0, num_chunks, config['batch_size']):
        batch_end = min(batch_start + config['batch_size'], num_chunks)
        
        entity_batch = steps_entity_extractor[batch_start:batch_end]
        relation_batch = steps_relation_extractor[batch_start:batch_end]
        
        batch_pipeline = create_batch_pipeline(entity_batch, relation_batch)
        pipelines.append(batch_pipeline)
    
    final_pipeline = Pipeline([Pipeline(pipelines, name="GraphBuilder")])
    
    
    runner = PipelineRunner(final_pipeline, result_class=GraphBuilderResult) 
    
    runner.map_transform([set_logger(logger)])
    return await runner.arun(qtracker)


