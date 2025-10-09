import asyncio
from hyperpipe_concrete.hyperengine import Llm, Embedder, neo4jGraph, qTracker, qChunk, Origin
from hyperpipe_concrete.graph_builder import build_graph
import litellm


#litellm._turn_on_debug()

async def main():
    llm = Llm(
        provider="openai",
        size="small",
        guardrails=True,
        input_max_tokens=8000,
        retries=3,
        cost_warning=0.5,
        debug=False
    )
    
    embedder = Embedder(
        provider="openai",
        size="small",
        guardrails=True,
        cost_warning=0.5,
        debug=False
    )
    
    neo4j = neo4jGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your_password",
        database="neo4j"
    )
    
    chunks = [
        qChunk(
            uid="chunk_1",
            text="Apple Inc. is a technology company founded by Steve Jobs.",
            headers="Company Information",
            pages=[1],
            metadata={"source": "tech_doc"}
        ),
        qChunk(
            uid="chunk_2", 
            text="Steve Jobs was the CEO of Apple and revolutionized personal computing.",
            headers="Leadership",
            pages=[1],
            metadata={"source": "tech_doc"}
        )
    ]
    
    tracker = qTracker(
        data="Technology Companies Document",
        chunks=chunks,
        name="tech_analysis",
        origin=Origin(
            mime_type="text/plain",
            file_type="document",
            source="local",
            reference="tech_companies.txt",
            reference_id="doc_001"
        ),
        metadata={"category": "technology"}
    )
    
    config = {
        'batch_size': 6,
        'pipeline': {
            'entity_cleaner': {
                'remove_punctuation': True,
                'normalize_case': True
            },
            'entity_extractor': {
                'temperature': 0.1,
            },
            'relation_extractor': {
                'temperature': 0.1,
            },
            'neo4j_matcher': {
                'similarity_threshold': 0.85,
                'vector_index_name': 'embedded_entities_index',
            }
        }
    }
    
    result = await build_graph(
        qtracker=tracker,
        neo4j_graph=neo4j,
        llm=llm,
        embedder=embedder,
        config=config
    )
    
    print(f"Graph building completed: {result}")

if __name__ == "__main__":
    asyncio.run(main())

