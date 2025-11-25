# fhgr_swe_pattern_recognizer

## Getting started

### create a new virtual env in .venv
```
python3 -m venv .venv
```

#### activate it (Linux/macOS)
```
source .venv/bin/activate
```
#### (Windows PowerShell)
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

#### upgrade pip and install requirements
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### run the program
```
python src/main.py IMAGE -i assets
```

## usage
- Camera live detection: `python src/main.py CAMERA`
- Process a folder of images: `python src/main.py IMAGE -i assets`
- Process a folder and choose an output directory (annotated images): `python src/main.py IMAGE -i assets -o annotated_output`
- Optional config file / log location / format: `python src/main.py CAMERA --config config.yaml --log-dir logs --log-format csv`
- `--log-format` can be `pretty` (sample_log-style table) or `csv`.
- Press `q` to quit the camera window.
- CAMERA mode opens a PyQt GUI with:
  - live feed, pause/resume
  - FPS slider (1-30, max = unlimited)
  - Save image button (saves to `camera_annotated/` and logs detections for that frame)
  - Speak detections button (gTTS + QtMultimedia playback)

### config file example (YAML)
```yaml
log_dir: logs
log_format: pretty  # or csv
shape_thresholds:
  min_area: 350
  square_aspect_tolerance: 0.1
  circularity: 0.82
  approx_epsilon: 0.04
color_thresholds:
  RED:
    - lower: [0, 70, 50]
      upper: [10, 255, 255]
    - lower: [170, 70, 50]
      upper: [180, 255, 255]
  GREEN:
    - lower: [35, 40, 40]
      upper: [85, 255, 255]
```

Color thresholds accept either a list of `[lower, upper]` pairs or explicit `lower`/`upper` objects per color as shown above.

### logging
Each detection is appended in the chosen format to `logs/` by default:
- `pretty`: ASCII table matching `log_sample.txt` (`Timestamp | Pattern | Color`)
- `csv`: plain CSV with header `Timestamp,Pattern,Color`
