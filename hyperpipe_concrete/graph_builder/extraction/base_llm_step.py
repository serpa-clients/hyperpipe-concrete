from abc import abstractmethod
from typing import TypeVar, Generic, Type, Callable, List, Dict, Any
import json
import asyncio
import time

from hyperpipe_core import AsyncStep, Result
from hyperengine import Llm

T = TypeVar('T')
U = TypeVar('U')
R = TypeVar('R')


class BaseLLMStep(AsyncStep, Generic[T, U, R]):
    def __init__(self,
                 llm: Llm,
                 temperature: float = 0.1,
                 name: str = None,
                 examples: List[Dict[str, str]] = None,
                 **kwargs):
        self.llm = llm
        self.temperature = temperature
        self.name = name or self.__class__.__name__
        self.examples = examples

    def build_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]
        if self.examples:
            for example in self.examples:
                if 'user_prompt' in example and 'response' in example:
                    messages.append({"role": "user", "content": example['user_prompt']})
                    messages.append({"role": "assistant", "content": example['response']})
                else:
                    messages.append(example)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def format_prompt_template(self, template: str, **kwargs) -> str:
        return template.format(**kwargs)

    def build_hallucination_params(self, messages: List[Dict[str, str]], **extra_params) -> Dict[str, Any]:
        return {
            "messages": messages,
            "temperature": extra_params.get("temperature", self.temperature),
            "tools": extra_params.get("tools", []),
            "parallel_tool_calls": extra_params.get("parallel_tool_calls", False),
            "user": extra_params.get("user", self.name or ""),
            "is_vision": extra_params.get("is_vision", False),
        }

    async def async_extract_structured_data(
        self,
        hallucination_params: Dict[str, Any],
        response_model: Type[T],
        converter: Callable[[T], List[U]],
        max_retries: int = 2,
        retry_delay: float = 3.0,
        total_timeout: float = 30.0,
    ) -> List[U]:
        start_time = time.time()
        json_parsing_errors = 0
        attempt = 0
        while attempt < max_retries:
            try:
                elapsed_time = time.time() - start_time
                if elapsed_time > total_timeout:
                    return []

                content = await self.llm.hallucinate(
                    messages=hallucination_params["messages"],
                    temperature=hallucination_params.get("temperature", self.temperature),
                    tools=hallucination_params.get("tools", []),
                    parallel_tool_calls=hallucination_params.get("parallel_tool_calls", False),
                    response_format=response_model,
                    user=hallucination_params.get("user", self.name or ""),
                    is_vision=hallucination_params.get("is_vision", False),
                )

                if '```json' in content:
                    content = content.split('```json', 1)[1].split('```', 1)[0].strip()

                parsed_data: Dict = json.loads(content)
                parsed_model: T = response_model.model_validate(parsed_data)
                return converter(parsed_model)

            except json.JSONDecodeError:
                attempt += 1
                json_parsing_errors += 1
                if json_parsing_errors >= 2:
                    return []
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                else:
                    return []

            except Exception:
                attempt += 1
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                else:
                    return []

        return []

    async def async_extract_from_llm(
        self,
        template: str,
        response_model: Type[T],
        converter: Callable[[T], List[U]],
        **template_kwargs
    ) -> List[U]:
        user_prompt = self.format_prompt_template(template, **template_kwargs)
        messages = self.build_messages(self.system_prompt, user_prompt)
        hallucination_params = self.build_hallucination_params(messages)
        return await self.async_extract_structured_data(
            hallucination_params=hallucination_params,
            response_model=response_model,
            converter=converter,
        )

    @abstractmethod
    def convert_to_domain(self, parsed_model: T, data: Result) -> List[U]:
        pass
