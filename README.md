# United Fire Backflow Preventer Test Report App

## Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud (Free)
1. Push this folder to GitHub (your existing `Backflow_app` repo)
2. Go to https://share.streamlit.io
3. New App → select repo → `app.py` → Deploy
4. Access from any device via the URL

## Files Required
- `app.py` — the Streamlit application
- `backflow_template.pdf` — your United Fire form (CamScanner scan)
- `requirements.txt` — Python dependencies

## Features
- Fills your exact United Fire PDF template
- All checkboxes (CV1, RV, CV2, PVB/SVB, Assembly Type, System Service, Bypass, Repairs)
- Sticky tester fields (Branch, AHJ, Gauge info, Technician) preserved on Clear
- Auto-named PDF: `CustomerName - StreetAddress.pdf`
- Session save/load across browser sessions
