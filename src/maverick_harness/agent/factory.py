import os
from dotenv import load_dotenv

from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider

# Default model to be used
DEFAULT_MODEL = "openai:gpt-5-mini"

def create_model(model_spec: str = DEFAULT_MODEL) -> Model:
    """
    Creating the Pydantic AI Model from the Provider

    Supported Providers:
    - openRouter: <model>
    - openai: <model>
    """

    load_dotenv()

    if ":" not in model_spec:
        raise ValueError(
            f"Invalid model '{model_spec}'. Expected format 'provider:model_name', "
            "e.g. 'openrouter:anthropic/claude-sonnet-4' or 'openai:gpt-4.1-mini'."
        )

    provider_name, model_name = model_spec.split(":", 1)

    if provider_name == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENROUTER_API_KEY in .env or environment.")
        return OpenRouterModel(
            model_name, provider = OpenRouterProvider(api_key=api_key, app_title="maverick-agent")
        )

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY in .env or environment.")
        return OpenAIChatModel(
            model_name, provider = OpenAIProvider(api_key=api_key)
        )

    raise ValueError(
        f"Unsupported provider '{provider_name}'. Supported: 'openrouter', 'openai'."
    )