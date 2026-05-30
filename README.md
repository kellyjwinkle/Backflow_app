# United Fire Backflow Report App

## Setup
1. Place **backflow_template.pdf** in this folder (same dir as app.py)
2. `pip install -r requirements.txt`
3. `streamlit run app.py`

## GitHub Pages / Streamlit Cloud
1. Create GitHub repo, push all files + backflow_template.pdf
2. Go to https://share.streamlit.io → New app → select repo → app.py
3. Deploy — get a URL for phone/browser access

## Coordinate Calibration
Coordinates were derived from your PPTX text box positions (EMU → PDF 612×792 pts).
To adjust: edit TEXT_FIELDS or CHECKBOXES dicts in app.py.
x increases left→right, y increases bottom→top (PDF coordinate system).

## ⭐ Sticky Fields
Branch, AHJ, Manufacturer, Model, Size, Gauge Mfg, Gauge Serial,
Date Calibrated, Technician, Cert No., Re-Cert Date

## PDF Filename
Auto-named: CustomerName - StreetAddress.pdf
