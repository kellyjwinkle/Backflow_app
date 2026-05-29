import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
import json, os, re
from datetime import date
from pdfrw import PdfReader, PdfWriter, PageMerge

TEMPLATE_PATH = "backflow_template.pdf"
SESSION_FILE  = "session_data.json"
PAGE_W, PAGE_H = 612, 792

# Fields marked with ⭐ persist across "Clear Form"
STICKY = {'branch','ahj','manufacturer','model','size',
          'gauge_mfg','gauge_serial','date_cal','technician','cert_no','recert'}

# All X-mark centers (x, y) calibrated to 612x792 real scan template
CHECKBOXES = {
    'RP':  (208.0, 485.1), 'DC':  (288.0, 483.4),
    'PVB': (208.0, 460.1), 'SVB': (288.0, 456.4),
    'FIRE':       (415.4, 491.9), 'DOMESTIC':   (414.4, 476.9),
    'IRRIGATION': (413.4, 464.6), 'ATTRACTION': (412.3, 452.6),
    'BYPASS_YES': (510.0, 476.9), 'BYPASS_NO':  (510.0, 462.0),
    'CV1_CLOSED': (112.0, 384.3), 'CV1_LEAKED': (112.0, 371.4), 'CV1_NA': (112.0, 359.3),
    'CV2_CLOSED': (414.3, 386.0), 'CV2_LEAKED': (394.1, 364.8), 'CV2_NA': (394.1, 352.0),
    'PVB_AI_CLOSED': (540.0, 407.0), 'PVB_AI_OPENED': (465.0, 351.5),
    'PVB_CV_LEAKED': (518.0, 319.4), 'PVB_CV_HELD':   (465.0, 285.6),
    'RV_OPENED':     (207.0, 396.4), 'RV_DIDNOTOPEN': (207.0, 371.4), 'RV_NA': (248.0, 371.4),
    'RV_OUT_CLOSED': (207.0, 316.8), 'RV_OUT_LEAKED': (248.0, 316.8),
    'RV_IN_CLOSED':  (207.0, 283.1), 'RV_IN_LEAKED':  (248.0, 283.1),
    'PASSED': (385.8, 259.3), 'FAILED': (462.0, 259.3),
    'REP_CVA':    (363.0, 267.1), 'REP_FLUSH':  (453.0, 267.1),
    'REP_RVA':    (363.0, 256.1), 'REP_CLEAN':  (453.0, 256.1),
    'REP_AIVA':   (363.0, 245.1), 'REP_OSY':    (453.0, 245.1),
    'REP_REPACK': (497.0, 245.1),
    'REP_RUBBER': (363.0, 234.1), 'REP_NEW':    (453.0, 234.1),
}

# Text insertion points (x, y, fontsize) — calibrated to real scan
TEXT_FIELDS = {
    'date':           (100, 585.4, 8),
    'branch':         (222, 585.4, 8),
    'ahj':            (430, 585.4, 8),
    'customer_name':  (200, 568.1, 8),
    'street_address': (175, 550.8, 8),
    'location':       (175, 535.1, 8),
    'serial_number':  (172, 508.4, 8),
    'manufacturer':   (172, 486.0, 8),
    'model':          (171, 470.0, 8),
    'size':           (432, 508.4, 8),
    'rv_psi':         (255, 396.4, 7),
    'cv1_dp':         (148, 346.5, 8),
    'cv2_dp':         (418, 346.5, 8),
    'pvb_ai_psi':     (497, 348.1, 7),
    'pvb_cv_psi':     (482, 282.1, 7),
    'test_date':      (100, 291.0, 8),
    'gauge_mfg':      (220, 174.0, 8),
    'gauge_serial':   (342, 174.0, 8),
    'date_cal':       (475, 174.0, 8),
    'technician':     (110, 158.0, 8),
    'cert_no':        (388, 158.0, 8),
    'recert':         (388, 145.0, 8),
}

def draw_x(c, bx, by, size=3.8):
    c.setStrokeColorRGB(0.05,0.05,0.05)
    c.setLineWidth(1.2)
    c.line(bx-size, by-size, bx+size, by+size)
    c.line(bx+size, by-size, bx-size, by+size)

def put_text(c, val, x, y, sz=8):
    if val:
        c.setFont("Helvetica", sz)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x, y, str(val))

def wrap_text(text, w=42):
    words = text.split(); lines, line = [], ""
    for word in words:
        t = (line + " " + word).strip()
        if len(t) > w: lines.append(line.strip()); line = word
        else: line = t
    if line: lines.append(line)
    return lines

def generate_pdf(form):
    if not os.path.exists(TEMPLATE_PATH):
        st.error(f"Template not found: place **backflow_template.pdf** in the same folder as app.py")
        st.stop()
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    # Text fields
    for field, (x, y, sz) in TEXT_FIELDS.items():
        put_text(c, form.get(field, ''), x, y, sz)

    # Assembly type
    asm = form.get('assembly_type', '')
    for key in ['RP', 'DC', 'PVB', 'SVB']:
        if asm == key: draw_x(c, *CHECKBOXES[key])

    # System service
    for key in ['FIRE', 'DOMESTIC', 'IRRIGATION', 'ATTRACTION']:
        if form.get('ss_' + key.lower()): draw_x(c, *CHECKBOXES[key])

    # Bypass
    bp = form.get('bypass', '')
    if bp == 'YES': draw_x(c, *CHECKBOXES['BYPASS_YES'])
    if bp == 'NO':  draw_x(c, *CHECKBOXES['BYPASS_NO'])

    # All checkbox groups
    for key in ['CV1_CLOSED','CV1_LEAKED','CV1_NA',
                'CV2_CLOSED','CV2_LEAKED','CV2_NA',
                'PVB_AI_CLOSED','PVB_AI_OPENED','PVB_CV_LEAKED','PVB_CV_HELD',
                'RV_OPENED','RV_DIDNOTOPEN','RV_NA',
                'RV_OUT_CLOSED','RV_OUT_LEAKED',
                'RV_IN_CLOSED','RV_IN_LEAKED']:
        if form.get(key.lower()): draw_x(c, *CHECKBOXES[key])

    # Result
    result = form.get('assembly_result', '')
    if result == 'PASSED': draw_x(c, *CHECKBOXES['PASSED'])
    if result == 'FAILED': draw_x(c, *CHECKBOXES['FAILED'])

    # Repair checkboxes
    for fk, ck in [
        ('rep_cva','REP_CVA'),('rep_flush','REP_FLUSH'),
        ('rep_rva','REP_RVA'),('rep_clean','REP_CLEAN'),
        ('rep_aiva','REP_AIVA'),('rep_osy','REP_OSY'),
        ('rep_repack','REP_REPACK'),
        ('rep_rubber','REP_RUBBER'),('rep_new','REP_NEW')
    ]:
        if form.get(fk): draw_x(c, *CHECKBOXES[ck])

    # Repair description text (in the left box under "DESCRIPTION")
    for i, ln in enumerate(wrap_text(form.get('repair_desc', ''), 42)[:4]):
        put_text(c, ln, 95, 254 - i*10, 7)

    # Remarks
    for i, ln in enumerate(wrap_text(form.get('remarks', ''), 55)[:2]):
        put_text(c, ln, 95, 204 - i*10, 7)

    c.save(); buf.seek(0)

    tp = PdfReader(TEMPLATE_PATH)
    op = PdfReader(buf)
    pg = tp.pages[0]
    PageMerge(pg).add(op.pages[0]).render()
    if pg.Annots: pg.Annots = []
    out = BytesIO()
    PdfWriter().write(out, tp)
    out.seek(0)
    return out

def safe_filename(customer, address):
    def clean(s): return re.sub(r'[^\w\s\-]', '', s).strip()
    return f"{clean(customer) or 'Customer'} - {clean(address) or 'Address'}.pdf"

def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE) as f: return json.load(f)
        except: pass
    return {}

def save_session(data):
    with open(SESSION_FILE, 'w') as f: json.dump(data, f)

# ──────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────
st.set_page_config(page_title="United Fire — Backflow Report", page_icon="🔧", layout="wide")
st.title("🔧 United Fire — Backflow Preventer Test Report")

if "form" not in st.session_state:
    st.session_state.form = load_session()

f = st.session_state.form

# ── Action buttons ──
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("💾 Save Session"):
        save_session(f); st.success("Session saved!")
with b2:
    if st.button("📂 Load Session"):
        st.session_state.form = load_session(); st.rerun()
with b3:
    if st.button("🗑️ Clear Form (keep ⭐ fields)"):
        st.session_state.form = {k:v for k,v in f.items() if k in STICKY}; st.rerun()

st.divider()

# ── Section 1: Header ──
st.subheader("📋 Job Information")
c1, c2, c3 = st.columns([1, 1, 2])
f["date"]   = c1.text_input("Date",   f.get("date", date.today().strftime("%m/%d/%Y")))
f["branch"] = c2.text_input("Branch ⭐", f.get("branch", ""))
f["ahj"]    = c3.text_input("Authority Having Jurisdiction ⭐", f.get("ahj", ""))
f["customer_name"]  = st.text_input("Customer / Site Name",  f.get("customer_name", ""))
f["street_address"] = st.text_input("Street Address",         f.get("street_address", ""))
f["location"]       = st.text_input("Location of Assembly",   f.get("location", ""))

st.divider()

# ── Section 2: Assembly ──
st.subheader("🔩 Backflow Assembly Information")
c1, c2, c3, c4 = st.columns(4)
f["serial_number"] = c1.text_input("Serial Number",      f.get("serial_number", ""))
f["manufacturer"]  = c2.text_input("Manufacturer ⭐",   f.get("manufacturer", ""))
f["model"]         = c3.text_input("Model ⭐",            f.get("model", ""))
f["size"]          = c4.text_input("Size ⭐",             f.get("size", ""))

c1, c2, c3 = st.columns(3)
asm_opts = ["", "RP", "DC", "PVB", "SVB"]
f["assembly_type"] = c1.selectbox("Type of Assembly",
    asm_opts, index=asm_opts.index(f.get("assembly_type","")) if f.get("assembly_type","") in asm_opts else 0)

ss_opts = ["", "FIRE", "DOMESTIC", "IRRIGATION", "ATTRACTION"]
curr_ss = f.get("system_service", "")
f["system_service"] = c2.selectbox("System Service",
    ss_opts, index=ss_opts.index(curr_ss) if curr_ss in ss_opts else 0)
for k in ["ss_fire","ss_domestic","ss_irrigation","ss_attraction"]: f[k] = False
if f["system_service"]: f["ss_" + f["system_service"].lower()] = True

bp_opts = ["", "YES", "NO"]
f["bypass"] = c3.selectbox("Bypass?",
    bp_opts, index=bp_opts.index(f.get("bypass","")) if f.get("bypass","") in bp_opts else 0)

st.divider()

# ── Section 3: Testing ──
st.subheader("🧪 Testing Information")
tc1, tc2, tc3, tc4 = st.columns(4)

with tc1:
    st.markdown("**Check Valve #1**")
    f["cv1_closed"] = st.checkbox("Closed Tight",  f.get("cv1_closed", False), key="cv1c")
    f["cv1_leaked"] = st.checkbox("Leaked",        f.get("cv1_leaked", False), key="cv1l")
    f["cv1_na"]     = st.checkbox("N/A",            f.get("cv1_na",    False), key="cv1n")
    f["cv1_dp"]     = st.text_input("DP Across CV1 (PSI)", f.get("cv1_dp",""), key="cv1dp")

with tc2:
    st.markdown("**Relief Valve**")
    f["rv_opened"]     = st.checkbox("Opened At",    f.get("rv_opened",     False), key="rvo")
    f["rv_psi"]        = st.text_input("PSI",         f.get("rv_psi",""),           key="rvpsi")
    f["rv_didnotopen"] = st.checkbox("Did Not Open", f.get("rv_didnotopen", False), key="rvdno")
    f["rv_na"]         = st.checkbox("N/A",           f.get("rv_na",        False), key="rvna")
    st.markdown("*Outlet Shut-Off Valve*")
    f["rv_out_closed"] = st.checkbox("Closed",  f.get("rv_out_closed", False), key="rvoc")
    f["rv_out_leaked"] = st.checkbox("Leaked",  f.get("rv_out_leaked", False), key="rvol")
    st.markdown("*Inlet Shut-Off Valve*")
    f["rv_in_closed"]  = st.checkbox("Closed",  f.get("rv_in_closed",  False), key="rvic")
    f["rv_in_leaked"]  = st.checkbox("Leaked",  f.get("rv_in_leaked",  False), key="rvil")

with tc3:
    st.markdown("**Check Valve #2**")
    f["cv2_closed"] = st.checkbox("Closed Tight", f.get("cv2_closed", False), key="cv2c")
    f["cv2_leaked"] = st.checkbox("Leaked",       f.get("cv2_leaked", False), key="cv2l")
    f["cv2_na"]     = st.checkbox("N/A",           f.get("cv2_na",    False), key="cv2n")
    f["cv2_dp"]     = st.text_input("DP Across CV2 (PSI)", f.get("cv2_dp",""), key="cv2dp")

with tc4:
    st.markdown("**PVB / SVB**")
    st.markdown("*Air Inlet*")
    f["pvb_ai_closed"] = st.checkbox("Closed Tight", f.get("pvb_ai_closed", False), key="pvbaic")
    f["pvb_ai_opened"] = st.checkbox("Opened At",    f.get("pvb_ai_opened", False), key="pvbaio")
    f["pvb_ai_psi"]    = st.text_input("PSI",          f.get("pvb_ai_psi", ""),      key="pvbaipsi")
    st.markdown("*Check Valve*")
    f["pvb_cv_leaked"] = st.checkbox("Leaked",   f.get("pvb_cv_leaked", False), key="pvbcvl")
    f["pvb_cv_held"]   = st.checkbox("Held At",  f.get("pvb_cv_held",   False), key="pvbcvh")
    f["pvb_cv_psi"]    = st.text_input("PSI",     f.get("pvb_cv_psi",   ""),    key="pvbcvpsi")

c1, c2 = st.columns(2)
f["test_date"] = c1.text_input("Test Date", f.get("test_date", date.today().strftime("%m/%d/%Y")))
res_opts = ["", "PASSED", "FAILED"]
f["assembly_result"] = c2.radio("This Assembly:",
    res_opts,
    index=res_opts.index(f.get("assembly_result","")) if f.get("assembly_result","") in res_opts else 0,
    horizontal=True)

st.divider()

# ── Section 4: Repairs ──
st.subheader("🔧 Repairs")
f["repair_desc"] = st.text_area("Description of Repairs (including Part #)",
    f.get("repair_desc", ""), height=80)

rc1, rc2 = st.columns(2)
with rc1:
    f["rep_cva"]    = st.checkbox("Check Valve Assembly",     f.get("rep_cva",    False))
    f["rep_rva"]    = st.checkbox("Relief Valve Assembly",    f.get("rep_rva",    False))
    f["rep_aiva"]   = st.checkbox("Air Inlet Valve Assembly", f.get("rep_aiva",   False))
    f["rep_rubber"] = st.checkbox("Rubber Repair Kit",        f.get("rep_rubber", False))
with rc2:
    f["rep_flush"]  = st.checkbox("Flush & Remove Debris",    f.get("rep_flush",  False))
    f["rep_clean"]  = st.checkbox("Clean Internal",           f.get("rep_clean",  False))
    f["rep_osy"]    = st.checkbox("OS&Y Repair",              f.get("rep_osy",    False))
    f["rep_repack"] = st.checkbox("Re-Packing",               f.get("rep_repack", False))
    f["rep_new"]    = st.checkbox("New Backflow",             f.get("rep_new",    False))

f["remarks"] = st.text_area("Remarks / Repairs Needed", f.get("remarks", ""), height=60)

st.divider()

# ── Section 5: Tester ──
st.subheader("🧰 Tester Information ⭐")
st.caption("These fields persist when you Clear Form.")
t1, t2, t3 = st.columns(3)
f["gauge_mfg"]    = t1.text_input("Gauge Manufacturer ⭐", f.get("gauge_mfg",""))
f["gauge_serial"] = t2.text_input("Gauge Serial # ⭐",     f.get("gauge_serial",""))
f["date_cal"]     = t3.text_input("Date Calibrated ⭐",    f.get("date_cal",""))
t1b, t2b, t3b = st.columns(3)
f["technician"] = t1b.text_input("Technician ⭐",         f.get("technician",""))
f["cert_no"]    = t2b.text_input("Certification No. ⭐",  f.get("cert_no",""))
f["recert"]     = t3b.text_input("Re-Cert Due Date ⭐",   f.get("recert",""))

st.divider()

# ── Generate PDF ──
if st.button("📄 Generate & Download PDF", type="primary", use_container_width=True):
    with st.spinner("Building PDF..."):
        try:
            pdf_bytes = generate_pdf(f)
            fname = safe_filename(f.get("customer_name","Customer"), f.get("street_address","Address"))
            st.download_button(
                f"⬇️ Download: {fname}",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True
            )
            save_session(f)
            st.success(f"✅ Ready: {fname}")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
