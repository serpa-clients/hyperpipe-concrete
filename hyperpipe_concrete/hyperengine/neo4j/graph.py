from ..utils import TODO

type SchemaSummary = None
type ConfirmationMessage = str

class neo4jGraph:
    async def read_query(
        self,
        query: str,
        params: None | dict
    ) -> list[dict]:
        TODO()

    async def write_query(
        self,
        query: str,
        params: None | dict
    ) -> list[dict]:
        TODO()

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