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

## YOLO setup

`ultralytics` and `opencv-python` are declared in `requirements.txt`. On first YOLO use, Ultralytics downloads a compatible pretrained weight file, which requires internet access. The RTX 3050 will be used only after installing a PyTorch build that matches your CUDA driver; check the current command at https://pytorch.org/get-started/locally/ before installing it. The current UI and uploads work without GPU acceleration; detection processing is the next implementation step after dependencies are installed.

Do not issue fines automatically. The fine-evidence screen is intentionally designed for an administrator to review and confirm AI evidence.
