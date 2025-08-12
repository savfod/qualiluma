from llmcqr.config import Config


class TestConfig:
    def test_get_labels(self):
        config = Config()
        labels = config.get_labels(".py")
        assert "code" in labels

        labels = config.get_labels(".txt")
        assert "docs" in labels

        labels = config.get_labels(".md")
        assert "docs" in labels

        labels = config.get_labels(".unknown")
        assert labels == []
