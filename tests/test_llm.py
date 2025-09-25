"""Simple tests for the LLM module"""

from qualiluma.util.llm import get_llm_client


def test_get_llm_client_smoke():
    assert get_llm_client("abcd") is None
    assert get_llm_client("fast") is not None
    assert isinstance(get_llm_client("fast")("Hello"), str)


def MockClient(is_initialized):
    class _MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def is_initialized(self):
            return is_initialized

    return _MockClient


def test_get_llm_client(monkeypatch):
    some_true = MockClient(True)()
    monkeypatch.setattr("qualiluma.util.llm._LLM_CLIENTS", {"some_true": some_true})
    assert get_llm_client("some_true") is some_true

    monkeypatch.setattr("qualiluma.util.llm.LLMClient", MockClient(False))
    assert get_llm_client("default") is None

    monkeypatch.setattr("qualiluma.util.llm.LLMClient", MockClient(True))
    assert get_llm_client("default") is not None
