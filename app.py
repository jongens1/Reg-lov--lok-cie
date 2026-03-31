import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
import io
import re

# --- NASTAVENIA STRÁNKY ---
st.set_page_config(page_title="Regálové štítky PRO", layout="wide")

# --- PARAMETRE ---
PAGE_W, PAGE_H = A4
STRIP_H = 19.8 * mm
STRIP_W = 210 * mm
ROWS_PER_PAGE = 15

def draw_label(c, x, y, text, barcode_scale, barcode_offset):
    # 1. Vonkajší rámček štítku (210mm)
    c.setLineWidth(0.4 * mm)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(x, y, STRIP_W, STRIP_H)

    # 2. Príprava čiarového kódu a jeho vnútorného rámčeka
    try:
        # Výška samotných čiar
        bc_h = STRIP_H * 0.7
        bc = code128.Code128(text, barHeight=bc_h, barWidth=barcode_scale)
        bc_w = bc.width
        
        # Súradnice pre vnútorný rámček kódu
        # padding určuje medzeru medzi čiarami a rámčekom kódu
        padding = 2 * mm
        box_x = x + barcode_offset * mm
        box_y = y + (STRIP_H - (bc_h + padding)) / 2
        box_w = bc_w + (padding * 2)
        box_h = bc_h + padding

        # Kreslenie vnútorného rámčeka okolo kódu
        c.setLineWidth(0.2 * mm)
        c.rect(box_x, box_y, box_w, box_h)

        # Kreslenie samotného kódu do vnútra rámčeka
        bc.drawOn(c, box_x + padding, box_y + (padding / 2))
    except:
        pass

    # 3. Text (vpravo) - Posledné dva segmenty TUČNE
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

    # Pozícia textu (vzdialenosť od pravého okraja pre lepšie zarovnanie)
    text_x_base = x + 145 * mm 
    text_y = y + (STRIP_H / 2) - 3.5 * mm

    # Kreslenie normálnej časti
    c.setFont("Helvetica", 22)
    c.drawString(text_x_base, text_y, prefix)
    
    prefix_width = c.stringWidth(prefix, "Helvetica", 22)
    
    # Kreslenie TUČNEJ časti
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
        e_n = st.number_input("Číslo do:", value=15)
        if st.button("Pripraviť zoznam"):
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]

with c2:
    st.subheader("Estetika a mriežka")
    b_offset = st.slider("Pozícia kódu zľava (mm):", 5, 100, 15)
    b_scale = st.slider("Hustota čiar kódu:", 0.3, 1.2, 0.5, 0.05)
    
    st.info("Štítok obsahuje vonkajšie ohraničenie aj vnútorný rámček pre kód.")
    
    if st.button("🚀 Generovať PDF", type="primary"):
        if v_mode == "Automatický rozsah" and not locs:
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]
        if locs:
            pdf = generate_pdf(locs, b_scale, b_offset)
            st.success(f"✅ PDF pripravené ({len(locs)} štítkov)")
            st.download_button("⬇️ STIAHNUŤ PDF", pdf, "regalove_stitky_box.pdf", "application/pdf")
