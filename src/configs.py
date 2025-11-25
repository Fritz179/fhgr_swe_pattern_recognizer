from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from logs import BaseLogger


DEFAULT_SHAPE_THRESHOLDS: dict[str, Any] = {
    "min_area": 300,                # minimum contour area to consider
    "square_aspect_tolerance": 0.15,  # how far from 1.0 the aspect ratio may deviate
    "circularity": 0.8,             # 1.0 is a perfect circle
    "approx_epsilon": 0.04,         # contour approximation factor
}

DEFAULT_COLOR_THRESHOLDS: dict[str, list[tuple[list[int], list[int]]]] = {
    # Each entry is a list of (lower, upper) HSV bounds. Red has two segments
    # to account for the hue wrap-around at 180.
    "RED": [([0, 70, 50], [10, 255, 255]), ([170, 70, 50], [180, 255, 255])],
    "GREEN": [([35, 40, 40], [85, 255, 255])],
    "BLUE": [([90, 50, 50], [130, 255, 255])],
    "YELLOW": [([20, 100, 100], [35, 255, 255])],
    "VIOLET": [([130, 50, 50], [160, 255, 255])],
}


@dataclass
class AppConfig:
    logger: BaseLogger
    shape_thresholds: dict
    color_thresholds: dict
    log_format: str


def _load_config_file(config_path: Path) -> dict:
    """
    Load a config dictionary from JSON or YAML file.
    """
    suffix = config_path.suffix.lower()
    if suffix == ".json":
        return json.loads(config_path.read_text(encoding="utf-8"))
    if suffix in {".yml", ".yaml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError("PyYAML is required to read YAML config files.") from exc
        return yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported config format: {config_path.suffix}")


def load_config(
    config_path: Path | None,
    log_dir: Path | None,
    log_format: str | None = None,
) -> AppConfig:
    """
    Build an AppConfig by merging defaults with an optional config file and CLI overrides.
    """
    cfg_data = (
        _load_config_file(config_path)
        if config_path is not None
        else {}
    )

    merged_shape = {
        **copy.deepcopy(DEFAULT_SHAPE_THRESHOLDS),
        **cfg_data.get("shape_thresholds", {}),
    }
    merged_color = copy.deepcopy(DEFAULT_COLOR_THRESHOLDS)
    merged_color.update(cfg_data.get("color_thresholds", {}))

    resolved_log_dir = Path(log_dir) if log_dir else Path(cfg_data.get("log_dir", "logs"))
    resolved_log_dir.mkdir(parents=True, exist_ok=True)
    resolved_log_format = (log_format or cfg_data.get("log_format") or "pretty").lower()

    from logs import create_logger

    logger = create_logger(resolved_log_dir, resolved_log_format)

    return AppConfig(
        shape_thresholds=merged_shape,
        color_thresholds=merged_color,
        logger=logger,
        log_format=resolved_log_format,
    )
