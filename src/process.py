import numpy as np
from dataclasses import dataclass
from datetime import datetime
from configs import AppConfig

@dataclass
class DetectionResult:
    timestamp: datetime
    pattern: str           # "circle", "square", "rectangle", "triangle"
    color: str             # "RED", "GREEN", "BLUE", "YELLOW", "VIOLET"
    bbox: tuple[int, int, int, int]  # (x, y, w, h)

    def draw_detections(self, frame: np.ndarray) -> np.ndarray:
        """
        Overlay bounding boxes and labels (pattern + color) on the frame.

        Returns a new annotated frame (or modifies frame in-place and returns it).
        """


def detect_shapes(
    frame: np.ndarray,
    config: AppConfig,
    timestamp: datetime,
) -> list[DetectionResult]:
    """
    High-level processing of a single frame:
    - detect shapes
    - detect colors inside each shape
    - return a list of DetectionResult entries
    """