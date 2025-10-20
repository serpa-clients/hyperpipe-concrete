models = {
        "openai": {
            "reasoning": "o3",
            "medium": "gpt-4.1",
            "small": "gpt-4.1-mini"
        },
        "anthropic": {
            "reasoning": "claude-opus-4-1-20250805",
            "medium": "claude-sonnet-4-20250514",
            "small": "claude-3-5-haiku-20241022"
        },
        "ollama": {
            "reasoning": "qwq",
            "medium": "qwen2.5:32b",
            "small": "qwen2.5:32b"
        },
       "gemini": {
            "reasoning": "gemini-2.5-pro",
            "medium": "gemini-2.5-flash",
            "small": "gemini-2.5-flash-lite"
        },
        "nvidia_nim": {
            "reasoning": "qwen/qwq-32b",
            "medium": "meta/llama-3.3-70b-instruct",
            "small": "meta/llama-3.3-70b-instruct"
        },
        "azure": {
            "reasoning": "o4-mini",
            "medium": "gpt-4.1",
            "small": "gpt-4.1-mini"
        }
    }

def get_model(
    provider: str,
    size: str,
) -> str:
    model_name = models[provider][size]
    return f'{provider}/{model_name}'