import cv2 as cv
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from configs import AppConfig

# Fallback thresholds in case the AppConfig is not fully populated yet.
DEFAULT_SHAPE_THRESHOLDS = {
    "min_area": 300,                  # skip tiny contours/noise
    "square_aspect_tolerance": 0.15,  # how far from 1.0 the aspect ratio may deviate
    "circularity": 0.8,               # 1.0 is a perfect circle
    "approx_epsilon": 0.04,           # approximation factor for polygonal curves
}

# HSV ranges for basic colors; values can be overridden via config.color_thresholds.
DEFAULT_COLOR_RANGES: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {
    "RED": [
        (np.array([0, 70, 50]), np.array([10, 255, 255])),
        (np.array([170, 70, 50]), np.array([180, 255, 255])),
    ],
    "GREEN": [(np.array([35, 40, 40]), np.array([85, 255, 255]))],
    "BLUE": [(np.array([90, 50, 50]), np.array([130, 255, 255]))],
    "YELLOW": [(np.array([20, 100, 100]), np.array([35, 255, 255]))],
    "VIOLET": [(np.array([130, 50, 50]), np.array([160, 255, 255]))],
}

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
        x, y, w, h = self.bbox
        color_map = {
            "RED": (0, 0, 255),
            "GREEN": (0, 255, 0),
            "BLUE": (255, 0, 0),
            "YELLOW": (0, 255, 255),
            "VIOLET": (211, 0, 148),
            "UNKNOWN": (255, 255, 255),
        }
        box_color = color_map.get(self.color.upper(), (255, 255, 255))

        cv.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)

        font = cv.FONT_HERSHEY_DUPLEX
        scale = 1
        thickness = 1
        pattern_text = self.pattern.capitalize()
        color_text = self.color.upper()
        space_size, _ = cv.getTextSize(" ", font, scale, thickness)
        pattern_size, _ = cv.getTextSize(pattern_text, font, scale, thickness)
        color_size, baseline = cv.getTextSize(color_text, font, scale, thickness)

        total_w = pattern_size[0] + space_size[0] + color_size[0]
        total_h = max(pattern_size[1], color_size[1]) + baseline
        padding = 5
        text_x = x
        text_y = max(total_h + padding, y - 10)

        bg_tl = (text_x - padding, text_y - total_h)
        bg_br = (text_x + total_w + padding, text_y + padding)
        cv.rectangle(frame, bg_tl, bg_br, (0, 0, 0), thickness=-1)

        cv.putText(
            frame,
            pattern_text,
            (text_x, text_y),
            font,
            scale,
            (255, 255, 255),
            thickness,
            lineType=cv.LINE_4,
        )
        color_x = text_x + pattern_size[0] + space_size[0]
        cv.putText(
            frame,
            color_text,
            (color_x, text_y),
            font,
            scale,
            box_color,
            thickness,
            lineType=cv.LINE_4,
        )
        return frame


def _resolve_shape_thresholds(config: AppConfig | None) -> dict:
    cfg = getattr(config, "shape_thresholds", None) or {}
    return {**DEFAULT_SHAPE_THRESHOLDS, **cfg}


def _resolve_color_ranges(config: AppConfig | None) -> dict[str, list[tuple[np.ndarray, np.ndarray]]]:
    """
    Normalize color thresholds from the config into HSV numpy arrays.

    The config can provide either:
      - a list of (lower, upper) HSV pairs
      - a single dict with ``lower``/``upper`` keys
      - a list of such dicts
    """
    ranges = DEFAULT_COLOR_RANGES.copy()
    cfg = getattr(config, "color_thresholds", None) or {}

    for name, bounds in cfg.items():
        normalized: list[tuple[np.ndarray, np.ndarray]] = []

        # Allow a single dict {lower: [...], upper: [...]} as shorthand.
        if isinstance(bounds, dict) and "lower" in bounds and "upper" in bounds:
            bounds = [(bounds["lower"], bounds["upper"])]

        for entry in bounds:
            if isinstance(entry, dict) and "lower" in entry and "upper" in entry:
                lower, upper = entry["lower"], entry["upper"]
            else:
                lower, upper = entry

            normalized.append(
                (np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
            )

        ranges[name.upper()] = normalized

    return ranges


def _classify_shape(contour: np.ndarray, thresholds: dict) -> str | None:
    peri = cv.arcLength(contour, True)
    epsilon_factor = thresholds.get("approx_epsilon", 0.04)
    approx = cv.approxPolyDP(contour, epsilon_factor * peri, True)
    area = cv.contourArea(contour)

    if area < thresholds["min_area"] or peri == 0:
        return None

    vertices = len(approx)
    if vertices == 3:
        return "triangle"
    if vertices == 4:
        x, y, w, h = cv.boundingRect(approx)
        aspect_ratio = w / float(h)
        tolerance = thresholds["square_aspect_tolerance"]
        return "square" if abs(aspect_ratio - 1.0) <= tolerance else "rectangle"

    circularity = 4 * np.pi * area / (peri * peri)
    if circularity >= thresholds["circularity"]:
        return "circle"
    return None


def _detect_color(hsv_frame: np.ndarray, contour: np.ndarray, color_ranges: dict[str, list[tuple[np.ndarray, np.ndarray]]]) -> str:
    mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
    cv.drawContours(mask, [contour], -1, 255, thickness=-1)
    total_pixels = cv.countNonZero(mask)
    if total_pixels == 0:
        return "UNKNOWN"

    best_color = "UNKNOWN"
    best_ratio = 0.0
    for color_name, bounds in color_ranges.items():
        color_mask = np.zeros_like(mask)
        for lower, upper in bounds:
            color_mask |= cv.inRange(hsv_frame, lower, upper)
        color_mask = cv.bitwise_and(color_mask, mask)
        ratio = cv.countNonZero(color_mask) / total_pixels
        if ratio > best_ratio:
            best_ratio = ratio
            best_color = color_name

    return best_color if best_ratio >= 0.05 else "UNKNOWN"


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
    if frame is None or frame.size == 0:
        return []

    thresholds = _resolve_shape_thresholds(config)
    color_ranges = _resolve_color_ranges(config)

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv.threshold(blurred, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    inverted = cv.bitwise_not(thresh)
    if cv.countNonZero(thresh) > cv.countNonZero(inverted):
        thresh = inverted
    contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    detections: list[DetectionResult] = []

    for contour in contours:
        shape = _classify_shape(contour, thresholds)
        if shape is None:
            continue

        x, y, w, h = cv.boundingRect(contour)
        color = _detect_color(hsv, contour, color_ranges)

        detections.append(
            DetectionResult(
                timestamp=timestamp,
                pattern=shape,
                color=color,
                bbox=(x, y, w, h),
            )
        )

    return detections
