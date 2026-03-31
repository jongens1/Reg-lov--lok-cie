import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
import io
import re

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Regálové štítky PRO", layout="wide")

# --- PARAMETRE ---
PAGE_W, PAGE_H = A4
STRIP_H = 19.8 * mm
STRIP_W = 210 * mm
ROWS_PER_PAGE = 15

def draw_label(c, x, y, text, barcode_scale, barcode_offset):
    # 1. Rámček štítku
    c.setLineWidth(0.4 * mm)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(x, y, STRIP_W, STRIP_H)

    # 2. Čiarový kód (Posunutý viac doprava pre estetiku)
    try:
        bc_h = STRIP_H * 0.75
        bc = code128.Code128(text, barHeight=bc_h, barWidth=barcode_scale)
        # barcode_offset určuje štart kódu zľava
        bc.drawOn(c, x + barcode_offset * mm, y + (STRIP_H - bc_h)/2)
    except:
        pass

    # 3. Text (vpravo) - Rozdelenie: Posledné dva segmenty TUČNE
    # Príklad: 2A-01-1-9 -> prefix: 2A-01- | bold: 1-9
    parts = text.split('-')
    if len(parts) >= 3:
        prefix = "-".join(parts[:-2]) + "-"
        bold_part = "-".join(parts[-2:])
    elif len(parts) == 2:
        prefix = parts[0] + "-"
        bold_part = parts[1]
    else:
        prefix = text
        bold_part = ""

    # Pozícia textu
    text_x_base = x + 135 * mm # Mierne posunuté doľava aby sa zmestil väčší font
    text_y = y + (STRIP_H / 2) - 3.5 * mm

    # Kreslenie normálnej časti (Font zväčšený na 22)
    c.setFont("Helvetica", 22)
    c.drawString(text_x_base, text_y, prefix)
    
    prefix_width = c.stringWidth(prefix, "Helvetica", 22)
    
    # Kreslenie TUČNEJ časti (Font zväčšený na 30)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(text_x_base + prefix_width + 1*mm, text_y - 0.5*mm, bold_part)

def generate_pdf(locations, barcode_scale, barcode_offset):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    idx = 0
    while idx < len(locations):
        for r in range(ROWS_PER_PAGE):
            if idx >= len(locations): break
            curr_y = PAGE_H - ((r + 1) * STRIP_H)
            draw_label(c, 0, curr_y, locations[idx], barcode_scale, barcode_offset)
            idx += 1
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP ---
st.title("🏭 Regálové štítky (210 x 19.8 mm)")

v_mode = st.radio("Zadanie:", ["Ručný zoznam", "Automatický rozsah"], horizontal=True)
locs = []

c1, c2 = st.columns([1, 1])

with c1:
    if v_mode == "Ručný zoznam":
        txt = st.text_area("Vložte lokácie (napr. 2A-01-1-9):", height=300)
        if txt.strip():
            locs = [x.strip() for x in re.split(r'[;,\n]+', txt) if x.strip()]
    else:
        pre = st.text_input("Prefix (všetko pred meniacim sa číslom):", value="2A-01-1-")
        s_n = st.number_input("Číslo od:", value=1)
        e_n = st.number_input("Číslo do:", value=10)
        if st.button("Pripraviť zoznam"):
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]

with c2:
    st.subheader("Estetické nastavenia")
    b_offset = st.slider("Odsadenie kódu zľava (mm):", 5, 100, 30)
    b_scale = st.slider("Šírka čiar (hustota):", 0.3, 1.2, 0.6, 0.05)
    
    if st.button("🚀 Generovať PDF", type="primary"):
        if v_mode == "Automatický rozsah" and not locs:
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]
        if locs:
            pdf = generate_pdf(locs, b_scale, b_offset)
            st.success(f"✅ PDF pripravené ({len(locs)} štítkov)")
            st.download_button("⬇️ STIAHNUŤ PDF", pdf, "regalove_stitky.pdf", "application/pdf")
