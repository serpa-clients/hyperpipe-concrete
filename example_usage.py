import asyncio
from hyperpipe_concrete.hyperengine import Llm, Embedder, neo4jGraph, qTracker, qChunk, Origin, Logger
from hyperpipe_concrete.graph_builder import build_graph
import litellm


#litellm._turn_on_debug()

async def main():
    import logging
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('\033[30m[%(asctime)s]\033[0m \033[36m[%(name)s]\033[0m \033[33m[%(levelname)s]\033[0m %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
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
            text="Apple Inc. is a multinational technology company headquartered in Cupertino, California. Founded by Steve Jobs, Steve Wozniak, and Ronald Wayne on April 1, 1976, the company initially focused on personal computers. Apple's first product, the Apple I, was hand-built by Wozniak and sold for $666.66. The company went public on December 12, 1980, with an initial public offering that generated more capital than any IPO since Ford Motor Company in 1956.",
            headers="Company History and Founding",
            pages=[1],
            metadata={"source": "tech_doc", "year": 1976, "category": "corporate_history"}
        ),
        qChunk(
            uid="chunk_2", 
            text="Steve Jobs served as CEO of Apple Inc. from 1997 until his resignation in August 2011, just months before his death in October 2011. Under his leadership, Apple revolutionized multiple industries including personal computing with the Macintosh, music with the iPod and iTunes, mobile phones with the iPhone, and tablets with the iPad. Jobs was known for his demanding perfectionism, attention to design details, and reality distortion field that pushed teams to achieve seemingly impossible goals. He reported directly to the Board of Directors and worked closely with design chief Jony Ive.",
            headers="Leadership and Management",
            pages=[1,2],
            metadata={"source": "tech_doc", "period": "1997-2011", "category": "leadership"}
        ),
        qChunk(
            uid="chunk_3",
            text="The iPhone was first released on June 29, 2007, revolutionizing the smartphone industry. Priced at $499 for the 4GB model and $599 for the 8GB model, it combined a phone, iPod, and internet communication device. The device was manufactured by Foxconn in China and designed by Apple's industrial design team led by Jonathan Ive. The iPhone used a multi-touch interface that eliminated the need for a physical keyboard, running on iOS (initially called iPhone OS). By 2023, over 2.3 billion iPhones have been sold worldwide, generating over $200 billion in annual revenue.",
            headers="Product Innovation - iPhone",
            pages=[3,4],
            metadata={"source": "tech_doc", "product": "iPhone", "launch_date": "2007-06-29", "category": "product"}
        ),
        qChunk(
            uid="chunk_4",
            text="Tim Cook became CEO of Apple on August 24, 2011, succeeding Steve Jobs. Before becoming CEO, Cook served as Chief Operating Officer and was responsible for Apple's worldwide sales and operations. Under Cook's leadership, Apple became the first publicly traded U.S. company to reach a $1 trillion market valuation in August 2018, and later $2 trillion in August 2020. Cook emphasizes environmental sustainability, privacy protection, and inclusive hiring practices. He reports to the Board of Directors and oversees executive team members including Craig Federighi (Software Engineering), John Ternus (Hardware Engineering), and Luca Maestri (CFO).",
            headers="Modern Leadership",
            pages=[5],
            metadata={"source": "tech_doc", "period": "2011-present", "category": "leadership"}
        ),
        qChunk(
            uid="chunk_5",
            text="Apple's research and development facility in Cupertino, known as Apple Park, opened in April 2017. The $5 billion campus, designed by Foster + Partners in collaboration with Apple, spans 175 acres and features a circular main building with a diameter of 1,512 feet. The facility houses over 12,000 employees and includes research labs, product testing facilities, and a 1,000-seat Steve Jobs Theater. Apple Park is powered by 100% renewable energy, with 17 megawatts of rooftop solar panels making it one of the largest on-site solar installations in the world. The campus includes partnerships with Stanford University for research collaborations.",
            headers="Infrastructure and Facilities",
            pages=[6,7],
            metadata={"source": "tech_doc", "location": "Cupertino", "category": "infrastructure"}
        ),
        qChunk(
            uid="chunk_6",
            text="Apple's App Store launched on July 10, 2008, with 500 applications available at launch. Developed and maintained by Apple's Services division, the platform has grown to host over 1.8 million apps as of 2023. The App Store uses a revenue sharing model where Apple takes a 30% commission on paid apps and in-app purchases (reduced to 15% for small businesses earning less than $1 million annually). The platform generated approximately $85 billion in revenue in 2022. Notable app developers include Epic Games (Fortnite), Meta (Facebook, Instagram), and Spotify. The App Store competes directly with Google Play Store on Android devices.",
            headers="Platform and Ecosystem",
            pages=[8,9],
            metadata={"source": "tech_doc", "platform": "App Store", "category": "services"}
        ),
        qChunk(
            uid="chunk_7",
            text="Jony Ive served as Chief Design Officer at Apple from 2015 to 2019, and prior to that held the position of Senior Vice President of Industrial Design from 1997 to 2015. Ive was responsible for designing iconic products including the iMac, iPod, iPhone, and iPad. He worked closely with Steve Jobs on product development and reported to Tim Cook after becoming CDO. Ive's design philosophy emphasized simplicity, minimalism, and the integration of hardware and software. In 2019, Ive departed Apple to found his independent design company LoveFrom, though Apple remained a client. His successor, Evans Hankey, became VP of Industrial Design.",
            headers="Design Leadership",
            pages=[10,11],
            metadata={"source": "tech_doc", "department": "design", "category": "leadership"}
        ),
        qChunk(
            uid="chunk_8",
            text="Apple's supply chain is managed globally with primary manufacturing partners in China, Taiwan, and Vietnam. Foxconn (Hon Hai Precision Industry) serves as the primary contract manufacturer, employing over 200,000 workers at its Zhengzhou facility, known as 'iPhone City'. Other key suppliers include TSMC (Taiwan Semiconductor Manufacturing Company) for chip production, Samsung for OLED displays, and Qualcomm for modem chips. Apple spent $449 billion with suppliers in 2022, supporting 2.7 million jobs across nine countries. The company works with environmental organizations to reduce carbon emissions across the supply chain and has committed to being carbon neutral by 2030.",
            headers="Supply Chain and Manufacturing",
            pages=[12,13,14],
            metadata={"source": "tech_doc", "category": "operations", "partners": ["Foxconn", "TSMC", "Samsung"]}
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
        config=config,
        logger=logger
    )
    

if __name__ == "__main__":
    asyncio.run(main())

