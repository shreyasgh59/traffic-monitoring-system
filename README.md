# Traffic Monitoring System

## First-time setup (Windows PowerShell)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations monitoring
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`, create an account, then upload a local test video.

The initial database is SQLite so the project runs immediately. To use MySQL 8, install the MySQL C connector/build tools if `mysqlclient` needs compilation, create a database, and replace the `DATABASES` value in `trafficwatch/settings.py` with the MySQL settings.

## Current implementation

- Registration and username/email sign-in, with separate administrator and user portals.
- A normalized `registered_vehicles` registry seeded idempotently with `KA01AB1234` through `KA10AB1234`.
- Live Monitoring starts with a blank player. Administrators select/deselect a queued clip, an IP Webcam URL, or a browser camera before it loads; selected clips provide an authenticated MJPEG feed.
- Each uploaded clip can be analysed on demand. Per-video traffic classifications, timestamps, annotated preview frames, and congestion scores are persisted and rendered in Traffic reports.
- Administrator-generated, timestamped helmet-violation reports with exactly one JPG/JPEG/PNG snapshot and protected vehicle-number lookup for issued fines.

## YOLO setup

`ultralytics` and `opencv-python` are declared in `requirements.txt`. On first analysis, Ultralytics downloads the compatible `yolo11n.pt` pretrained weight file, which requires internet access. The RTX 3050 will be used only after installing a PyTorch build that matches your CUDA driver; check the current command at https://pytorch.org/get-started/locally/ before installing it. The application works with CPU processing, although it will be slower.

Do not issue fines automatically. The fine-evidence screen is intentionally designed for an administrator to review and confirm AI evidence.

## Known limitations before deployment

- Live YOLO inference runs synchronously for each browser stream. Large or multiple concurrent clips can occupy the server; move inference to a background worker/service for production.
- The current traffic-density value is an estimate based on YOLO vehicle counts, not calibrated physical road coverage.
- `DEBUG=True`, the development secret key, SQLite, and the seeded demonstration accounts are suitable only for local coursework. Replace these and configure secure media storage before deployment.
- Fine evidence remains human-reviewed. Plate numbers are not read automatically; add a validated OCR pipeline before any real enforcement workflow.
