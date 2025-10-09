import asyncio
from typing import List
import litellm
import numpy as np
import tiktoken
from .router import get_model, get_tokenizer, get_max_tokens

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
        self.model = get_model(self.provider, self.size)
        self.tokenizer = tiktoken.get_encoding(get_tokenizer(self.provider, self.size))
        self.max_tokens = get_max_tokens(self.provider, self.size)
    
    async def embed(self, query: str|list[str]) -> list[list[float]]:
       
        batches = self.split_into_batches(query)
        
        batch_tasks = [self.calculate_batch_embeddings(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)

         
        all_embeddings = []
        for batch_embeddings in batch_results:
            all_embeddings.extend(batch_embeddings)
            
        return all_embeddings
    
    async def calculate_batch_embeddings(self, texts: List[str]) -> List[np.array]:
        try:
            embeddings = await litellm.aembedding(model=self.model, input=texts)
            result = [np.array(embedding['embedding']) for embedding in embeddings.data]
            return result
        except Exception as e:
            raise e

    def estimate_tokens(self, texts: List[str]) -> int:
        if self.tokenizer is None:
            total_chars = sum(len(text) for text in texts)
            return max(1, total_chars // 4)
        
        total_tokens = 0
        for text in texts:
            try:
                tokens = len(self.tokenizer.encode(text))
                total_tokens += tokens
            except Exception:
                total_tokens += max(1, len(text) // 4)
        
        return total_tokens 
    
    
    def split_into_batches(self, texts: List[str]) -> List[List[str]]:
        batches = []
        current_batch = []
        current_tokens = 0
        
        for text in texts:
            text_tokens = self.estimate_tokens([text])
            
            if current_tokens + text_tokens > self.max_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = text_tokens
            else:
                current_batch.append(text)
                current_tokens += text_tokens
        
        if current_batch:
            batches.append(current_batch)
            
        return batches