"""Module for LLMs usage"""

import os
import warnings
from pathlib import Path
import typing as tp

import dotenv
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_openai import ChatOpenAI

from ..util.config import CONFIG_PATH, _yaml_read
from .logs import get_logger

CONFIG = _yaml_read(CONFIG_PATH)
_LLM_CLIENTS: dict[str, "LLMClient"] = {}
USAGE_HANDLER = UsageMetadataCallbackHandler()

logger = get_logger(__name__)


T = tp.TypeVar("T")
class LLMClient(tp.Generic[T]):
    """Simple wrapper to use only our simple for now logic"""

    def __init__(self, name: str = "fast"):
        """Init LLM client

        Args:
            name: The name of the LLM client to use (e.g. default if we have more)
        """

        self.llm_config: tp.Any = CONFIG["llms"].get(name, {})
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

    def structured_output(self, query: str, answer_schema: type[T]) -> T:
        """Get structured output from the LLM client using pydantic

        Args:
            answer_schema: The pydantic model to use for structured output
        Returns:
            The structured output from the LLM client
        """ 
        assert self.client, "LLM client is not initialized"

        client_structured = self.client.with_structured_output(answer_schema)
        res = client_structured.invoke(
            [("user", query)],
            config={"callbacks": [USAGE_HANDLER]},
        )
        assert isinstance(
            res, answer_schema
        ), f"LLM structured response is not of type {answer_schema}: {res}"
        return res

def get_llm_client(name: str = "fast") -> LLMClient | None:
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


def log_llm_pricing(config: dict | None = None) -> float:
    """Log the LLM usage and pricing information.

    Args:
        config: The pricing configuration for LLM usage.

    Returns:
        The total cost of LLM usage.
    """
    if config is None:
        config = CONFIG.get("llm_pricing", {})
 
    incomplete_info = False
    cost_by_model = {}
    for model, usage in USAGE_HANDLER.usage_metadata.items():
        input_cached = usage.get("input_cached_details", {}).get("cache_read", 0)
        input_non_cached = usage.get("input_tokens", 0) - input_cached
        output_tokens = usage.get("output_tokens", 0)  # includes reasoning

        if model not in config:
            logger.warning(f"No pricing configuration found for model '{model}'")
            incomplete_info = True
            continue

        model_config = config.get(model, {})
        required_keys = {"input_noncached_per_1m", "output_per_1m", "input_cached_per_1m"}
        missing_keys = required_keys - set(model_config.keys())
        if missing_keys:
            logger.warning(f"Incomplete pricing configuration for model '{model}', missing keys: {missing_keys}")
            incomplete_info = True
            continue

        cost_by_model[model] = (
            input_non_cached * model_config["input_noncached_per_1m"] / 1_000_000
            + output_tokens * model_config["output_per_1m"] / 1_000_000
            + input_cached * model_config["input_cached_per_1m"] / 1_000_000
        )

    incomplete_str = " (INCOMPLETE info)" if incomplete_info else ""
    for model, cost in cost_by_model.items():
        logger.debug(f"LLM Cost for {model}{incomplete_str}: ${cost:.4f}")
    total_cost = sum(cost_by_model.values())
    logger.info(f"Total LLM Cost{incomplete_str}: ${total_cost:.4f}")
    return total_cost
