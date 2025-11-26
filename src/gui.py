from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

import cv2 as cv

# Reset Qt plugin path set by OpenCV to avoid conflicts with PyQt's plugins.
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
from gtts import gTTS

from process import detect_shapes

# Ensure the plugin path points to PyQt's plugins if not already set.
try:
    plugin_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)
    if plugin_path:
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", plugin_path)
except Exception:
    # If location is unavailable, we leave the env untouched.
    pass


class CameraWindow(QtWidgets.QMainWindow):
    """
    PyQt GUI for camera mode with controls for saving, logging, FPS, pause, and speech output.
    """

    def __init__(self, config) -> None:
        super().__init__()
        self.setWindowTitle("Pattern Recognizer")

        self.config = config
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open the default camera.")

        self.output_dir = Path("camera_annotated")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.paused = False
        self.last_frame = None
        self.last_detections = []
        self._temp_audio_path: str | None = None

        self.audio_player = QtMultimedia.QMediaPlayer()
        self.audio_player.stateChanged.connect(self._cleanup_audio)

        self._build_ui()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self._apply_fps(self.fps_slider.value())
        self.timer.start(self._interval_ms)

    # -- UI setup ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        layout.addWidget(self.image_label)

        controls = QtWidgets.QHBoxLayout()

        self.save_log_btn = QtWidgets.QPushButton("Save image")
        self.save_log_btn.clicked.connect(self.save_image_and_log)
        controls.addWidget(self.save_log_btn)

        self.pause_btn = QtWidgets.QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        controls.addWidget(self.pause_btn)

        fps_layout = QtWidgets.QVBoxLayout()
        fps_label_layout = QtWidgets.QHBoxLayout()
        fps_label_layout.addWidget(QtWidgets.QLabel("FPS"))
        self.fps_value_label = QtWidgets.QLabel("")
        fps_label_layout.addWidget(self.fps_value_label)
        fps_layout.addLayout(fps_label_layout)

        self.fps_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fps_slider.setMinimum(1)
        self.fps_slider.setMaximum(30)
        self.fps_slider.setValue(15)
        self.fps_slider.valueChanged.connect(self.on_fps_changed)
        fps_layout.addWidget(self.fps_slider)
        controls.addLayout(fps_layout)

        self.speak_btn = QtWidgets.QPushButton("Speak detections")
        self.speak_btn.clicked.connect(self.speak_detections)
        controls.addWidget(self.speak_btn)

        layout.addLayout(controls)
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.on_fps_changed()

    # -- Frame processing -----------------------------------------------------------
    def update_frame(self) -> None:
        if self.paused:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        timestamp = datetime.now()
        detections = detect_shapes(frame, self.config, timestamp) or []
        annotated = frame.copy()
        for det in detections:
            annotated = det.draw_detections(annotated)

        self.last_frame = annotated
        self.last_detections = detections
        self._display_frame(annotated)

    def _display_frame(self, frame) -> None:
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        ))

    # -- Controls -------------------------------------------------------------------
    def save_image_and_log(self) -> None:
        if self.last_frame is not None:
            filename = self.output_dir / f"frame_{datetime.now():%Y%m%d_%H%M%S%f}.png"
            cv.imwrite(str(filename), self.last_frame)
        if self.last_detections:
            self.config.logger.write(self.last_detections)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_btn.setText("Resume" if self.paused else "Pause")

    def on_fps_changed(self) -> None:
        value = self.fps_slider.value()
        if value == self.fps_slider.maximum():
            self.fps_value_label.setText("Unlimited")
        else:
            self.fps_value_label.setText(str(value))
        self._apply_fps(value)

    def _apply_fps(self, slider_value: int) -> None:
        if slider_value == self.fps_slider.maximum():
            self._interval_ms = 0  # run as fast as possible
        else:
            self._interval_ms = max(1, int(1000 / max(1, slider_value)))
        if hasattr(self, "timer"):
            self.timer.setInterval(self._interval_ms)

    def speak_detections(self) -> None:
        if not self.last_detections:
            text = "No objects detected."
        else:
            parts = []
            for idx, det in enumerate(self.last_detections, start=1):
                parts.append(
                    f"Shape {idx} is a {det.color.capitalize()} {det.pattern.capitalize()}"
                )
            text = f"Detected {len(self.last_detections)} objects: " + ", ".join(parts)

        if self.audio_player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.audio_player.stop()
        if self._temp_audio_path:
            try:
                os.remove(self._temp_audio_path)
            except Exception:
                pass
            self._temp_audio_path = None

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            gTTS(text=text).save(tmp.name)
            self._temp_audio_path = tmp.name

        url = QtCore.QUrl.fromLocalFile(self._temp_audio_path)
        self.audio_player.setMedia(QtMultimedia.QMediaContent(url))
        self.audio_player.play()

    def _cleanup_audio(self, state) -> None:
        if state == QtMultimedia.QMediaPlayer.StoppedState and self._temp_audio_path:
            try:
                os.remove(self._temp_audio_path)
            except Exception:
                pass
            self._temp_audio_path = None

    # -- Cleanup --------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # type: ignore[override]
        if hasattr(self, "cap") and self.cap:
            self.cap.release()
        self.config.logger.close()
        super().closeEvent(event)

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == QtCore.Qt.Key_Q:
            self.close()
        else:
            super().keyPressEvent(event)
