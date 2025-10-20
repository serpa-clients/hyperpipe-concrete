import litellm
import pydantic
from .router import get_model

class Llm:
    provider: str # 'auto' | 'openai' | ...
    size: str # 'small' | 'medium' | 'large'
    guardrails: bool
    input_max_tokens: int
    retries: int
    cost_warning: float
    debug: bool

    def __init__(
        self,
        provider: str,
        size: str,
        guardrails: bool,
        input_max_tokens: int,
        retries: int,
        cost_warning: float,
        debug: bool,
    ) -> None:
        self.provider = provider
        self.size = size
        self.guardrails = guardrails
        self.input_max_tokens = input_max_tokens
        self.retries = retries
        self.cost_warning = cost_warning
        self.debug = debug
        self.model = get_model(self.provider, self.size)

    async def hallucinate(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        tools: list,
        parallel_tool_calls: bool,
        response_format: pydantic.BaseModel,
        user: str,
        is_vision: bool
    ) -> str:
        
        completions = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format=response_format,
        )
        result = completions.choices[0]
        return result