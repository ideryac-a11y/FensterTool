import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Profi-Fensteraufmaß v6.5", layout="wide")

# --- STAMMDATEN ---
LIEFERANTEN_MASSE = [50, 70, 90, 110, 130, 150, 165, 180, 195, 210, 225, 240, 260, 280, 300, 320, 340, 360, 380, 400]
FARBEN_BLECH = ["Silber", "Weiß", "Anthrazit", "Bronze"]
FARBEN_GURT = ["Silber", "Beige", "Weiß"]
GURTWICKLER_MASSE = ["Kein Gurtwickler", "13,8 cm", "16,5 cm", "18,5 cm", "20,5 cm"]
PROFILTIEFEN = [70, 76, 80, 82]
FENSTERARTEN = ["DKR", "DKL", "Festverglasung", "DKL-DKR", "D-DKR", "DKL-D", "Fest-DKR", "DKL-Fest"]

# --- HILFSFUNKTIONEN ---
def berechne_bestellmass(rechenwert, liste):
    unterer_wert = 0
    index = 0
    for i, wert in enumerate(liste):
        if wert <= rechenwert:
            unterer_wert = wert
            index = i
        else: break
    if unterer_wert == 0: return liste[0]
    return unterer_wert if (rechenwert - unterer_wert) <= 5 else (liste[index + 1] if index + 1 < len(liste) else liste[-1])

def runden_auf_5(zahl):
    return 5 * round(zahl / 5)

def generate_pdf(daten):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Aufmass-Protokoll", ln=True, align='C')
    pdf.ln(10)
    for entry in daten:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, txt=f"Pos: {entry.get('Pos', '??')} - {entry.get('Art', '??')}", ln=True)
        pdf.set_font("Arial", "", 9)
        protokoll_text = (f"Bestellmass (BxH): {entry.get('Bestellmaß (BxH)', '??')} | Glas: {entry.get('Glas', '??')}\n"
                         f"Kastent.: {entry.get('Kastent.', '??')} | Deckel: {entry.get('Deckel Neu', '??')}\n"
                         f"Schienen: {entry.get('Schienen', '??')} | Traverse: {entry.get('Traverse', '??')}\n"
                         f"Blech: {entry.get('Blech Fertigmaß', '??')} ({entry.get('Blech-F', '??')})\n"
                         f"Bemerkungen: {entry.get('Bemerkungen', '')}")
        pdf.multi_cell(0, 5, txt=protokoll_text.encode('latin-1', 'replace').decode('latin-1'))
        if entry.get("Foto") is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                img = entry["Foto"].convert("RGB")
                img.save(tmpfile.name, format="JPEG", quality=75)
                pdf.image(tmpfile.name, w=50)
                os.unlink(tmpfile.name)
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1', 'replace')

if 'daten' not in st.session_state:
    st.session_state.daten = []

st.title("🏗️ Profi-Aufmaß v6.5")

# --- SEITENLEISTE ---
with st.sidebar:
    st.header("1. Altmaße & Foto")
    pos = st.text_input("Position", f"{len(st.session_state.daten) + 1:02d}")
    foto_file = st.camera_input("Foto aufnehmen")

    st.subheader("Lichte Breite Innen (mm)")
    b1 = st.number_input("Breite 1", value=1000, min_value=0)
    b2 = st.number_input("Breite 2 (opt.)", value=0, min_value=0)
    b3 = st.number_input("Breite 3 (opt.)", value=0, min_value=0)
    breiten = [b for b in [b1, b2, b3] if b > 0]
    m_b_in_avg = sum(breiten) / len(breiten) if breiten else 0
    st.caption(f"Ø Breite: {m_b_in_avg:.1f} mm")

    st.subheader("Lichte Höhe Innen (mm)")
    h1 = st.number_input("Höhe 1", value=1250, min_value=0)
    h2 = st.number_input("Höhe 2 (opt.)", value=0, min_value=0)
    h3 = st.number_input("Höhe 3 (opt.)", value=0, min_value=0)
    hoehen = [h for h in [h1, h2, h3] if h > 0]
    m_h_in_avg = sum(hoehen) / len(hoehen) if hoehen else 0
    st.caption(f"Ø Höhe: {m_h_in_avg:.1f} mm")
    
    st.markdown("---")
    dt1 = st.number_input("Deckeltiefe 1", value=140, min_value=0)
    dt2 = st.number_input("Deckeltiefe 2 (opt.)", value=0, min_value=0)
    d_tiefen = [dt for dt in [dt1, dt2] if dt > 0]
    d_tiefe_alt_avg = sum(d_tiefen) / len(d_tiefen) if d_tiefen else 0
    
    b_tiefe_alt = st.number_input("Bautiefe alt (mm)", value=70)
    m_b_aus = st.number_input("Lichte Breite Außen (mm)", value=1000)
    laibung = st.number_input("Laibungstiefe (mm)", value=150)
    
    st.header("2. Technik (Neu)")
    f_art = st.selectbox("Fensterart", FENSTERARTEN)
    v_fach = st.selectbox("Verglasung", ["2-fach", "3-fach"], index=1)
    glas_typ = st.text_input("Glasart", "Klarglas")
    kasten_typ = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    schiene_t = st.radio("Schienentiefe (mm)", [40, 48]) if kasten_typ == "Mit Kasten" else 0
    profil_t = st.selectbox("Profiltiefe Fenster (mm)", PROFILTIEFEN)
    
    st.header("3. Rollladen-Zubehör")
    welle_benoetigt = st.checkbox("Welle SW60 benötigt?", value=True)
    welle_plus = st.number_input("Welle Zusatzmaß (mm)", value=0) if welle_benoetigt else 0
    teleskop = st.checkbox("Teleskop-Endstück")
    gurtrolle = st.checkbox("Gurtrolle")
    zubehoer_frei = st.text_input("Sonstiges Zubehör", "")
    
    st.header("4. Gurt & Wickler")
    gurt_bed = st.checkbox("Gurtbedienung?", value=True)
    gurt_wick = st.selectbox("Gurtwickler", GURTWICKLER_MASSE[1:]) if gurt_bed else "-"
    gurt_f = st.selectbox("Gurtfarbe", FARBEN_GURT) if gurt_bed else "-"
    v_laenge = "5 m" if m_h_in_avg <= 1300 else "6 m"
    
    st.header("5. Bleche")
    f_blech = st.selectbox("Farbe Blech", FARBEN_BLECH)
    endstueck_typ = st.radio("Endstück", ["Putzendstück", "Gleitendstück"])

    bemerkungen = st.text_area("Bemerkungen")

    if st.button("💾 Pos. Speichern"):
        kastentiefe = d_tiefe_alt_avg + b_tiefe_alt
        bautiefe_neu = profil_t + schiene_t
        deckeltiefe_neu = runden_auf_5(kastentiefe - bautiefe_neu + 10)
        br_b, br_h = m_b_in_avg - 12, (m_h_in_avg if kasten_typ == "Mit Kasten" else m_h_in_avg - 6)
        pz_b, pz_h = br_b - 35, br_h + 150
        blech_b, ausl_bestell = m_b_aus + 30, berechne_bestellmass(laibung + 10 + schiene_t + 45, LIEFERANTEN_MASSE)
        welle_text = f"{m_b_in_avg + welle_plus:.1f} mm" if welle_benoetigt else "-"
        
        extras_liste = [e for e, b in [("Teleskop", teleskop), ("Gurtrolle", gurtrolle)] if b]
        if zubehoer_frei: extras_liste.append(zubehoer_frei)

        st.session_state.daten.append({
            "Pos": pos, "Art": f_art, "Glas": f"{v_fach} {glas_typ}",
            "Ø Alt (BxH)": f"{m_b_in_avg:.0f}x{m_h_in_avg:.0f}", 
            "Bestellmaß (BxH)": f"{br_b:.1f}x{br_h:.1f}", 
            "Kastent.": f"{kastentiefe:.1f}", "Deckel Neu": f"{(m_b_in_avg+50):.1f}x{deckeltiefe_neu:.0f}",
            "Bau Neu": f"{profil_t} mm", "Schienen": f"Ja ({schiene_t}mm)" if kasten_typ=="Mit Kasten" else "Nein",
            "Traverse": "Ja" if kasten_typ=="Mit Kasten" else "Nein", "Panzer": f"{pz_b:.0f}x{pz_h:.0f}",
            "Welle": welle_text, "Wickler": gurt_wick, "Gurt-L": v_laenge if gurt_bed else "-", "Gurt-F": gurt_f,
            "Blech Fertigmaß": f"{blech_b}x{ausl_bestell}", "Blech-F": f_blech, "Endstück": endstueck_typ,
            "Extras": ", ".join(extras_liste), "Bemerkungen": bemerkungen,
            "Foto": Image.open(foto_file) if foto_file else None
        })
        st.rerun()

# --- HAUPTBEREICH ---
if st.session_state.daten:
    st.subheader("Aktuelle Bestellliste")
    df_view = pd.DataFrame(st.session_state.daten).drop(columns=["Foto"])
    st.dataframe(df_view, use_container_width=True)

    st.markdown("---")
    st.subheader("Positionen sortieren / löschen")
    for i, row in enumerate(st.session_state.daten):
        # Nutze .get(), um Absturz bei alten Spaltennamen zu verhindern
        pos_label = row.get('Pos', '??')
        art_label = row.get('Art', '??')
        mass_label = row.get('Bestellmaß (BxH)', 'Altlast')
        
        with st.expander(f"Pos {pos_label} - {art_label} ({mass_label})"):
            c1, c2, c3 = st.columns([1, 4, 1.2])
            if row.get("Foto"): c1.image(row["Foto"], width=120)
            c2.write(f"**Bestellmaß:** {mass_label} | **Blech:** {row.get('Blech Fertigmaß', '??')}")
            c2.write(f"**Extras:** {row.get('Extras', '')} | **Bemerkung:** {row.get('Bemerkungen', '')}")
            with c3:
                col_up, col_down, col_del = st.columns(3)
                if col_up.button("⬆️", key=f"u_{i}") and i > 0:
                    st.session_state.daten[i], st.session_state.daten[i-1] = st.session_state.daten[i-1], st.session_state.daten[i]
                    st.rerun()
                if col_down.button("⬇️", key=f"d_{i}") and i < len(st.session_state.daten)-1:
                    st.session_state.daten[i], st.session_state.daten[i+1] = st.session_state.daten[i+1], st.session_state.daten[i]
                    st.rerun()
                if col_del.button("🗑️", key=f"x_{i}"):
                    st.session_state.daten.pop(i)
                    st.rerun()

    st.markdown("### Export")
    e1, e2, e3 = st.columns(3)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_view.to_excel(writer, index=False)
    e1.download_button("📊 Excel Export", data=output.getvalue(), file_name="Aufmass.xlsx")
    pdf_data = generate_pdf(st.session_state.daten)
    e2.download_button("📄 PDF inkl. Fotos", data=pdf_data, file_name="Protokoll.pdf")
    if e3.button("⚠️ Alles löschen"):
        st.session_state.daten = []
        st.rerun()
