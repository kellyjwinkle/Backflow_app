# United Fire – Backflow Test Report App

A Streamlit app that fills in the United Fire Backflow Preventer Assembly Test & Maintenance Report PDF using your actual form as the template.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files Required
- `app.py` — the application
- `backflow_template.pdf` — your United Fire form (already in repo)
- `requirements.txt`
- `session_data.json` — auto-created on first save

## Features
- Fills in your exact United Fire form template
- All checkboxes mark with an X on the actual form
- PDF named automatically: `Customer Name - Street Address.pdf`
- Lock Site Info between jobs — tester info persists
- Save/restore full session
- Clear Form keeps tester/branch info sticky

## Deploy on Streamlit Community Cloud (free)
1. Push all files to a GitHub repo
2. Go to https://share.streamlit.io
3. Connect your repo and set `app.py` as the entry point
4. Done — access from any device including phone
