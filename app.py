import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.lib.colors import HexColor
import io
import re

# --- NASTAVENIA STRÁNKY ---
st.set_page_config(page_title="Farebné Regálové štítky PRO", layout="wide")

# --- POMOCNÁ FUNKCIA NA PRIRODZENÉ RADENIE (Natural Sort) ---
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

# --- PARAMETRE ---
PAGE_W, PAGE_H = A4
STRIP_H = 19.8 * mm
STRIP_W = 210 * mm
ROWS_PER_PAGE = 15

def draw_label(c, x, y, text, barcode_scale, barcode_offset, show_inner_box, bg_hex):
    bg_color = HexColor(bg_hex)
    
    # 1. Vyplnenie pozadia štítku farbou
    c.setFillColor(bg_color)
    c.rect(x, y, STRIP_W, STRIP_H, stroke=0, fill=1)

    box_end_x = x + 100 * mm # Predvolená hodnota, ak by kód zlyhal

    # 2. Čiarový kód a BIELY BOX
    try:
        bc_h = STRIP_H * 0.7
        bc = code128.Code128(text, barHeight=bc_h, barWidth=barcode_scale)
        bc_w = bc.width
        
        padding = 2 * mm
        box_x = x + barcode_offset * mm
        box_y = y + (STRIP_H - (bc_h + padding)) / 2
        box_w = bc_w + (padding * 2)
        box_h = bc_h + padding
        
        # Zapamätáme si, kde končí biely box pre výpočet stredu textu
        box_end_x = box_x + box_w

        # Kreslenie bieleho boxu
        c.setFillColorRGB(1, 1, 1)
        c.rect(box_x, box_y, box_w, box_h, stroke=1 if show_inner_box else 0, fill=1)
        
        # Kreslenie kódu
        c.setFillColorRGB(0, 0, 0)
        bc.drawOn(c, box_x + padding, box_y + (padding / 2))
    except:
        pass

    # 3. Vonkajšie ohraničenie štítku (čierne)
    c.setLineWidth(0.4 * mm)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(x, y, STRIP_W, STRIP_H, stroke=1, fill=0)

    # 4. Text - Rozdelenie a VYCENTROVANIE
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

    # --- VÝPOČET CENTROVANIA ---
    # Priestor napravo od bieleho boxu
    available_space_start = box_end_x
    available_space_end = x + STRIP_W
    center_of_available_space = (available_space_start + available_space_end) / 2
    
    # Výpočet celkovej šírky textu (Normal + Bold)
    font_normal = 22
    font_bold = 30
    w_prefix = c.stringWidth(prefix, "Helvetica", font_normal)
    w_bold = c.stringWidth(bold_part, "Helvetica-Bold", font_bold)
    total_text_width = w_prefix + w_bold + 1*mm # 1mm medzera medzi nimi
    
    # Štartovacia pozícia X pre text tak, aby bol stred celého textu v strede voľného miesta
    text_x_start = center_of_available_space - (total_text_width / 2)
    text_y = y + (STRIP_H / 2) - 3.5 * mm

    # Kreslenie normálnej časti
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", font_normal)
    c.drawString(text_x_start, text_y, prefix)
    
    # Kreslenie tučnej časti
    c.setFont("Helvetica-Bold", font_bold)
    c.drawString(text_x_start + w_prefix + 1*mm, text_y - 0.5*mm, bold_part)

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
st.title("🎨 Regálové štítky")
st.markdown("![Návštevy](https://hits.dwyl.com/jongens1/farebne-stitky-final-v7.svg)")

v_mode = st.radio("Zadanie:", ["Ručný zoznam", "Automatický rozsah"], horizontal=True)
locs = []

c1, c2 = st.columns([1, 1])

with c1:
    if v_mode == "Ručný zoznam":
        txt = st.text_area("Vložte lokácie (napr. 2MP-01-23-2):", height=300)
        if txt.strip():
            locs = [x.strip() for x in re.split(r'[;,\n\t]+', txt) if x.strip()]
    else:
        pre = st.text_input("Prefix:", value="2MP-01-")
        col_a, col_b = st.columns(2)
        s_n = col_a.number_input("Číslo od:", value=1)
        e_n = col_b.number_input("Číslo do:", value=15)
        # Nový pomocný prvok pre druhú časť rozsahu (napr. 20-1 až 20-4)
        suffix_mode = st.checkbox("Pridať pod-rozsah (napr. -1 až -4)")
        suf_start, suf_end = 1, 1
        if suffix_mode:
            c_suf1, c_suf2 = st.columns(2)
            suf_start = c_suf1.number_input("Pod-číslo od:", value=1)
            suf_end = c_suf2.number_input("Pod-číslo do:", value=4)

        if st.button("Pripraviť zoznam"):
            if suffix_mode:
                locs = [f"{pre}{i}-{j}" for i in range(s_n, e_n + 1) for j in range(s_start, s_end + 1)]
            else:
                locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]

with c2:
    st.subheader("Vzhľad")
    bg_color = st.color_picker("Farba pozadia", "#33A2FF") 
    b_offset = st.slider("Pozícia kódu zľava (mm):", 5, 100, 15)
    b_scale = st.slider("Hustota kódu:", 0.3, 1.2, 0.5, 0.05)
    do_sort = st.checkbox("Automaticky zoradiť zoznam", value=True)
    show_box = st.checkbox("Zobraziť mriežku kódu", value=True)
    
    if st.button("🚀 Generovať PDF", type="primary"):
        if v_mode == "Automatický rozsah" and not locs:
            if suffix_mode:
                locs = [f"{pre}{i}-{j}" for i in range(s_n, e_n + 1) for j in range(suf_start, suf_end + 1)]
            else:
                locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]
        
        if locs:
            if do_sort:
                locs.sort(key=natural_sort_key)
            with st.spinner('Generujem...'):
                pdf = generate_pdf(locs, b_scale, b_offset, show_box, bg_color)
                st.success(f"✅ Hotovo ({len(locs)} štítkov)")
                st.download_button("⬇️ STIAHNUŤ PDF", pdf, "stitky_final.pdf", "application/pdf")
