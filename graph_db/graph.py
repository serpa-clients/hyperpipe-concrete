from typing import Any
import neo4j

class SchemaSummary: ...
class ConfirmationMessage: ...

async def transaction(tx: neo4j.AsyncTransaction, query: str, params: dict = {}) -> list[dict]:
    result = await tx.run(query, **params)
    records = await result.data()
    return records

class neo4jGraph:
    driver: neo4j.AsyncDriver

    def __init__(
        self, 
        uri: str = None, 
        user: str = None, 
        password: str = None, 
        database: str = None
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        self.driver = await self._initialize_driver(
            uri=self.uri, 
            user=self.user, 
            password=self.password
        )
        self._initialized = True
    
    async def _initialize_driver(
        self, 
        uri: str, 
        user: str, 
        password: str
    ):
        driver = neo4j.AsyncGraphDatabase.driver(uri, auth=(user, password))
        try:
            await driver.verify_connectivity()
        except neo4j.exceptions.ServiceUnavailable:
            raise ValueError("Could not connect to Neo4j database. Please ensure that the url is correct")
        except neo4j.exceptions.AuthError:
            raise ValueError("Could not connect to Neo4j database. Please ensure that the username and password are correct")
        return driver

    async def read_query(
        self, 
        query: str, 
        params: dict = {}
    ) -> list[dict]:
        if not self._initialized:
            await self.initialize()
        async with self.driver.session(database=self.database) as session:
            try:
                data = await session.execute_read(transaction, query, params)
                return data
            except neo4j.exceptions.CypherSyntaxError as e:
                raise ValueError(f"Generated Cypher Statement is not valid\n{e}")

    async def write_query(
        self, 
        query: str, 
        params: dict = {}
    ) -> list[dict]:
        if not self._initialized:
            await self.initialize()
        async with self.driver.session(database=self.database) as session:
            try:
                data = await session.execute_write(transaction, query, params)
                return data
            except neo4j.exceptions.CypherSyntaxError as e:
                raise ValueError(f"Generated Cypher Statement is not valid\n{e}")

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def schema(self) -> SchemaSummary:
        pass

    async def refresh_schema(self) -> SchemaSummary:
        pass
    
    async def drop_index(
        self,
        label: str,
        kind: str = 'vector',
    ) -> ConfirmationMessage:
        pass
    
    async def create_index(
        self,
        label: str,
        kind: str = 'vector',
        full_refresh: None | bool = None,
    ) -> ConfirmationMessage:
        pass