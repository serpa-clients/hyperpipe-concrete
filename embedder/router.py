models = {
        "openai": {
            "small": {"model": "text-embedding-3-small", "dimension": 1536, "tokenizer": "cl100k_base", "max_tokens": 8000},
            "large": {"model": "text-embedding-3-large", "dimension": 3072, "tokenizer": "cl100k_base", "max_tokens": 8000}
        },
        "nvidia_nim": {
            "small": {"model": "baai/bge-m3", "dimension": 1024, "tokenizer": "cl100k_base", "max_tokens": 8000},
            "large": {"model": "baai/bge-m3", "dimension": 1024, "tokenizer": "cl100k_base", "max_tokens": 8000}
        },
         "azure": {
            "small": {"model": "text-embedding-3-small", "dimension": 1536, "tokenizer": "cl100k_base", "max_tokens": 8000},
            "large": {"model": "text-embedding-3-large", "dimension": 3072, "tokenizer": "cl100k_base", "max_tokens": 8000  }
},
        "gemini": {
            "small": {"model": "text-embedding-004", "dimension": 768, "tokenizer": "cl100k_base", "max_tokens": 8000},
            "large": {"model": "gemini-embedding-exp-03-07", "dimension": 3072, "tokenizer": "cl100k_base", "max_tokens": 8000} # EXPERIMENTAL TODO
        }
}

def get_model(
    provider: str,
    size: str,
) -> str:
    model_name = models[provider][size]['model']
    return f'{provider}/{model_name}'

def get_tokenizer(
    provider: str,
    size: str,
) -> str:
    return models[provider][size]['tokenizer']

def get_max_tokens(
    provider: str,
    size: str,
) -> int:
    return models[provider][size]['max_tokens']