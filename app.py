import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.lib.colors import hexColor
import io
import re

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Farebné Regálové štítky", layout="wide")

# --- PARAMETRE ---
PAGE_W, PAGE_H = A4
STRIP_H = 19.8 * mm
STRIP_W = 210 * mm
ROWS_PER_PAGE = 15

def draw_label(c, x, y, text, barcode_scale, barcode_offset, show_inner_box, bg_hex):
    # Prevod HEX farby na formát pre ReportLab
    bg_color = hexColor(bg_hex)

    # 1. Vyplnenie pozadia štítku farbou
    c.setFillColor(bg_color)
    c.rect(x, y, STRIP_W, STRIP_H, stroke=0, fill=1)

    # 2. Príprava čiarového kódu a BIELY BOX pod ním
    try:
        bc_h = STRIP_H * 0.7
        bc = code128.Code128(text, barHeight=bc_h, barWidth=barcode_scale)
        bc_w = bc.width
        
        padding = 2 * mm
        box_x = x + barcode_offset * mm
        box_y = y + (STRIP_H - (bc_h + padding)) / 2
        box_w = bc_w + (padding * 2)
        box_h = bc_h + padding

        # VŽDY BIELY BOX pod kódom (kvôli skenovaniu)
        c.setFillColorRGB(1, 1, 1)
        c.rect(box_x, box_y, box_w, box_h, stroke=1 if show_inner_box else 0, fill=1)

        # Kreslenie samotného kódu (čiernou)
        c.setFillColorRGB(0, 0, 0)
        bc.drawOn(c, box_x + padding, box_y + (padding / 2))
    except:
        pass

    # 3. Vonkajšie ohraničenie štítku (čierne)
    c.setLineWidth(0.4 * mm)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(x, y, STRIP_W, STRIP_H, stroke=1, fill=0)

    # 4. Text (vpravo) - Posledné dva segmenty TUČNE
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

    text_x_base = x + 145 * mm 
    text_y = y + (STRIP_H / 2) - 3.5 * mm

    c.setFillColorRGB(0, 0, 0) # Text bude vždy čierny
    c.setFont("Helvetica", 22)
    c.drawString(text_x_base, text_y, prefix)
    prefix_width = c.stringWidth(prefix, "Helvetica", 22)
    
    c.setFont("Helvetica-Bold", 30)
    c.drawString(text_x_base + prefix_width + 1*mm, text_y - 0.5*mm, bold_part)

def generate_pdf(locations, barcode_scale, barcode_offset, show_inner_box, bg_hex):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    total_locs = len(locations)
    idx = 0
    while idx < total_locs:
        for r in range(ROWS_PER_PAGE):
            if idx >= total_locs: break
            curr_y = PAGE_H - ((r + 1) * STRIP_H)
            draw_label(c, 0, curr_y, locations[idx], barcode_scale, barcode_offset, show_inner_box, bg_hex)
            idx += 1
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP ---
st.title("🎨 Farebné regálové štítky (210 x 19.8 mm)")
st.markdown("![Návštevy](https://hits.dwyl.com/jongens1/farebne-stitky-as-v5.svg)")

v_mode = st.radio("Zadanie:", ["Ručný zoznam", "Automatický rozsah"], horizontal=True)
locs = []

c1, c2 = st.columns([1, 1])

with c1:
    if v_mode == "Ručný zoznam":
        txt = st.text_area("Vložte lokácie:", height=300)
        if txt.strip():
            locs = [x.strip() for x in re.split(r'[;,\n]+', txt) if x.strip()]
    else:
        pre = st.text_input("Prefix:", value="2A-01-1-")
        s_n = st.number_input("Od:", value=1)
        e_n = st.number_input("Do:", value=15)
        if st.button("Pripraviť zoznam"):
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]

with c2:
    st.subheader("Vzhľad a Farby")
    # COLOR PICKER
    bg_color = st.color_picker("Vyberte farbu pozadia štítku", "#33A2FF") # Predvolená modrá z obrázka
    
    b_offset = st.slider("Pozícia kódu zľava (mm):", 5, 100, 15)
    b_scale = st.slider("Hustota kódu:", 0.3, 1.2, 0.5, 0.05)
    show_box = st.checkbox("Zobraziť mriežku kódu", value=True)
    
    if st.button("🚀 Generovať PDF", type="primary"):
        if v_mode == "Automatický rozsah" and not locs:
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]
        if locs:
            with st.spinner('Generujem...'):
                pdf = generate_pdf(locs, b_scale, b_offset, show_box, bg_color)
                st.success(f"✅ Hotovo ({len(locs)} štítkov)")
                st.download_button("⬇️ STIAHNUŤ FAREBNÉ PDF", pdf, "farebne_stitky.pdf", "application/pdf")
