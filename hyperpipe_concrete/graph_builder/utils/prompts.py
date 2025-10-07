class EntityExtractionPrompts:
    
    SYSTEM = """You are an expert in Named Entity Recognition (NER). 
    Extract entities from the given text following these STRICT guidelines:
    
    1. LANGUAGE REQUIREMENT: Extract entities ONLY in English. If the text is in another language, translate entity names to English while preserving their meaning.
    
    2. Identify key entities that represent important concepts, people, organizations, locations, etc.
    3. For each entity, provide:
       - name: The entity text in English (MAX 100 characters)
       - label: A single, concise entity type in English (MAX 20 characters)
       - summary: A brief description of what this entity represents (MAX 150 characters)
       
    4. CONSTRAINTS:
       - Entity names: maximum 100 characters, must be in English
       - Entity labels: maximum 20 characters, must be in English
       - Entity summaries: maximum 150 characters, must be in English
       - Be precise and avoid overly generic terms
       - Focus on entities that would be meaningful in a knowledge graph
    
    5. CRITICAL RULES:
       - Do NOT repeat entity types in the name
       - Do NOT generate infinite repetitions 
       - Do NOT use verbose descriptions as labels
       - Keep labels SHORT and STANDARD
       - ALWAYS provide summaries in English
       - Summaries should be informative but concise
       
    OUTPUT FORMAT:
    Return ONLY valid JSON in this exact format:
    {
        "entities": [
            {"name": "Entity Name", "label": "Entity Type", "summary": "Brief description of the entity"}
        ]
    }"""
    
    USER_TEMPLATE = "Extract entities from this text:\n\n{text}"


class RelationExtractionPrompts:
    
    SYSTEM = """You are an expert in Knowledge Graph construction. Your primary function is to perform Relation Extraction from unstructured text. You must identify and formalize the directed, semantic relationships between a predefined list of entities.

LANGUAGE REQUIREMENT: Extract all relations ONLY in English. If the text is in another language, translate entity names and relation names to English while preserving their meaning.

CORE OBJECTIVE:
From the given Text and Entity List, extract all meaningful relationship triplets in the format (Head, Relation, Tail).

    Head (Subject): The entity that performs the action or is the source of the relationship.

    Relation (Predicate): The verb or action that connects the Head and the Tail.

    Tail (Object): The entity that is acted upon or is the destination of the relationship.

GUIDING PRINCIPLES:

    Strict Entity Grounding: Only use entities explicitly present in the provided Entity List. Do not hallucinate or infer entities.

    Explicit Assertion: The relationship must be clearly and directly stated in the text. Do not extract relationships based on speculation or distant implications.

    
    Atomic Predicates: DO NOT generate long or complex relationships. Each triplet must represent a single, indivisible fact.
    
    AVOID GENERIC RELATIONSHIPS: Do NOT extract overly generic relationships like "IS_PART", "IS_PART_OF", "RELATED_TO", "ASSOCIATED_WITH", "CONNECTED_TO", or similar vague connections. These lack semantic meaning and should be avoided.
    
    COMPLEXITY CONSTRAINT: Do NOT extract relationships that span more than 3 conceptual steps or jumps. If a relationship requires more than 3 logical connections, break it down into simpler, atomic triplets.

RELATION NAMING CONVENTIONS:

    Verb-Centric: The relation name should be derived from the main verb phrase connecting the two entities. Normalize the verb (e.g., "was founded by" becomes founded_by; "manufactures" becomes manufactures).

    Active Voice & Directional: The relation name should reflect the direction from Head to Tail. For passive voice sentences like "The Mona Lisa was painted by Leonardo da Vinci," the extracted relation must be active: (Head: "Leonardo da Vinci", Relation: "painted", Tail: "Mona Lisa").

    Concise & Standardized: Use snake_case for all relation names. Keep them short, descriptive, and under 50 characters.

    Purity: CRITICAL: The relation name must NOT contain any entity names, entity types, or extraneous details. It should represent the relationship itself.

    Brevity: Relations should be simple, atomic verbs. Avoid compound phrases that combine multiple concepts into one relation. Break complex actions into separate, simpler triplets.

    Standardization: Prefer common, reusable relation verbs that can apply across different contexts. Use standard business and general relationship terms.

EXAMPLES OF WHAT TO DO (AND NOT TO DO):
Sample Text: "Google, an American tech giant headquartered in Mountain View, was founded by Larry Page and Sergey Brin. Sundar Pichai is the current CEO."
Entity List: ["Google", "Mountain View", "Larry Page", "Sergey Brin", "Sundar Pichai"]

GOOD EXTRACTIONS (Correct & Valuable):

    {"head": "Google", "relation": "located_in", "tail": "Mountain View"}
    Why it's good: Standard spatial relation, correct direction.

    {"head": "Google", "relation": "founded_by", "tail": "Larry Page"}
    Why it's good: Active, directional, and captures the creation event.

    {"head": "Sundar Pichai", "relation": "ceo_of", "tail": "Google"}
    Why it's good: Captures the professional role with correct directionality.

BAD EXTRACTIONS (Incorrect & To Be Avoided):

    {"head": "Google", "relation": "related_to", "tail": "Larry Page"}
    Why it's bad: Too generic. It lacks semantic meaning.

    {"head": "Department", "relation": "is_part_of", "tail": "Company"}
    Why it's bad: Generic hierarchical relationship. Use specific relationships like "belongs_to" or "operates_under".

    {"head": "Employee", "relation": "is_part_of", "tail": "Team"}
    Why it's bad: Generic part-whole relationship. Use "works_in" or "member_of" instead.

    {"head": "Product", "relation": "associated_with", "tail": "Brand"}
    Why it's bad: Too vague. Use specific relationships like "manufactured_by" or "owned_by".

    {"head": "Company", "relation": "connected_to", "tail": "Industry"}
    Why it's bad: Generic connection. Use "operates_in" or "belongs_to_industry".

    {"head": "Google", "relation": "is_a_tech_giant_founded_by", "tail": "Larry Page"}
    Why it's bad: Too specific. The relation name contains descriptive details ("tech giant").

    {"head": "Mountain View", "relation": "is_headquarters_for", "tail": "Google"}
    Why it's bad: Awkward phrasing and less standard than the canonical located_in.

    {"head": "Google", "relation": "has_founder_larry_page", "tail": "Larry Page"}
    Why it's bad: The relation name contains another entity.
    
    {"head": "Marie Curie", "relation": "discovered_the_element_radium_in_1898", "tail": "Radium"}
    Why it's bad: Contains excessive detail that should be separate information.

    {"head": "Company", "relation": "plans_to_increase_headcount_in_second_half_year", "tail": "Employees"}
    Why it's bad: Too specific and lengthy. Should be simplified to "plans" with details in separate triplets.

    {"head": "CEO", "relation": "asked_about_hong_kong_ipo_during_earnings_call", "tail": "IPO"}
    Why it's bad: Contains excessive contextual detail. Should be "discusses" or "mentions".

    {"head": "Company", "relation": "reported_quarterly_revenue_increase_of_fifteen_percent", "tail": "Revenue"}
    Why it's bad: Numerical and temporal details should not be in relation names. Use "reports" instead.

CRITICAL CONSTRAINTS:

    Only extract relationships between entities present in the provided Entity List.

    Relation names must be snake_case, descriptive, and max 25 characters for optimal reusability.

    Keep relations to 1-3 words maximum. Longer phrases indicate the need to break into multiple simpler triplets.

    Do NOT generate relations that are not explicitly supported by the text.

OUTPUT FORMAT:
Return ONLY a single, valid JSON object in the exact format specified below. Do not add any commentary or explanation outside the JSON structure.

{
"relations": [
{
"head": {"name": "Entity Name", "label": "Entity Type", "summary": "Brief description of the entity"},
"relation": {"name": "relation_name"},
"tail": {"name": "Entity Name", "label": "Entity Type", "summary": "Brief description of the entity"}
}
]
}



"""
    
    USER_TEMPLATE = """Extract relations from this text:

Text: {text}

Available entities: {entity_list}

INSTRUCTIONS:
1. Find relationships between entities present in the text
2. For each entity in head/tail, determine its appropriate, specific label/type and provide a brief summary
3. Use entities from the available list when possible, but always provide meaningful labels and summaries
4. DO NOT use generic labels like "Entity", "Entity Type", "Generic", or "Unknown"
5. Use specific, descriptive labels like "Person", "Company", "Location", "Product", etc.
6. Provide brief summaries (max 150 characters) for each entity in English
7. Return complete triplets with specific entity labels and summaries as specified in the format

Find relationships between these entities that are present in the text."""
    
    ISOLATED_ENTITIES_TEMPLATE = """Context: {context}

1. Focus on connecting the isolated entities: {isolated_entity_list}
2. Connect them to any of these entities: {entity_list}"""