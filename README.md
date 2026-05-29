# United Fire Backflow Report App

## Setup

1. Place **backflow_template.pdf** (your original United Fire form scan) in this folder
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   streamlit run app.py
   ```

## Deploy on Streamlit Cloud (Free)

1. Create a GitHub repo and push all files including **backflow_template.pdf**
2. Go to https://share.streamlit.io → New app
3. Select your repo, set main file = `app.py`
4. Deploy — you'll get a URL usable on any phone or browser

## ⭐ Sticky Fields (persist across Clear Form)
Branch, AHJ, Manufacturer, Model, Size,
Gauge Manufacturer, Gauge Serial #, Date Calibrated,
Technician, Certification No., Re-Cert Due Date

## Field Numbers (matching Excel mapping)
| # | Field |
|---|---|
| 1 | Date |
| 2 | Branch |
| 3 | AHJ |
| 4 | Customer / Site Name |
| 5 | Street Address |
| 6 | Location of Assembly |
| 7 | Serial Number |
| 8 | Manufacturer |
| 9 | Model |
| 10 | Size |
| 11.1-4 | Type of Assembly (RP/DC/PVB/SVB) |
| 12.1-4 | System Service (Fire/Domestic/Irrigation/Attraction) |
| 13.1-2 | Bypass Yes/No |
| 14.1-2 | CV1 Closed Tight / Leaked |
| 15 | CV1 DP PSI |
| 16.1-2 | CV2 Closed Tight / Leaked |
| 17 | CV2 DP PSI |
| 18.1 | PVB Air Inlet Closed Tight |
| 18.2 | PVB Check Valve Leaked |
| 19.1 | PVB Air Inlet Opened At |
| 19.2 | PVB Check Valve Held At |
| 20 | PVB Air Inlet PSI |
| 21 | PVB Check Valve PSI |
| 22 | Test Date |
| 23/24 | Passed / Failed |
| 25.1-2 | RV Opened At / Did Not Open |
| 26 | RV PSI |
| 27.1-2 | Outlet S/O Closed / Leaked |
| 28.1-2 | Inlet S/O Closed / Leaked |
| 29 | Remarks / Repairs Needed |
| 30 | Gauge Manufacturer |
| 31 | Gauge Serial # |
| 32 | Date Calibrated |
| 33 | Certification No. |
| 34 | Re-Cert Due Date |

## PDF Output Naming
Files are auto-named:
`CustomerName - StreetAddress.pdf`
e.g. `Publix 1234 - 4602 35th Street.pdf`
