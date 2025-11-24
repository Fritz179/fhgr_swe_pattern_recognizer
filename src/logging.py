from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from process import DetectionResult


class CSVLogger:
    def __init__(self, log_dir: Path | None, file_name: str | None = None) -> None:
        """
        Initialize the CSV logger by opening a CSV file and writing a header if needed.
        """
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        name = file_name or f"detections_{datetime.now():%Y%m%d_%H%M%S}.csv"
        self.path = self.log_dir / name

        self.file = self.path.open("a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)

        if self.path.stat().st_size == 0:
            self.writer.writerow(["timestamp", "pattern", "color", "x", "y", "w", "h"])
            self.file.flush()

    def write(self, detections: DetectionResult | Iterable[DetectionResult]) -> None:
        """
        Append one or many DetectionResult objects to the CSV.
        """
        if detections is None:
            return

        if isinstance(detections, Iterable) and not isinstance(detections, (str, bytes)):
            iterable = detections
        else:
            iterable = [detections]

        for detection in iterable:
            x, y, w, h = detection.bbox
            self.writer.writerow(
                [
                    detection.timestamp.isoformat(),
                    detection.pattern.upper(),
                    detection.color.upper(),
                    x,
                    y,
                    w,
                    h,
                ]
            )

        self.file.flush()

    def close(self) -> None:
        """Close the CSV file."""
        if hasattr(self, "file") and self.file and not self.file.closed:
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        """Ensure the file is closed even if user forgets."""
        self.close()
