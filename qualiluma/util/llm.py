"""Module for LLMs usage"""

import os
import warnings
from pathlib import Path
from typing import Any

import dotenv
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_openai import ChatOpenAI

from ..util.config import CONFIG_PATH, _yaml_read
from .logs import get_logger

CONFIG = _yaml_read(CONFIG_PATH)
_LLM_CLIENTS: dict[str, "LLMClient"] = {}
USAGE_HANDLER = UsageMetadataCallbackHandler()

logger = get_logger(__name__)


class LLMClient:
    """Simple wrapper to use only our simple for now logic"""

    def __init__(self, name: str = "fast"):
        """Init LLM client

        Args:
            name: The name of the LLM client to use (e.g. default if we have more)
        """

        self.llm_config: Any = CONFIG["llms"].get(name, {})
        self.client: ChatOpenAI | None = None

        if not self.llm_config:
            warnings.warn(f"No configuration found for LLM client '{name}'")
            return

        dotenv.load_dotenv(Path(__file__).parents[2] / ".env")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

        if not OPENAI_API_KEY:
            warnings.warn(
                "OPENAI_API_KEY is not set. Please set it to use the LLM checker."
            )
            return

        self.client = ChatOpenAI(
            model=self.llm_config.get("model"),
            timeout=None,
            max_retries=2,
            max_tokens=self.llm_config["max_tokens"],
        )

    def is_initialized(self) -> bool:
        """Check if the LLM client is initialized"""
        return self.client is not None

    def __call__(self, query: str) -> str:
        assert self.client, "LLM client is not initialized"

        response = self.client.invoke(
            [("user", query)],  # or system?
            # max_tokens=self.llm_config["max_tokens"],
            config={"callbacks": [USAGE_HANDLER]},
        )
        res = response.content
        assert isinstance(res, str), f"LLM response is not a string: {type(res)}"
        logger.debug(f"Usage: {response.usage_metadata}")

        return res.strip()


def get_llm_client(name: str = "default") -> LLMClient | None:
    """
    Get the LLM client for code checking.

    Returns:
        The LLM client if the API key is set, None otherwise.

    """
    if name not in _LLM_CLIENTS:
        client = LLMClient(name)
        if client.is_initialized():
            _LLM_CLIENTS[name] = client

    return _LLM_CLIENTS.get(name, None)


def log_llm_pricing(config=CONFIG.get("llms_pricing", {})) -> float:
    """Log the LLM usage and pricing information.

    Args:
        config: The pricing configuration for LLM usage.

    Returns:
        The total cost of LLM usage.
    """

    total_cost = 0.0

    # 2025-09-17 15:45:50.599 | DEBUG    | qualiluma.util.llm:__call__:65 - Usage: {'input_tokens': 98, 'output_tokens': 1145, 'total_tokens': 1243, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 1088}}

    # using input_tokens, output_tokens, reasoning_tokens

    incomplete_info = False
    for model, usage in USAGE_HANDLER.usage_metadata.items():
        input_cached = usage.get("input_cached_details", {}).get("cache_read", 0)
        input_non_cached = usage.get("input_tokens", 0) - input_cached
        output_tokens = usage.get("output_tokens", 0)  # includes reasoning

        if model not in config:
            logger.warning(f"No pricing configuration found for model '{model}'")
            incomplete_info = True
            continue

        model_config = config.get(model, {})
        if {"input_noncached_per_1m", "output_per_1m", "input_cached_per_1m"} - set(
            model_config.keys()
        ):
            logger.warning(f"Incomplete pricing configuration for model '{model}'")
            incomplete_info = True
            continue

        total_cost += (
            input_non_cached * model_config["input_noncached_per_1m"] / 1_000_000
        )
        total_cost += output_tokens * model_config["output_per_1m"] / 1_000_000
        total_cost += input_cached * model_config["input_cached_per_1m"] / 1_000_000

    incomplete_str = " (INCOMPLETE info)" if incomplete_info else ""
    logger.info(f"Total LLM Cost{incomplete_str}: ${total_cost:.4f}")
    return total_cost
