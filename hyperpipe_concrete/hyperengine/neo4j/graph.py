from ..utils import TODO
from typing import Any
import neo4j

class SchemaSummary: ...
class ConfirmationMessage: ...

async def async_transaction(tx: neo4j.AsyncTransaction, query: str, params: dict = {}) -> list[dict]:
    data = await tx.run(query, **params)
    return [r.data() async for r in data]

class neo4jGraph:
    driver: neo4j.AsyncDriver

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
        driver = neo4j.AsyncGraphDatabase.driver(uri, auth=(user, password))
        return driver

    async def read_query(
        self, 
        query: str, 
        params: dict = {}
    ) -> list[dict]:
        async with self.driver.session(database=self.database) as session:
            try:
                data = await session.execute_read(async_transaction, query, params)
                return data
            except neo4j.exceptions.CypherSyntaxError as e:
                raise ValueError(f"Generated Cypher Statement is not valid\n{e}")

    async def write_query(
        self, 
        query: str, 
        params: dict = {}
    ) -> list[dict]:
        async with self.driver.session(database=self.database) as session:
            try:
                data = await session.execute_write(async_transaction, query, params)
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