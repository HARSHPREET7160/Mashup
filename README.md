# Mashup Assignment Solution (Roll No: 102317160)

## Program 1 (CLI)
File: `102317160.py`

### Install dependencies
```bash
pip install -r requirements.txt
```

### Usage
```bash
python 102317160.py "Singer Name" <NumberOfVideos> <AudioDurationSec> <OutputFileName>
```

Example:
```bash
python 102317160.py "Sharry Maan" 20 30 102317160-output.mp3
```

Rules enforced:
- Correct number of parameters required.
- `NumberOfVideos` must be greater than 10.
- `AudioDurationSec` must be greater than 20.
- Exceptions are handled with readable error messages.

## Program 2 (Web Service)
File: `app.py`

### Required SMTP environment variables
```bash
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your_email@example.com
set SMTP_PASS=your_app_password
set SMTP_FROM=your_email@example.com
```

### Run web app
```bash
python app.py
```
Open: `http://localhost:5000`

User inputs:
- Singer name
- Number of videos (>10)
- Duration in seconds (>20)
- Valid email ID

Result:
- Mashup is generated, zipped, and sent to the provided email address.

## Notes
- Internet is required for YouTube download.
- `moviepy` requires ffmpeg runtime; if missing, install ffmpeg or ensure `imageio-ffmpeg` can fetch binary.
