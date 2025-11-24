from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from logging import CSVLogger


DEFAULT_SHAPE_THRESHOLDS: dict[str, Any] = {
    "min_area": 400,  # minimum contour area to consider
    "approx_epsilon": 0.02,  # approximation factor for polygonal curves
    "canny_low": 50,
    "canny_high": 150,
}

DEFAULT_COLOR_THRESHOLDS: dict[str, dict[str, list[int]]] = {
    "RED": {"lower": [0, 120, 70], "upper": [10, 255, 255]},
    "GREEN": {"lower": [36, 50, 70], "upper": [89, 255, 255]},
    "BLUE": {"lower": [90, 50, 70], "upper": [128, 255, 255]},
    "YELLOW": {"lower": [15, 100, 100], "upper": [35, 255, 255]},
    "VIOLET": {"lower": [129, 50, 70], "upper": [158, 255, 255]},
}


@dataclass
class AppConfig:
    source_type: str  # "CAMERA" or "IMAGE"
    image_dir: Path | None
    log_dir: Path
    shape_thresholds: dict
    color_thresholds: dict
    logger: "CSVLogger"


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
    mode: str,
    image_dir: Path | None,
) -> AppConfig:
    """
    Build an AppConfig by merging defaults with an optional config file and CLI overrides.
    """
    cfg_data = (
        _load_config_file(config_path)
        if config_path is not None
        else {}
    )

    mode_upper = mode.upper()
    if mode_upper not in {"CAMERA", "IMAGE"}:
        raise ValueError("Mode must be 'CAMERA' or 'IMAGE'.")

    resolved_image_dir = Path(image_dir) if image_dir else None
    if mode_upper == "IMAGE" and resolved_image_dir is None:
        raise ValueError("IMAGE mode requires an image directory.")

    merged_shape = {
        **copy.deepcopy(DEFAULT_SHAPE_THRESHOLDS),
        **cfg_data.get("shape_thresholds", {}),
    }
    merged_color = copy.deepcopy(DEFAULT_COLOR_THRESHOLDS)
    merged_color.update(cfg_data.get("color_thresholds", {}))

    resolved_log_dir = Path(log_dir) if log_dir else Path(cfg_data.get("log_dir", "logs"))
    resolved_log_dir.mkdir(parents=True, exist_ok=True)

    # Local import to avoid confusion with stdlib logging module name.
    from logging import CSVLogger

    logger = CSVLogger(resolved_log_dir)

    return AppConfig(
        source_type=mode_upper,
        image_dir=resolved_image_dir,
        log_dir=resolved_log_dir,
        shape_thresholds=merged_shape,
        color_thresholds=merged_color,
        logger=logger,
    )
