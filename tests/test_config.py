from qualiluma.util import Config


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

    def test_get_ignored_directories(self):
        config = Config()
        ignored_dirs = config.get_ignored_directories()
        assert "venv" in ignored_dirs
        assert "node_modules" in ignored_dirs
        assert "dist" in ignored_dirs
        assert "build" in ignored_dirs
        assert "tmp" in ignored_dirs
        assert "base.py" not in ignored_dirs
