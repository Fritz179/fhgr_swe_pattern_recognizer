from pathlib import Path
from src.process import DetectionResult

class CSVLogger:
    def __init__(self, log_dir: Path | None) -> None:
        """
        Initialize the CSV logger.

        Creates the log directory if it does not exist.
        Prepares the CSV file for logging detection results.
        """

    def write(self, detections: list[DetectionResult]) -> None:
        """
        Append multiple DetectionResult objects to the CSV.
        """


    def close(self) -> None:
        """Close the CSV file."""

    def __del__(self):
        """Ensure the file is closed even if user forgets."""
