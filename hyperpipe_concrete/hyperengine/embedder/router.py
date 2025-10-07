models = {
        "openai": {
            "small": {"model": "text-embedding-3-small", "dimension": 1536},
            "large": {"model": "text-embedding-3-large", "dimension": 3072}
        },
        "nvidia_nim": {
            "small": {"model": "baai/bge-m3", "dimension": 1024},
            "large": {"model": "baai/bge-m3", "dimension": 1024}
        },
         "azure": {
            "small": {"model": "text-embedding-3-small", "dimension": 1536},
            "large": {"model": "text-embedding-3-large", "dimension": 3072}
},
        "gemini": {
            "small": {"model": "text-embedding-004", "dimension": 768},
            "large": {"model": "gemini-embedding-exp-03-07", "dimension": 3072} # EXPERIMENTAL TODO
        }
}

def get_model(
    provider: str,
    size: str,
) -> str
    model_name = models[provider][size]['model']
    return f'{provider}/{model_name}'