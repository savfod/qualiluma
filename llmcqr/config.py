import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "configs" / "config.yaml"


def _yaml_read(file_path: Path) -> dict:
    """Reads a YAML file and returns the contents as a dictionary.

    Args:
        file_path (Path): The path to the YAML file to read.

    Returns:
        dict: The contents of the YAML file as a dictionary.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


class Config:
    def __init__(self):
        self._config = _yaml_read(CONFIG_PATH)

        self._ext_to_type: dict[str, str] = {}
        for type_, extensions in self._config["files"]["type"].items():
            for ext in extensions:
                assert ext not in self._ext_to_type, (
                    f"Extension {ext} is mapped to several"
                    f" types: {self._ext_to_type[ext]}, {type_}"
                )
                self._ext_to_type[ext] = type_

        self._type_to_labels: dict[str, list[str]] = {}
        for label, types in self._config["files"]["labels"].items():
            for type_ in types:
                if type_ not in self._type_to_labels:
                    self._type_to_labels[type_] = []
                self._type_to_labels[type_].append(label)

    def get_labels(self, file_extension: str) -> list[str]:
        """Returns a list of labels associated with a given file extension.

        Args:
            file_extension (str): The file extension to look up.

        Returns:
            list[str]: A list of labels associated with the file extension,
                e.g. ['code'] or ['docs'].
        """
        type_ = self._ext_to_type.get(file_extension, "")
        labels = self._type_to_labels.get(type_, [])
        return labels

    def get_ignored_directories(self) -> list[str]:
        """Returns a list of directories to ignore.

        Returns:
            list[str]: A list of directory names to ignore.
        """
        return self._config["directories"]["ignore"]

    def get_checker_extra(self, checker_name: str) -> dict:
        """Returns extra configuration for a given checker.

        Args:
            checker_name (str): The name of the checker to look up.

        Returns:
            dict: The extra configuration for the checker.
        """
        for checker in self._config.get("checkers_extra", []):
            if checker.get("name") == checker_name:
                return checker
        return {}
