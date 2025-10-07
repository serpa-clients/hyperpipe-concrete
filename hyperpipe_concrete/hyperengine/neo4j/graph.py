from ..utils import TODO
import neo4j

type SchemaSummary = None
type ConfirmationMessage = str    

def transaction(tx: neo4j.Transaction, query: str, params: dict = {}) -> list[dict]:
    data = tx.run(query, **params)
    return [r.data() for r in data]

class neo4jGraph:
    driver: neo4j.Driver

    def __init__(
        self, 
        uri: str = None, 
        user: str = None, 
        password: str = None, 
        database: str = None
    ):
        self.driver = self.initialize_driver(
            uri=uri, 
            user=user, 
            password=password
        )
        
        self.database = database
    
    def initialize_driver(
        self, 
        uri: str, 
        user: str, 
        password: str
    ):
        driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        try:
            driver.verify_connectivity()
        except neo4j.exceptions.ServiceUnavailable:
            raise ValueError("Could not connect to Neo4j database. Please ensure that the url is correct")
        except neo4j.exceptions.AuthError:
            raise ValueError("Could not connect to Neo4j database. Please ensure that the username and password are correct")
        return driver

    def read_query(
        self, 
        query: str, 
        params: dict = {}
    ) -> list[dict]:
        with self.driver.session(database=self.database) as session:
            try:
                data = session.execute_read(transaction, query, params)
                return data
            except neo4j.exceptions.CypherSyntaxError as e:
                raise ValueError(f"Generated Cypher Statement is not valid\n{e}")

    def write_query(
        self, 
        query: str, 
        params: dict = {}
    ) -> list[dict]:
        with self.driver.session(database=self.database) as session:
            try:
                data = session.execute_write(transaction, query, params)
                return data
            except neo4j.exceptions.CypherSyntaxError as e:
                raise ValueError(f"Generated Cypher Statement is not valid\n{e}")

    async def schema() -> SchemaSummary:
        TODO()

    async def refresh_schema() -> SchemaSummary:
        TODO()
    
    async def drop_index(
        self,
        label: str,
        kind: str = 'vector',
    ) -> ConfirmationMessage:
        TODO()
    
    async def create_index(
        self,
        label: str,
        kind: str = 'vector', # | 'full_text' | 'hybrid'
        full_refresh: None | bool = None,
    ) -> ConfirmationMessage:
        TODO()