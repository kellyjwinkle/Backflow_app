import streamlit as st
from io import BytesIO
import json, os, re
from datetime import date

try:
    from pdfrw import PdfReader, PdfWriter
    from pdfrw import PageMerge
    from reportlab.pdfgen import canvas
    LIBS_OK = True
except ImportError:
    LIBS_OK = False

TEMPLATE_PATH = "backflow_template.pdf"
SESSION_FILE  = "session_data.json"
PAGE_W, PAGE_H = 612, 1008

# ── Verified checkbox coordinates (calibrated to CamScanner template) ──
CHECKBOXES = {
    "RP":  (222.0, 591.3), "DC":  (293.0, 591.3),
    "PVB": (222.0, 579.0), "SVB": (293.0, 579.0),
    "FIRE":       (434.0, 626.0), "DOMESTIC":   (434.0, 607.0),
    "IRRIGATION": (426.0, 591.3), "ATTRACTION": (426.0, 576.0),
    "BYPASS_YES": (563.0, 607.0), "BYPASS_NO":  (563.0, 591.3),
    "CV1_CLOSED": (64.8, 518.0), "CV1_LEAKED": (64.8, 506.0), "CV1_NA": (64.8, 494.0),
    "RV_OPENED":     (154.5, 518.0), "RV_DIDNOTOPEN": (154.5, 506.0), "RV_NA": (201.1, 506.0),
    "RV_OUT_CLOSED": (154.5, 485.0), "RV_OUT_LEAKED": (185.8, 485.0),
    "RV_IN_CLOSED":  (154.5, 472.0), "RV_IN_LEAKED":  (185.8, 472.0),
    "CV2_CLOSED": (255.0, 518.0), "CV2_LEAKED": (255.0, 506.0), "CV2_NA": (255.0, 494.0),
    "PVB_AI_CLOSED": (367.9, 518.0), "PVB_AI_OPENED": (367.9, 506.0),
    "PVB_CV_LEAKED": (367.9, 483.0), "PVB_CV_HELD":   (367.9, 470.0),
    "PASSED": (414.0, 378.0), "FAILED": (490.0, 378.0),
    "REP_CVA":    (368.0, 340.0), "REP_FLUSH":  (511.0, 340.0),
    "REP_RVA":    (368.0, 326.0), "REP_CLEAN":  (511.0, 326.0),
    "REP_AIVA":   (368.0, 312.0), "REP_OSY":    (511.0, 312.0), "REP_REPACK": (545.0, 312.0),
    "REP_RUBBER": (368.0, 298.0), "REP_NEW":    (511.0, 298.0),
}

TEXT_FIELDS = {
    "date":          (83,  745, 8), "branch":        (222, 745, 8), "ahj":  (470, 745, 8),
    "customer_name": (170, 723, 8), "street_address": (170, 701, 8), "location": (170, 681, 8),
    "serial_number": (172, 647, 8), "size":  (432, 647, 8),
    "manufacturer":  (170, 626, 8), "model": (171, 606, 8),
    "cv1_dp":  (148, 441, 8), "rv_psi":  (240, 518, 7),
    "cv2_dp":  (418, 441, 8), "pvb_ai_psi": (510, 506, 7), "pvb_cv_psi": (510, 470, 7),
    "test_date": (175, 378, 8),
    "gauge_mfg":    (220, 216, 8), "gauge_serial": (342, 216, 8), "date_cal": (483, 216, 8),
    "technician":   (192, 197, 8), "cert_no": (388, 197, 8),   "recert":   (483, 197, 8),
}

STICKY = {"branch","ahj","gauge_mfg","gauge_serial","date_cal","technician","cert_no","recert"}

# ── PDF generation ──
def draw_x(c, bx, by, size=4.5):
    c.setStrokeColorRGB(0.05,0.05,0.05); c.setLineWidth(1.3)
    c.line(bx-size, by-size, bx+size, by+size)
    c.line(bx+size, by-size, bx-size, by+size)

def put_text(c, val, x, y, sz=8):
    if val:
        c.setFont("Helvetica", sz); c.setFillColorRGB(0,0,0)
        c.drawString(x, y, str(val))

def wrap_text(text, w=65):
    words = text.split(); lines, line = [], ""
    for word in words:
        test = (line+" "+word).strip()
        if len(test) > w: lines.append(line.strip()); line = word
        else: line = test
    if line: lines.append(line)
    return lines

def generate_pdf(form):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    for field, (x, y, sz) in TEXT_FIELDS.items():
        put_text(c, form.get(field,""), x, y, sz)
    asm = form.get("assembly_type","")
    for key in ["RP","DC","PVB","SVB"]:
        if asm == key: draw_x(c, *CHECKBOXES[key])
    for key in ["FIRE","DOMESTIC","IRRIGATION","ATTRACTION"]:
        if form.get("ss_"+key.lower()): draw_x(c, *CHECKBOXES[key])
    bp = form.get("bypass","")
    if bp=="YES": draw_x(c, *CHECKBOXES["BYPASS_YES"])
    if bp=="NO":  draw_x(c, *CHECKBOXES["BYPASS_NO"])
    for key in ["CV1_CLOSED","CV1_LEAKED","CV1_NA"]:
        if form.get(key.lower()): draw_x(c, *CHECKBOXES[key])
    for key in ["RV_OPENED","RV_DIDNOTOPEN","RV_NA","RV_OUT_CLOSED","RV_OUT_LEAKED","RV_IN_CLOSED","RV_IN_LEAKED"]:
        if form.get(key.lower()): draw_x(c, *CHECKBOXES[key])
    for key in ["CV2_CLOSED","CV2_LEAKED","CV2_NA"]:
        if form.get(key.lower()): draw_x(c, *CHECKBOXES[key])
    for key in ["PVB_AI_CLOSED","PVB_AI_OPENED","PVB_CV_LEAKED","PVB_CV_HELD"]:
        if form.get(key.lower()): draw_x(c, *CHECKBOXES[key])
    result = form.get("assembly_result","")
    if result=="PASSED": draw_x(c, *CHECKBOXES["PASSED"])
    if result=="FAILED": draw_x(c, *CHECKBOXES["FAILED"])
    REPAIR_MAP = [("rep_cva","REP_CVA"),("rep_flush","REP_FLUSH"),("rep_rva","REP_RVA"),
                  ("rep_clean","REP_CLEAN"),("rep_aiva","REP_AIVA"),("rep_osy","REP_OSY"),
                  ("rep_repack","REP_REPACK"),("rep_rubber","REP_RUBBER"),("rep_new","REP_NEW")]
    for fk,ck in REPAIR_MAP:
        if form.get(fk): draw_x(c, *CHECKBOXES[ck])
    for i, ln in enumerate(wrap_text(form.get("repair_desc",""), 55)[:2]):
        put_text(c, ln, 95, 358-i*11, 7)
    for i, ln in enumerate(wrap_text(form.get("remarks",""), 60)[:2]):
        put_text(c, ln, 95, 265-i*11, 7)
    c.save(); buf.seek(0)
    tp = PdfReader(TEMPLATE_PATH); op = PdfReader(buf)
    pg = tp.pages[0]; PageMerge(pg).add(op.pages[0]).render()
    if pg.Annots: pg.Annots = []
    out = BytesIO(); PdfWriter().write(out, tp); out.seek(0)
    return out

def safe_filename(customer, address):
    def clean(s): return re.sub(r"[^\w\s\-]", "", s).strip()
    c = clean(customer) or "Unknown"
    a = clean(address) or "NoAddress"
    return f"{c} - {a}.pdf"

# ── Session persistence ──
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            return json.load(f)
    return {}

def save_session(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)

# ── Streamlit UI ──
st.set_page_config(page_title="United Fire Backflow Report", page_icon="🔧", layout="wide")
st.title("🔧 United Fire — Backflow Preventer Test Report")

if not LIBS_OK:
    st.error("Missing libraries. Run: pip install pdfrw reportlab streamlit")
    st.stop()
if not os.path.exists(TEMPLATE_PATH):
    st.error(f"Template not found: {TEMPLATE_PATH}")
    st.stop()

if "form" not in st.session_state:
    saved = load_session()
    st.session_state.form = saved

f = st.session_state.form

col_save, col_load, col_clear = st.columns([1,1,1])
with col_save:
    if st.button("💾 Save Session"):
        save_session(f); st.success("Session saved!")
with col_load:
    if st.button("📂 Load Session"):
        st.session_state.form = load_session(); st.rerun()
with col_clear:
    if st.button("🗑️ Clear Form (keep tester info)"):
        sticky = {k:v for k,v in f.items() if k in STICKY}
        st.session_state.form = sticky; st.rerun()

st.divider()

# ── Header fields ──
st.subheader("Job Information")
c1,c2,c3 = st.columns([1,1,2])
f["date"]   = c1.text_input("Date", f.get("date", date.today().strftime("%m/%d/%Y")))
f["branch"] = c2.text_input("Branch ⭐", f.get("branch",""))
f["ahj"]    = c3.text_input("Authority Having Jurisdiction ⭐", f.get("ahj",""))
f["customer_name"]  = st.text_input("Customer / Site Name", f.get("customer_name",""))
f["street_address"] = st.text_input("Street Address", f.get("street_address",""))
f["location"]       = st.text_input("Location of Assembly", f.get("location",""))

st.divider()
st.subheader("Backflow Assembly Information")

c1,c2,c3,c4 = st.columns(4)
f["serial_number"] = c1.text_input("Serial Number", f.get("serial_number",""))
f["manufacturer"]  = c2.text_input("Manufacturer",  f.get("manufacturer",""))
f["model"]         = c3.text_input("Model",          f.get("model",""))
f["size"]          = c4.text_input("Size",           f.get("size",""))

c1,c2,c3 = st.columns(3)
f["assembly_type"] = c1.selectbox("Type of Assembly", ["","RP","DC","PVB","SVB"], 
    index=["","RP","DC","PVB","SVB"].index(f.get("assembly_type","")))
ss_options = ["FIRE","DOMESTIC","IRRIGATION","ATTRACTION"]
curr_ss = f.get("system_service","")
f["system_service"] = c2.selectbox("System Service", [""]+ss_options,
    index=([""]+ss_options).index(curr_ss) if curr_ss in [""]+ss_options else 0)
for k in ["ss_fire","ss_domestic","ss_irrigation","ss_attraction"]:
    f[k] = False
if f["system_service"]:
    f["ss_"+f["system_service"].lower()] = True
f["bypass"] = c3.selectbox("Bypass?", ["","YES","NO"],
    index=["","YES","NO"].index(f.get("bypass","")))

st.divider()
st.subheader("Testing Information")

# CV1 | RV | CV2 | PVB/SVB
tc1, tc2, tc3, tc4 = st.columns(4)

with tc1:
    st.markdown("**Check Valve #1**")
    f["cv1_closed"] = st.checkbox("Closed Tight",   f.get("cv1_closed",False), key="k_cv1_c")
    f["cv1_leaked"] = st.checkbox("Leaked",          f.get("cv1_leaked",False), key="k_cv1_l")
    f["cv1_na"]     = st.checkbox("N/A",             f.get("cv1_na",False),     key="k_cv1_n")
    f["cv1_dp"]     = st.text_input("DP (PSI)",      f.get("cv1_dp",""),        key="k_cv1_dp")

with tc2:
    st.markdown("**Relief Valve**")
    f["rv_opened"]     = st.checkbox("Opened At",    f.get("rv_opened",False),    key="k_rv_o")
    f["rv_psi"]        = st.text_input("PSI",         f.get("rv_psi",""),          key="k_rv_psi")
    f["rv_didnotopen"] = st.checkbox("Did Not Open",  f.get("rv_didnotopen",False),key="k_rv_dno")
    f["rv_na"]         = st.checkbox("N/A",           f.get("rv_na",False),        key="k_rv_na")
    st.markdown("*Outlet Shut-Off Valve*")
    f["rv_out_closed"] = st.checkbox("Closed",        f.get("rv_out_closed",False),key="k_rv_oc")
    f["rv_out_leaked"] = st.checkbox("Leaked",        f.get("rv_out_leaked",False),key="k_rv_ol")
    st.markdown("*Inlet Shut-Off Valve*")
    f["rv_in_closed"]  = st.checkbox("Closed",        f.get("rv_in_closed",False), key="k_rv_ic")
    f["rv_in_leaked"]  = st.checkbox("Leaked",        f.get("rv_in_leaked",False), key="k_rv_il")

with tc3:
    st.markdown("**Check Valve #2**")
    f["cv2_closed"] = st.checkbox("Closed Tight",   f.get("cv2_closed",False), key="k_cv2_c")
    f["cv2_leaked"] = st.checkbox("Leaked",          f.get("cv2_leaked",False), key="k_cv2_l")
    f["cv2_na"]     = st.checkbox("N/A",             f.get("cv2_na",False),     key="k_cv2_n")
    f["cv2_dp"]     = st.text_input("DP (PSI)",      f.get("cv2_dp",""),        key="k_cv2_dp")

with tc4:
    st.markdown("**PVB / SVB**")
    st.markdown("*Air Inlet*")
    f["pvb_ai_closed"] = st.checkbox("Closed Tight", f.get("pvb_ai_closed",False),key="k_pvb_aic")
    f["pvb_ai_opened"] = st.checkbox("Opened At",    f.get("pvb_ai_opened",False),key="k_pvb_aio")
    f["pvb_ai_psi"]    = st.text_input("PSI",         f.get("pvb_ai_psi",""),      key="k_pvb_psi")
    st.markdown("*Check Valve*")
    f["pvb_cv_leaked"] = st.checkbox("Leaked",        f.get("pvb_cv_leaked",False),key="k_pvb_cvl")
    f["pvb_cv_held"]   = st.checkbox("Held At (PSI)", f.get("pvb_cv_held",False),  key="k_pvb_cvh")
    f["pvb_cv_psi"]    = st.text_input("PSI ",        f.get("pvb_cv_psi",""),       key="k_pvb_cpsi")

c1,c2 = st.columns(2)
f["test_date"] = c1.text_input("Test Date", f.get("test_date", date.today().strftime("%m/%d/%Y")))
result = c2.radio("This Assembly:", ["","PASSED","FAILED"], 
    index=["","PASSED","FAILED"].index(f.get("assembly_result","")),
    horizontal=True)
f["assembly_result"] = result

st.divider()
st.subheader("Repairs")

f["repair_desc"] = st.text_area("Description of Repairs (including part #)", f.get("repair_desc",""), height=80)

rc1, rc2 = st.columns(2)
with rc1:
    f["rep_cva"]    = st.checkbox("Check Valve Assembly",      f.get("rep_cva",False))
    f["rep_rva"]    = st.checkbox("Relief Valve Assembly",     f.get("rep_rva",False))
    f["rep_aiva"]   = st.checkbox("Air Inlet Valve Assembly",  f.get("rep_aiva",False))
    f["rep_rubber"] = st.checkbox("Rubber Repair Kit",         f.get("rep_rubber",False))
with rc2:
    f["rep_flush"]  = st.checkbox("Flush & Remove Debris",     f.get("rep_flush",False))
    f["rep_clean"]  = st.checkbox("Clean Internal",            f.get("rep_clean",False))
    f["rep_osy"]    = st.checkbox("OS&Y Repair",               f.get("rep_osy",False))
    f["rep_repack"] = st.checkbox("Re-Packing",                f.get("rep_repack",False))
    f["rep_new"]    = st.checkbox("New Backflow",              f.get("rep_new",False))

f["remarks"] = st.text_area("Remarks / Repairs Needed", f.get("remarks",""), height=60)

st.divider()
st.subheader("Tester Information ⭐ (auto-saved)")
t1,t2,t3 = st.columns(3)
f["gauge_mfg"]    = t1.text_input("Gauge Manufacturer ⭐", f.get("gauge_mfg",""))
f["gauge_serial"] = t2.text_input("Gauge Serial # ⭐",     f.get("gauge_serial",""))
f["date_cal"]     = t3.text_input("Date Calibrated ⭐",    f.get("date_cal",""))
t1b,t2b,t3b = st.columns(3)
f["technician"] = t1b.text_input("Technician ⭐", f.get("technician",""))
f["cert_no"]    = t2b.text_input("Certification No. ⭐", f.get("cert_no",""))
f["recert"]     = t3b.text_input("Re-Cert Due Date ⭐",  f.get("recert",""))

st.divider()
st.caption("⭐ = sticky fields preserved on Clear Form")

if st.button("📄 Generate & Download PDF", type="primary", use_container_width=True):
    with st.spinner("Generating PDF..."):
        try:
            pdf_bytes = generate_pdf(f)
            fname = safe_filename(f.get("customer_name","Customer"), f.get("street_address","Address"))
            st.download_button(
                label=f"⬇️ Download: {fname}",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True
            )
            sticky_data = {k:v for k,v in f.items() if k in STICKY}
            save_session({**f})
            st.success(f"✅ PDF ready: {fname}")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
