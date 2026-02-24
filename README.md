# Mashup Assignment Solution (Roll No: 102317160)

This repository contains both required programs for the Mashup assignment:
- Program 1: Command-line Python script (`102317160.py`)
- Program 2: Web service (`app.py`) that emails a ZIP containing the mashup

## Project Structure
- `102317160.py`: CLI entrypoint required by assignment
- `app.py`: Flask web app for user input + email delivery
- `mashup_core.py`: Shared mashup logic (download, trim, merge)
- `requirements.txt`: Python dependencies
- `Procfile`: Render start command (`gunicorn app:app`)

## Requirements
- Python 3.10+
- Internet connection
- FFmpeg (local install recommended)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Program 1 (CLI)
File: `102317160.py`

### Usage
```bash
python 102317160.py "Singer Name" <NumberOfVideos> <AudioDurationSec> <OutputFileName>
```

Example:
```bash
python 102317160.py "Sharry Maan" 11 21 102317160-output.mp3
```

### Input Rules (as per assignment)
- Correct number of parameters is mandatory
- `NumberOfVideos` must be greater than `10`
- `AudioDurationSec` must be greater than `20`
- Exceptions are handled with user-friendly error messages

### Output
- A merged MP3 mashup at the output file path you provide

## Program 2 (Web Service)
File: `app.py`

The web app accepts:
- Singer name
- Number of videos (>10)
- Duration in seconds (>20)
- Email address

It generates a mashup, zips it, and sends it via email.

### Run Locally
Set SMTP variables first.

PowerShell:
```powershell
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your_email@gmail.com
set SMTP_PASS=your_16_char_app_password
set SMTP_FROM=your_email@gmail.com
python app.py
```

Open:
- `http://localhost:5000`

## Gmail SMTP Setup (App Password)
Do not use your normal Gmail password.

1. Go to `https://myaccount.google.com/security`
2. Enable **2-Step Verification**
3. Open **App passwords**
4. Create a new app password
5. Use that 16-character value in `SMTP_PASS`

## Render Deployment
1. Push project to GitHub.
2. In Render: **New > Web Service**.
3. Select your repo and branch.
4. Use:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add environment variables:
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USER`
   - `SMTP_PASS`
   - `SMTP_FROM`
6. Deploy and open the Render URL.

## Important Notes
- YouTube can rate-limit/block some downloads; retries or a different singer may be needed.
- On hosted environments, long mashup requests may take time.
- Keep secrets only in environment variables (never hardcode passwords).

<img width="1917" height="967" alt="image" src="https://github.com/user-attachments/assets/5583f8ff-19c6-4935-9557-ca331e130339" />


## Submission Checklist
- Program 1: submit `102317160.py`
- Program 2: submit deployed web app link
- Keep a sample generated output file for demonstration/testing

