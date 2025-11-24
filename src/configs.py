from dataclasses import dataclass
from src.logging import CSVLogger
from pathlib import Path

@dataclass
class AppConfig:
    logger: CSVLogger
    source_type: str  # "CAMERA" or "IMAGE"

    shape_thresholds: dict
    color_thresholds: dict


    def __init__(self, path: Path | None):
        """
        Load application configuration from the given file path.

        If path is None, load a default config (e.g. from 'config.yaml').
        """