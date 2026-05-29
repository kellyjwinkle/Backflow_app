import streamlit as st
import json, os
from io import BytesIO
from datetime import date
from pdfrw import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from pdfrw import PageMerge

st.set_page_config(page_title="United Fire – Backflow Report", layout="centered", page_icon="🔥")

TEMPLATE     = "backflow_template.pdf"
SESSION_FILE = "session_data.json"
PAGE_W, PAGE_H = 612, 1008

def load_saved():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            return json.load(f)
    return {}

def save_session(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)

def draw_x(c, px, py, size=4.5):
    c.setStrokeColorRGB(0.05, 0.05, 0.05)
    c.setLineWidth(1.3)
    c.line(px-size, py-size, px+size, py+size)
    c.line(px+size, py-size, px-size, py+size)

def txt(c, value, px, py, size=8):
    if value:
        c.setFont("Helvetica", size)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(px, py, str(value))

def wrap(text, width):
    words = text.split(); lines, line = [], ""
    for w in words:
        if len(line + " " + w) > width: lines.append(line.strip()); line = w
        else: line = (line + " " + w)
    if line.strip(): lines.append(line.strip())
    return lines

def generate_pdf(form):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    txt(c, form.get("date"),   83,  745)
    txt(c, form.get("branch"), 222, 745)
    txt(c, form.get("ahj"),    460, 745)
    txt(c, form.get("customer_name"),  170, 723)
    txt(c, form.get("street_address"), 170, 701)
    txt(c, form.get("location"),       170, 681)
    txt(c, form.get("serial_number"), 172, 647)
    txt(c, form.get("size"),          432, 647)
    txt(c, form.get("manufacturer"),  170, 626)
    txt(c, form.get("model"),         171, 606)

    asm = form.get("assembly_type","")
    if asm=="RP":  draw_x(c,220,579)
    if asm=="DC":  draw_x(c,292,579)
    if asm=="PVB": draw_x(c,220,562)
    if asm=="SVB": draw_x(c,292,562)

    if form.get("ss_fire"):       draw_x(c,443,596)
    if form.get("ss_domestic"):   draw_x(c,443,580)
    if form.get("ss_irrigation"): draw_x(c,443,566)
    if form.get("ss_attraction"): draw_x(c,443,551)
    if form.get("bypass")=="YES": draw_x(c,568,577)
    if form.get("bypass")=="NO":  draw_x(c,568,563)

    if form.get("cv1_closed"): draw_x(c,83,519)
    if form.get("cv1_leaked"): draw_x(c,83,504)
    if form.get("cv1_na"):     draw_x(c,83,490)
    txt(c, form.get("cv1_dp"), 152, 477)

    if form.get("rv_opened"):     draw_x(c,210,519)
    txt(c, form.get("rv_psi"),    232, 519)
    if form.get("rv_didnotopen"): draw_x(c,210,504)
    if form.get("rv_na"):         draw_x(c,275,504)
    if form.get("rv_out_closed"): draw_x(c,210,484)
    if form.get("rv_out_leaked"): draw_x(c,260,484)
    if form.get("rv_in_closed"):  draw_x(c,210,468)
    if form.get("rv_in_leaked"):  draw_x(c,260,468)

    if form.get("cv2_closed"): draw_x(c,342,519)
    if form.get("cv2_leaked"): draw_x(c,342,504)
    if form.get("cv2_na"):     draw_x(c,342,490)
    txt(c, form.get("cv2_dp"), 354, 456)

    if form.get("pvb_ai_closed"):  draw_x(c,497,519)
    if form.get("pvb_ai_opened"):  draw_x(c,497,503)
    txt(c, form.get("pvb_ai_psi"), 523, 503)
    if form.get("pvb_cv_leaked"):  draw_x(c,497,482)
    if form.get("pvb_cv_held"):    draw_x(c,497,466)
    txt(c, form.get("pvb_cv_psi"), 523, 466)

    txt(c, form.get("test_date"), 175, 374)
    result = form.get("assembly_result","")
    if result=="PASSED": draw_x(c,413,374,5.5)
    if result=="FAILED": draw_x(c,488,374,5.5)

    if form.get("rep_cva"):    draw_x(c,373,320)
    if form.get("rep_flush"):  draw_x(c,510,320)
    if form.get("rep_rva"):    draw_x(c,373,304)
    if form.get("rep_clean"):  draw_x(c,510,304)
    if form.get("rep_aiva"):   draw_x(c,373,288)
    if form.get("rep_osy"):    draw_x(c,510,288)
    if form.get("rep_repack"): draw_x(c,551,288)
    if form.get("rep_rubber"): draw_x(c,373,272)
    if form.get("rep_new"):    draw_x(c,510,272)

    rdesc = form.get("repair_desc","")
    if rdesc:
        for i, ln in enumerate(wrap(rdesc,70)[:2]):
            txt(c, ln, 95, 340-i*12, 7)

    remarks = form.get("remarks","")
    if remarks:
        for i, ln in enumerate(wrap(remarks,75)[:2]):
            txt(c, ln, 95, 254-i*12, 7)

    txt(c, form.get("gauge_mfg"),    220, 216)
    txt(c, form.get("gauge_serial"), 342, 216)
    txt(c, form.get("date_cal"),     483, 216)
    txt(c, form.get("cert_no"),      388, 197)
    txt(c, form.get("technician"),   192, 197)
    txt(c, form.get("recert"),       483, 197)

    c.save(); buf.seek(0)
    template_pdf = PdfReader(TEMPLATE)
    overlay_pdf  = PdfReader(buf)
    page = template_pdf.pages[0]
    PageMerge(page).add(overlay_pdf.pages[0]).render()
    if page.Annots: page.Annots = []
    out = BytesIO()
    PdfWriter().write(out, template_pdf)
    out.seek(0)
    return out

saved = load_saved()
if "form" not in st.session_state:    st.session_state.form   = saved.copy() if saved else {}
if "locked" not in st.session_state:  st.session_state.locked = False
form  = st.session_state.form
today = str(date.today())
if not form.get("date"):      form["date"]      = today
if not form.get("test_date"): form["test_date"] = today
STICKY = ["branch","ahj","gauge_mfg","gauge_serial","date_cal","cert_no","technician","recert"]

def reset_form():
    kept = {k: form.get(k,"") for k in STICKY}
    kept["date"] = today; kept["test_date"] = today
    st.session_state.form = kept

st.markdown("""<div style="background:linear-gradient(135deg,#c0392b,#7f1d1d);padding:14px 20px;border-radius:8px;margin-bottom:18px">
  <h2 style="color:white;margin:0;font-size:1.3rem">&#128293; United Fire &ndash; Backflow Test Report</h2>
  <p style="color:#fca5a5;margin:3px 0 0;font-size:.8rem">Backflow Preventer Assembly Test &amp; Maintenance Report</p>
</div>""", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
if c1.button("🔒 Lock Site"):   st.session_state.locked=True;  st.toast("Site info locked",icon="🔒")
if c2.button("🔓 Unlock"):      st.session_state.locked=False; st.toast("Unlocked",icon="🔓")
if c3.button("💾 Save Session"): save_session(form);            st.toast("Session saved!",icon="✅")
if c4.button("🗑️ Clear Form"):  reset_form();                  st.rerun()

st.divider()
st.subheader("📋 Report Header")
co1,co2,co3 = st.columns(3)
form["date"]   = co1.text_input("Date",   form.get("date",today))
form["branch"] = co2.text_input("Branch", form.get("branch",""), disabled=st.session_state.locked)
form["ahj"]    = co3.text_input("Authority Having Jurisdiction", form.get("ahj",""), disabled=st.session_state.locked)
co1,co2 = st.columns(2)
form["customer_name"]  = co1.text_input("Customer / Site Name", form.get("customer_name",""), disabled=st.session_state.locked)
form["street_address"] = co2.text_input("Street Address",       form.get("street_address",""), disabled=st.session_state.locked)
form["location"] = st.text_input("Location of Assembly", form.get("location",""))

st.divider()
st.subheader("🔧 Backflow Information")
co1,co2,co3,co4 = st.columns(4)
form["serial_number"] = co1.text_input("Serial Number", form.get("serial_number",""))
form["manufacturer"]  = co2.text_input("Manufacturer",  form.get("manufacturer",""), disabled=st.session_state.locked)
form["model"]         = co3.text_input("Model",         form.get("model",""),         disabled=st.session_state.locked)
form["size"]          = co4.text_input("Size",          form.get("size",""),          disabled=st.session_state.locked)
co1,co2,co3 = st.columns(3)
form["assembly_type"] = co1.selectbox("Type of Assembly",["","RP","DC","PVB","SVB"],
    index=["","RP","DC","PVB","SVB"].index(form.get("assembly_type","")) if form.get("assembly_type","") in ["","RP","DC","PVB","SVB"] else 0)
with co2:
    st.markdown("**System Service**")
    form["ss_fire"]       = st.checkbox("Fire",       form.get("ss_fire",False))
    form["ss_domestic"]   = st.checkbox("Domestic",   form.get("ss_domestic",False))
    form["ss_irrigation"] = st.checkbox("Irrigation", form.get("ss_irrigation",False))
    form["ss_attraction"] = st.checkbox("Attraction", form.get("ss_attraction",False))
with co3:
    st.markdown("**Bypass?**")
    bp=["","YES","NO"]
    form["bypass"]=st.radio("Bypass",bp,index=bp.index(form.get("bypass","")) if form.get("bypass","") in bp else 0,label_visibility="collapsed")

st.divider()
st.subheader("🧪 Testing Information")
co1,co2,co3,co4 = st.columns(4)

with co1:
    st.markdown("**Check Valve #1**")
    qa,qb=st.columns(2)
    if qa.button("✅ PASS",key="cv1p",use_container_width=True): form["cv1_closed"]=True;  form["cv1_leaked"]=False; form["cv1_na"]=False
    if qb.button("❌ FAIL",key="cv1f",use_container_width=True): form["cv1_closed"]=False; form["cv1_leaked"]=True;  form["cv1_na"]=False
    form["cv1_closed"]=st.checkbox("Closed Tight",form.get("cv1_closed",False),key="ck_cv1ct")
    form["cv1_leaked"]=st.checkbox("Leaked",       form.get("cv1_leaked",False),key="ck_cv1lk")
    form["cv1_na"]    =st.checkbox("N/A",          form.get("cv1_na",False),    key="ck_cv1na")
    form["cv1_dp"]    =st.text_input("DP Across CV1 (PSI)",form.get("cv1_dp",""),key="ti_cv1dp")

with co2:
    st.markdown("**Relief Valve**")
    ra,rb=st.columns(2)
    if ra.button("✅ PASS",key="rvp",use_container_width=True): form["rv_opened"]=True;  form["rv_didnotopen"]=False; form["rv_na"]=False
    if rb.button("❌ FAIL",key="rvf",use_container_width=True): form["rv_opened"]=False; form["rv_didnotopen"]=True
    form["rv_opened"]     =st.checkbox("Opened At",   form.get("rv_opened",False),    key="ck_rvo")
    form["rv_psi"]        =st.text_input("Opened At PSI",form.get("rv_psi",""),       key="ti_rvpsi")
    form["rv_didnotopen"] =st.checkbox("Did Not Open",form.get("rv_didnotopen",False), key="ck_rvdn")
    form["rv_na"]         =st.checkbox("N/A",          form.get("rv_na",False),        key="ck_rvna")
    st.caption("Outlet S/O Valve")
    form["rv_out_closed"] =st.checkbox("Closed",form.get("rv_out_closed",False),key="ck_rvoc")
    form["rv_out_leaked"] =st.checkbox("Leaked",form.get("rv_out_leaked",False),key="ck_rvol")
    st.caption("Inlet S/O Valve")
    form["rv_in_closed"]  =st.checkbox("Closed",form.get("rv_in_closed",False),key="ck_rvic")
    form["rv_in_leaked"]  =st.checkbox("Leaked",form.get("rv_in_leaked",False),key="ck_rvil")

with co3:
    st.markdown("**Check Valve #2**")
    ca,cb2=st.columns(2)
    if ca.button("✅ PASS",key="cv2p",use_container_width=True): form["cv2_closed"]=True;  form["cv2_leaked"]=False; form["cv2_na"]=False
    if cb2.button("❌ FAIL",key="cv2f",use_container_width=True): form["cv2_closed"]=False; form["cv2_leaked"]=True;  form["cv2_na"]=False
    form["cv2_closed"]=st.checkbox("Closed Tight",form.get("cv2_closed",False),key="ck_cv2ct")
    form["cv2_leaked"]=st.checkbox("Leaked",       form.get("cv2_leaked",False),key="ck_cv2lk")
    form["cv2_na"]    =st.checkbox("N/A",          form.get("cv2_na",False),    key="ck_cv2na")
    form["cv2_dp"]    =st.text_input("Opt. DP Across CV2 (PSI)",form.get("cv2_dp",""),key="ti_cv2dp")

with co4:
    st.markdown("**PVB or SVB**")
    pa,pb=st.columns(2)
    if pa.button("✅ PASS",key="pvbp",use_container_width=True): form["pvb_ai_closed"]=True;  form["pvb_cv_leaked"]=False
    if pb.button("❌ FAIL",key="pvbf",use_container_width=True): form["pvb_ai_closed"]=False; form["pvb_cv_leaked"]=True
    st.caption("Air Inlet")
    form["pvb_ai_closed"]=st.checkbox("Closed Tight",form.get("pvb_ai_closed",False))
    form["pvb_ai_opened"]=st.checkbox("Opened At",   form.get("pvb_ai_opened",False))
    form["pvb_ai_psi"]   =st.text_input("Air Inlet PSI",form.get("pvb_ai_psi",""))
    st.caption("Check Valve")
    form["pvb_cv_leaked"]=st.checkbox("Leaked",  form.get("pvb_cv_leaked",False))
    form["pvb_cv_held"]  =st.checkbox("Held At", form.get("pvb_cv_held",False))
    form["pvb_cv_psi"]   =st.text_input("Held At PSI",form.get("pvb_cv_psi",""))

st.divider()
co1,co2=st.columns(2)
form["test_date"]=co1.text_input("Test Date",form.get("test_date",today))
with co2:
    st.markdown("**This Assembly:**")
    r1,r2,r3=st.columns(3)
    if r1.button("✅ PASS", key="finp",use_container_width=True): form["assembly_result"]="PASSED"
    if r2.button("❌ FAIL", key="finf",use_container_width=True): form["assembly_result"]="FAILED"
    if r3.button("🔧 REPAIR",key="finr",use_container_width=True): form["assembly_result"]="REPAIR"
    cur=form.get("assembly_result","")
    st.markdown(f"**{'✅ PASSED' if cur=='PASSED' else '❌ FAILED' if cur=='FAILED' else '🔧 REPAIR' if cur=='REPAIR' else '— not set'}**")

st.divider()
st.subheader("🔨 Repairs")
form["repair_desc"]=st.text_area("Description of Repairs (including Part #)",form.get("repair_desc",""))
co1,co2=st.columns(2)
with co1:
    form["rep_cva"]   =st.checkbox("Check Valve Assembly",    form.get("rep_cva",False))
    form["rep_rva"]   =st.checkbox("Relief Valve Assembly",   form.get("rep_rva",False))
    form["rep_aiva"]  =st.checkbox("Air Inlet Valve Assembly",form.get("rep_aiva",False))
    form["rep_rubber"]=st.checkbox("Rubber Repair Kit",       form.get("rep_rubber",False))
with co2:
    form["rep_flush"] =st.checkbox("Flush & Remove Debris",form.get("rep_flush",False))
    form["rep_clean"] =st.checkbox("Clean Internal",       form.get("rep_clean",False))
    form["rep_osy"]   =st.checkbox("OS&Y Repair",          form.get("rep_osy",False))
    form["rep_repack"]=st.checkbox("Re-Packing",           form.get("rep_repack",False))
form["rep_new"]=st.checkbox("New Backflow",form.get("rep_new",False))
form["remarks"]=st.text_area("Remarks / Repairs Needed",form.get("remarks",""))

st.divider()
st.subheader("👷 Tester Information")
co1,co2,co3=st.columns(3)
form["gauge_mfg"]   =co1.text_input("Gauge Manufacturer",form.get("gauge_mfg",""),   disabled=st.session_state.locked)
form["gauge_serial"]=co2.text_input("Gauge Serial #",    form.get("gauge_serial",""),disabled=st.session_state.locked)
form["date_cal"]    =co3.text_input("Date Calibrated",   form.get("date_cal",""),    disabled=st.session_state.locked)
co1,co2,co3=st.columns(3)
form["cert_no"]   =co1.text_input("Certification No.", form.get("cert_no",""),   disabled=st.session_state.locked)
form["technician"]=co2.text_input("Technician",        form.get("technician",""),disabled=st.session_state.locked)
form["recert"]    =co3.text_input("Re-Cert Due Date",  form.get("recert",""),    disabled=st.session_state.locked)

st.divider()
if st.button("📄 Generate & Download PDF", use_container_width=True, type="primary"):
    save_session(form)
    try:
        pdf_bytes = generate_pdf(form)
        cust  = (form.get("customer_name") or "Customer").replace("/","_").replace("\\","_")
        addr  = (form.get("street_address") or "Address").replace("/","_").replace("\\","_")
        fname = f"{cust} - {addr}.pdf"
        st.download_button(label=f"⬇️ Download: {fname}", data=pdf_bytes, file_name=fname, mime="application/pdf", use_container_width=True)
        st.success(f"PDF ready — {fname}")
    except Exception as e:
        st.error(f"Error generating PDF: {e}"); st.exception(e)

st.caption("🔒 Lock Site Info to prevent accidental edits between jobs. Tester fields persist after Save Session.")
