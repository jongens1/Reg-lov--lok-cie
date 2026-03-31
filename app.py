import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
import io
import re

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Regálové štítky 210x19.8", layout="wide")

# --- PARAMETRE ---
PAGE_W, PAGE_H = A4
STRIP_H = 19.8 * mm
STRIP_W = 210 * mm
ROWS_PER_PAGE = 15

def draw_label(c, x, y, text, barcode_scale):
    # Rámček štítku
    c.setLineWidth(0.5 * mm)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(x, y, STRIP_W, STRIP_H)

    # Čiarový kód
    try:
        bc_h = STRIP_H * 0.7
        bc = code128.Code128(text, barHeight=bc_h, barWidth=barcode_scale)
        bc.drawOn(c, x + 5*mm, y + (STRIP_H - bc_h)/2)
    except:
        pass

    # Text (vpravo)
    if '-' in text:
        parts = text.rsplit('-', 1)
        prefix = parts[0] + "-"
        bold_part = parts[1]
    else:
        prefix = text
        bold_part = ""

    text_x_base = x + 140 * mm
    text_y = y + (STRIP_H / 2) - 3*mm

    c.setFont("Helvetica", 18)
    c.drawString(text_x_base, text_y, prefix)
    
    prefix_width = c.stringWidth(prefix, "Helvetica", 18)
    
    c.setFont("Helvetica-Bold", 26)
    c.drawString(text_x_base + prefix_width + 1*mm, text_y - 1*mm, bold_part)

def generate_pdf(locations, barcode_scale):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    idx = 0
    while idx < len(locations):
        for r in range(ROWS_PER_PAGE):
            if idx >= len(locations):
                break
            curr_y = PAGE_H - ((r + 1) * STRIP_H)
            draw_label(c, 0, curr_y, locations[idx], barcode_scale)
            idx += 1
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

st.title("🏭 Generátor regálových štítkov (210 x 19.8 mm)")
st.markdown("![Návštevy](https://hits.dwyl.com/jongens1/regalove-stitky-as-v3.svg)")

v_mode = st.radio("Zadanie:", ["Ručný zoznam", "Automatický rozsah"], horizontal=True)
locs = []

c1, c2 = st.columns([1, 1])

with c1:
    if v_mode == "Ručný zoznam":
        txt = st.text_area("Vložte lokácie:", height=300)
        if txt.strip():
            locs = [x.strip() for x in re.split(r'[;,\n]+', txt) if x.strip()]
    else:
        pre = st.text_input("Prefix:", value="1X-01-")
        s_n = st.number_input("Od:", value=1)
        e_n = st.number_input("Do:", value=6)
        if st.button("Vytvoriť zoznam"):
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]

with c2:
    b_scale = st.slider("Hustota kódu:", 0.3, 1.2, 0.6, 0.05)
    if st.button("🚀 Generovať PDF", type="primary"):
        if v_mode == "Automatický rozsah" and not locs:
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]
        if locs:
            pdf = generate_pdf(locs, b_scale)
            st.success(f"✅ Hotovo ({len(locs)} štítkov)")
            st.download_button("⬇️ STIAHNUŤ", pdf, "stitky.pdf", "application/pdf")
        else:
            st.error("Zoznam je prázdny!")
