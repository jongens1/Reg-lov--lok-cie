import streamlit as st
    c.rect(x, y, STRIP_W, STRIP_H)

    # 2. Čiarový kód (vľavo)
    try:
        bc_h = STRIP_H * 0.7
        bc = code128.Code128(text, barHeight=bc_h, barWidth=barcode_scale)
        bc.drawOn(c, x + 5*mm, y + (STRIP_H - bc_h)/2)
    except:
        pass

    # 3. Text (vpravo) - Rozdelenie na normálnu a TUČNÚ časť
    # Hľadáme poslednú pomlčku
    if '-' in text:
        parts = text.rsplit('-', 1)
        prefix = parts[0] + "-"
        bold_part = parts[1]
    else:
        prefix = text
        bold_part = ""

    # Nastavenie pozície textu
    text_x_base = x + 140 * mm
    text_y = y + (STRIP_H / 2) - 3*mm

    # Kreslenie normálnej časti
    c.setFont("Helvetica", 18)
    c.drawString(text_x_base, text_y, prefix)
    
    # Výpočet šírky predchádzajúceho textu, aby sme vedeli kde začať Bold časť
    prefix_width = c.stringWidth(prefix, "Helvetica", 18)
    
    # Kreslenie TUČNEJ a VÄČŠEJ časti
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
            
            # Výpočet súradníc (zhora nadol)
            # x je 0, lebo štítok má 210mm (celá šírka A4)
            curr_y = PAGE_H - ((r + 1) * STRIP_H)
            
            draw_label(c, 0, curr_y, locations[idx], barcode_scale)
            idx += 1
        
        c.showPage()
    
    c.save()
    buffer.seek(0)
    return buffer

# --- ROZHRANIE APP ---
st.title("🏭 Generátor regálových štítkov (210 x 19.8 mm)")
st.markdown("![Návštevy](https://hits.dwyl.com/jongens1/regalove-stitky-as.svg)")

vstup_mode = st.radio("Spôsob zadania:", ["Ručný zoznam (Enter)", "Automatický rozsah"], horizontal=True)

locations_to_print = []

col1, col2 = st.columns([1, 1])

with col1:
    if vstup_mode == "Ručný zoznam (Enter)":
        input_text = st.text_area("Vložte lokácie (napr. 1A-01-1):", height=300)
        if input_text.strip():
            locations_to_print = [x.strip() for x in re.split(r'[;,\n]+', input_text) if x.strip()]
    else:
        st.subheader("Nastavenie rozsahu")
        prefix = st.text_input("Prefix (všetko pred číslom):", value="1X-01-")
        c1, c2 = st.columns(2)
        start_n = c1.number_input("Číslo od:", value=1)
        end_n = c2.number_input("Číslo do:", value=6)
        
        if st.button("Vygenerovať zoznam"):
            locations_to_print = [f"{prefix}{i}" for i in range(start_n, end_n + 1)]
            st.info(f"Vytvorených {len(locations_to_print)} lokácií.")

with col2:
    st.subheader("Nastavenia tlače")
    barcode_scale = st.slider("Hustota čiarového kódu:", 0.3, 1.2, 0.6, 0.05)
    st.write("**Špecifikácia:**")
    st.write("- Rozmer: 210 x 19.8 mm")
    st.write("- Počet na A4: 15 ks")
    st.write("- Posledná časť za pomlčkou bude **Tučná a väčšia**.")

    if st.button("🚀 Pripraviť PDF na stiahnutie", type="primary"):
        # Ak sme v automatickom režime a zoznam je prázdny, vygenerujeme ho pred tlačou
        if vstup_mode == "Automatický rozsah" and not locations_to_print:
            locations_to_print = [f"{prefix}{i}" for i in range(start_n, end_n + 1)]
            
        if locations_to_print:
            pdf_buffer = generate_pdf(locations_to_print, barcode_scale)
            st.success(f"✅ PDF vygenerované ({len(locations_to_print)} štítkov)")
            st.download_button(
                label="⬇️ STIAHNUŤ PDF",
                data=pdf_buffer,
                file_name="regalove_stitky.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Zoznam lokácií je prázdny!")
