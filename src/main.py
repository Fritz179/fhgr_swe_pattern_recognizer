import cv2 as cv
from pathlib import Path
from collections.abc import Sequence
from datetime import datetime
import numpy as np

from src.configs import AppConfig

def parse_args(argv: Sequence[str] | None = None):
    """
    Parse command line arguments.

    Returns an argparse.Namespace with at least:
      - mode: Literal["CAMERA", "IMAGE"]
      - image_dir: Path | None
      - config_path: Path | None
      - log_dir: Path | None
    """

def main() -> None:
    """Entry point of the application."""

def run_camera_mode(config: AppConfig) -> None:
    """
    Run the application in CAMERA mode:
    - open webcam
    - process each frame
    - visualize detections
    - log detections to CSV
    """

def run_image_mode(config: AppConfig, image_dir: Path) -> None:
    """
    Run the application in IMAGE mode:
    - iterate over all images in image_dir
    - process each image
    - optionally save annotated images
    - log detections to CSV
    """