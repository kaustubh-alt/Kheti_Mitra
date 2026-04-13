# KhetiMitra Backend - Setup, Install and Run

This file provides instructions to download, install dependencies, and run the project.

## 1. Prerequisites

- Windows 10/11 (or Linux/Mac with minor path adjustments)
- Python 3.10+ (3.11 recommended)
- Git
- [Optional] GPU + CUDA drivers when using GPU inference (PyTorch CUDA build)

## 2. Clone repository

```powershell
cd C:\Programs
git clone <YOUR_REPO_URL> khetiback
cd khetiback
```

> Replace `<YOUR_REPO_URL>` with the actual remote URL.

## 3. Create Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> On cmd.exe: `.\.venv\Scripts\activate.bat`.

## 4. Install Python dependencies

### Option A (full stack - includes API and google generative)

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Option B (model-only, recommended for your GitHub model tester scenario)

```powershell
pip install --upgrade pip
pip install -r requirements-model.txt
```

`requirements-model.txt` contains:

- torch
- torchvision
- pillow
- pandas

> This mode skips FastAPI, `google-generativeai`, and `python-dotenv` entirely, to focus on model inference only.

- For GPU (CUDA) versions see: https://pytorch.org/get-started/locally/

## 5. Verify model files

Required data files in project root:

- `plant-disease-model-complete.pth`
- `disease_info.csv`
- `model/SoilNet_93_86.h5`

## 6. Standalone model-only usage (recommended for GitHub users)

This section is for users who want to run only the disease model without FastAPI or Google APIs.

### 6.1 Required additional libraries

Install minimal inference dependencies:

```powershell
pip install torch torchvision pillow pandas
```

### 6.2 Run local inference script

Use the `disease_detector.py` helper added to the repo:

```powershell
python disease_detector.py "C:\Users\kaust\Downloads\leaf.jpg"
```

Expected output (JSON-like dict):

- `prediction_idx`
- `confidence`
- `disease_name`
- `description`
- `prevention`

### 6.3 Programmatic usage

```python
from disease_detector import get_prediction

result = get_prediction(r"C:\Users\kaust\Downloads\leaf.jpg")
print(result)
```

## 7. Run the API server

Use Uvicorn:

```powershell
pip install uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

This starts the API at `http://127.0.0.1:8000`.

## 7. API endpoints

- `POST /plant` : disease prediction
  - JSON body: `{ "image_url": "<filename.jpg>" }`
- `POST /soil/` : soil model
  - JSON body: `{ "image_url": "<filename.jpg>" }`
- `POST /crop` : crop recommendation
  - JSON body: `{ "N": ..., "P": ..., "K": ..., "temperature": ..., "humidity": ..., "ph": ..., "rainfall": ... }`

## 8. Run prediction script (wrapper)

New file `disease_detector.py` provides a direct function call:

```python
from disease_detector import get_prediction

result = get_prediction(r"C:\Users\kaust\Downloads\image.jpg")
print(result)
```

Or as standalone:

```powershell
python disease_detector.py "C:\Users\kaust\Downloads\image.jpg"
```

## 9. Troubleshooting

- `FileNotFoundError` for model: confirm `plant-disease-model-complete.pth` exists in root
- `PermissionError`: check virtual environment activation and run as user with file access
- GPU not available: falls back to CPU in `diseases.py` via `torch.device(...)`

## 10. Notes

- Keep `disease_info.csv` in sync with your `plant-disease-model-complete.pth` class indices.
- Update CORS in `main.py` before production (current config allows all origins).
