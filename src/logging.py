from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from process import DetectionResult


class BaseLogger:
    """Simple base class to unify the interface."""

    def write(self, detection):  # pragma: no cover - interface only
        raise NotImplementedError

    def close(self):  # pragma: no cover - interface only
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


class CSVLogger(BaseLogger):
    """
    CSV logger: writes rows as Timestamp,Pattern,Color with microsecond precision.
    """

    def __init__(self, log_dir: Path | None, file_name: str | None = None) -> None:
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        name = file_name or f"detections_{datetime.now():%Y%m%d_%H%M%S}.csv"
        self.path = self.log_dir / name

        self.file = self.path.open("a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)

        if self.path.stat().st_size == 0:
            self.writer.writerow(["Timestamp", "Pattern", "Color"])
            self.file.flush()

    def write(self, detection: Iterable["DetectionResult"] | "DetectionResult" | None) -> None:
        if detection is None:
            return

        if isinstance(detection, Iterable) and not hasattr(detection, "timestamp"):
            detections = detection
        else:
            detections = [detection]

        for det in detections:
            if not hasattr(det, "timestamp"):
                continue
            ts = det.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            pattern = getattr(det, "pattern", "").capitalize()
            color = getattr(det, "color", "").upper()
            self.writer.writerow([ts, pattern, color])

        self.file.flush()

    def close(self) -> None:
        if hasattr(self, "file") and self.file and not self.file.closed:
            self.file.close()


class PrettyLogger(BaseLogger):
    """
    Text-table logger that formats detections like the provided sample.
    """

    TIMESTAMP_WIDTH = 28  # includes leading/trailing spaces
    PATTERN_WIDTH = 11
    COLOR_WIDTH = 8

    def __init__(self, log_dir: Path | None, file_name: str | None = None) -> None:
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        name = file_name or f"detections_{datetime.now():%Y%m%d_%H%M%S}.txt"
        self.path = self.log_dir / name

        self.file = self.path.open("a", encoding="utf-8")

        if self.path.stat().st_size == 0:
            self._write_header()

    # -- internal formatting helpers -------------------------------------------------
    @property
    def _border_line(self) -> str:
        return (
            f"|{'-' * self.TIMESTAMP_WIDTH}"
            f"|{'-' * self.PATTERN_WIDTH}"
            f"|{'-' * self.COLOR_WIDTH}|\n"
        )

    def _format_row(self, ts: str, pattern: str, color: str) -> str:
        ts_col = ts.ljust(self.TIMESTAMP_WIDTH - 2)
        pattern_col = pattern.ljust(self.PATTERN_WIDTH - 2)
        color_col = color.ljust(self.COLOR_WIDTH - 2)
        return f"| {ts_col} | {pattern_col} | {color_col} |\n"

    def _write_header(self) -> None:
        self.file.write(self._border_line)
        self.file.write(self._format_row("Timestamp", "Pattern", "Color"))
        self.file.write(self._border_line)
        self.file.flush()

    # -- public API -------------------------------------------------------------------
    def write(self, detection: Iterable["DetectionResult"] | "DetectionResult" | None) -> None:
        """
        Append one or many DetectionResult objects in the table format.
        """
        if detection is None:
            return

        if isinstance(detection, Iterable) and not hasattr(detection, "timestamp"):
            detections = detection
        else:
            detections = [detection]

        for det in detections:
            if not hasattr(det, "timestamp"):
                continue
            ts = det.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            pattern = getattr(det, "pattern", "").capitalize()
            color = getattr(det, "color", "").upper()
            self.file.write(self._format_row(ts, pattern, color))
            self.file.write(self._border_line)

        self.file.flush()

    def close(self) -> None:
        if hasattr(self, "file") and self.file and not self.file.closed:
            self.file.close()


def create_logger(log_dir: Path | None, log_format: str | None) -> BaseLogger:
    fmt = (log_format or "pretty").lower()
    if fmt == "csv":
        return CSVLogger(log_dir)
    # default to pretty table
    return PrettyLogger(log_dir)
