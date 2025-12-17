import argparse
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import cv2 as cv
import numpy as np

from configs import AppConfig, load_config
from process import detect_shapes

def parse_args(argv: Sequence[str] | None = None):
    """
    Parse command line arguments.

    Returns an argparse.Namespace with at least:
      - mode: Literal["CAMERA", "IMAGE"]
      - image_dir: Path | None
      - config_path: Path | None
      - log_dir: Path | None
    """

    parser = argparse.ArgumentParser(description="Pattern recognizer")

    parser.add_argument(
        "mode",
        nargs="?",
        choices=["CAMERA", "IMAGE"],
        default="CAMERA",
        help="Run with webcam (CAMERA) or on a folder of images (IMAGE).",
    )

    parser.add_argument(
        "-i",
        "--image-dir",
        type=Path,
        default=None,
        help="Directory containing images to process in IMAGE mode.",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        type=Path,
        default=None,
        help="Directory where annotated images will be written in IMAGE mode. "
        "Defaults to <image-dir>_annotated.",
    )

    parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        type=Path,
        default=None,
        help="Optional path to a config file.",
    )

    parser.add_argument(
        "-l",
        "--log-dir",
        dest="log_dir",
        type=Path,
        default=None,
        help="Directory where logs will be written.",
    )

    parser.add_argument(
        "-f",
        "--log-format",
        dest="log_format",
        choices=["csv", "pretty"],
        default=None,
        help="Logging format: 'csv' or 'pretty' (table-style text).",
    )

    args = parser.parse_args(argv)
    if args.mode == "IMAGE" and args.image_dir is None:
        parser.error("IMAGE mode requires --image-dir")

    return args

def main() -> None:
    """Entry point of the application."""
    args = parse_args()
    config = load_config(args.config_path, args.log_dir, args.log_format)

    print(f"Running in {args.mode} mode.")

    try:
        if args.mode == "CAMERA":
            run_camera_mode(config)
        else:
            run_image_mode(config, args.image_dir, args.output_dir)
    finally:
        config.logger.close()


def run_camera_mode(config: AppConfig) -> None:
    """
    Run the application in CAMERA mode:
    - open webcam
    - process each frame
    - visualize detections in a GUI
    - optional logging and saving through GUI controls
    """
    from PyQt5 import QtWidgets  # imported here to avoid hard dependency in IMAGE mode
    from gui import CameraWindow

    app = QtWidgets.QApplication([])
    window = CameraWindow(config)
    window.show()
    app.exec_()

def run_image_mode(config: AppConfig, image_dir: Path, output_dir: Path | None) -> None:
    """
    Run the application in IMAGE mode:
    - iterate over all images in image_dir
    - process each image
    - optionally save annotated images
    - log detections to CSV
    """
    if not image_dir.is_dir():
        raise NotADirectoryError(f"{image_dir} is not a directory.")

    dest_dir = output_dir or image_dir.with_name(f"{image_dir.name}_annotated")
    dest_dir.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(
        p
        for p in image_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    )

    for path in image_paths:
        frame = cv.imread(str(path))
        if frame is None:
            continue

        timestamp = datetime.fromtimestamp(path.stat().st_mtime)
        detections = detect_shapes(frame, config, timestamp) or []

        for det in detections:
            frame = det.draw_detections(frame)

        if detections:
            config.logger.write(detections)

        annotated_path = dest_dir / path.name
        cv.imwrite(str(annotated_path), frame)


if __name__ == "__main__":
    main()
