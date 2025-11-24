import cv2 as cv
import argparse
from pathlib import Path
from collections.abc import Sequence
from datetime import datetime
import numpy as np

from configs import AppConfig
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
        help="Directory where CSV logs will be written.",
    )

    args = parser.parse_args(argv)
    if args.mode == "IMAGE" and args.image_dir is None:
        parser.error("IMAGE mode requires --image-dir")

    return args

def main() -> None:
    """Entry point of the application."""
    args = parse_args()
    config = AppConfig(args.config_path, args.log_dir)
    config.source_type = args.mode

    print(f"Running in {args.mode} mode.")

    if args.mode == "CAMERA":
        run_camera_mode(config)
    else:
        run_image_mode(config, args.image_dir)


def run_camera_mode(config: AppConfig) -> None:
    """
    Run the application in CAMERA mode:
    - open webcam
    - process each frame
    - visualize detections
    - log detections to CSV
    """
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open the default camera.")

    window_name = "Pattern Recognizer"

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = datetime.now()
            detections = detect_shapes(frame, config, timestamp) or []

            for det in detections:
                frame = det.draw_detections(frame)

            cv.imshow(window_name, frame)
            if cv.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv.destroyAllWindows()

def run_image_mode(config: AppConfig, image_dir: Path) -> None:
    """
    Run the application in IMAGE mode:
    - iterate over all images in image_dir
    - process each image
    - optionally save annotated images
    - log detections to CSV
    """
    if not image_dir.is_dir():
        raise NotADirectoryError(f"{image_dir} is not a directory.")

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

        annotated_path = path.with_name(f"{path.stem}_annotated{path.suffix}")
        cv.imwrite(str(annotated_path), frame)


if __name__ == "__main__":
    main()