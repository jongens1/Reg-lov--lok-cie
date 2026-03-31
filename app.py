import streamlit as st
    text_x_base = x + 145 * mm 
    text_y = y + (STRIP_H / 2) - 3.5 * mm

    c.setFont("Helvetica", 22)
    c.drawString(text_x_base, text_y, prefix)
    prefix_width = c.stringWidth(prefix, "Helvetica", 22)
    
    c.setFont("Helvetica-Bold", 30)
    c.drawString(text_x_base + prefix_width + 1*mm, text_y - 0.5*mm, bold_part)

def generate_pdf(locations, barcode_scale, barcode_offset, show_inner_box):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Progress bar pre veľké množstvá
    progress_bar = st.progress(0)
    total_locs = len(locations)

    idx = 0
    while idx < total_locs:
        for r in range(ROWS_PER_PAGE):
            if idx >= total_locs: break
            curr_y = PAGE_H - ((r + 1) * STRIP_H)
            draw_label(c, 0, curr_y, locations[idx], barcode_scale, barcode_offset, show_inner_box)
            idx += 1
        
        c.showPage()
        # Aktualizácia progress baru každých 15 lokácií
        progress_bar.progress(min(idx / total_locs, 1.0))
        
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP ---
st.title("🏭 Regálové štítky (210 x 19.8 mm)")

v_mode = st.radio("Zadanie:", ["Ručný zoznam", "Automatický rozsah"], horizontal=True)
locs = []

c1, col_spacer, c2 = st.columns([1, 0.1, 1])

with c1:
    if v_mode == "Ručný zoznam":
        txt = st.text_area("Vložte lokácie (napr. 2A-01-1-9):", height=350)
        if txt.strip():
            locs = [x.strip() for x in re.split(r'[;,\n\t\s]+', txt) if x.strip()]
    else:
        st.subheader("Nastavenie rozsahu")
        pre = st.text_input("Prefix:", value="2A-01-1-")
        s_n = st.number_input("Číslo od:", value=1, step=1)
        e_n = st.number_input("Číslo do:", value=15, step=1)
        if st.button("Pripraviť zoznam"):
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]
            st.info(f"Vytvorených {len(locs)} lokácií.")

with c2:
    st.subheader("Estetika a limity")
    b_offset = st.slider("Pozícia kódu zľava (mm):", 5, 100, 15)
    b_scale = st.slider("Hustota čiar kódu:", 0.3, 1.2, 0.5, 0.05)
    
    # NOVÝ PREPÍNAČ PRE RÁMČEK
    show_inner_box = st.checkbox("Zobraziť rámček okolo kódu", value=True)
    
    st.warning(f"Aktuálny počet lokácií: **{len(locs)}**")
    if len(locs) > 1000:
        st.write(f"⚠️ PDF bude mať približne {-(len(locs)//-15)} strán. Generovanie môže chvíľu trvať.")

    if st.button("🚀 Generovať PDF", type="primary"):
        if v_mode == "Automatický rozsah" and not locs:
            locs = [f"{pre}{i}" for i in range(s_n, e_n + 1)]
        
        if locs:
            with st.spinner('Generujem PDF... Prosím čakajte.'):
                pdf = generate_pdf(locs, b_scale, b_offset, show_inner_box)
                st.success(f"✅ PDF hotové!")
                st.download_button("⬇️ STIAHNUŤ PDF", pdf, "regalove_stitky.pdf", "application/pdf")
        else:
            st.error("Zoznam je prázdny!")
