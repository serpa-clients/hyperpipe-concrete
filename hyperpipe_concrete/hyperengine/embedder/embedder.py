import litellm
from .router import get_model

class Embedder:
    provider: str # 'auto' | 'openai' | ...
    size: str # 'small' | 'medium' | 'large'
    guardrails: bool
    cost_warning: float
    debug: bool

    def __init__(
        self,
        provider: str,
        size: str,
        guardrails: bool,
        cost_warning: float,
        debug: bool,
    ) -> None:
        self.provider = provider
        self.size = size
        self.guardrails = guardrails
        self.cost_warning = cost_warning
        self.debug = debug
    
    async def embed(self, query: str|list[str]) -> list[list[float]]:
        model = get_model(self.provider, self.size)
        embeddings = await litellm.embeddings(
            model=model,
            input=query,
        )

        return embeddings.data