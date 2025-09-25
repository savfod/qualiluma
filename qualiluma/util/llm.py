"""Module for LLMs usage"""

import os
import warnings
from pathlib import Path
from typing import Any

import dotenv
from langchain_openai import ChatOpenAI

from ..util.config import CONFIG_PATH, _yaml_read
from .logs import get_logger

CONFIG = _yaml_read(CONFIG_PATH)
_LLM_CLIENTS: dict[str, "LLMClient"] = {}

logger = get_logger(__name__)


class LLMClient:
    """Simple wrapper to use only our simple for now logic"""

    def __init__(self, name: str = "default"):
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
