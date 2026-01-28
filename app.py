import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Profi-Fensteraufmaß v6.2", layout="wide")

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
        pdf.cell(0, 8, txt=f"Pos: {entry['Pos']} - {entry['Art']}", ln=True)
        pdf.set_font("Arial", "", 9)
        protokoll_text = (f"Fenster: {entry['Fenster (BxH)']} | Glas: {entry['Glas']}\n"
                         f"Kastent.: {entry['Kastent.']} | Deckel: {entry['Deckel Neu']}\n"
                         f"Schienen: {entry['Schienen']} | Traverse: {entry['Traverse']}\n"
                         f"Blech: {entry['Blech Fertigmaß']} ({entry['Blech-F']})\n"
                         f"Welle: {entry['Welle']} | Wickler: {entry['Wickler']} ({entry['Gurt-F']})\n"
                         f"Extras: {entry['Extras']}\n"
                         f"Bemerkungen: {entry['Bemerkungen']}")
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

st.title("🏗️ Profi-Aufmaß v6.2 (Alle Infos & Editierbar)")

# --- SEITENLEISTE (EINGABE v5.5) ---
with st.sidebar:
    st.header("1. Altmaße & Foto")
    pos = st.text_input("Position", f"{len(st.session_state.daten) + 1:02d}")
    foto_file = st.camera_input("Foto")

    b1 = st.number_input("Breite 1", value=1000)
    h1 = st.number_input("Höhe 1", value=1250)
    dt1 = st.number_input("Deckeltiefe 1", value=140)
    b_tiefe_alt = st.number_input("Bautiefe alt", value=70)
    m_b_aus = st.number_input("Lichte Breite Außen", value=1000)
    laibung = st.number_input("Laibungstiefe", value=150)
    
    st.header("2. Technik (Neu)")
    f_art = st.selectbox("Fensterart", FENSTERARTEN)
    v_fach = st.selectbox("Verglasung", ["2-fach", "3-fach"], index=1)
    glas_typ = st.text_input("Glasart", "Klarglas")
    kasten_typ = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    schiene_t = st.radio("Schienentiefe", [40, 48]) if kasten_typ == "Mit Kasten" else 0
    profil_t = st.selectbox("Profiltiefe Fenster", PROFILTIEFEN)
    
    st.header("3. Rollladen-Zubehör")
    welle_benoetigt = st.checkbox("Welle SW60?", value=True)
    welle_plus = st.number_input("Welle Zusatzmaß (mm)", value=0) if welle_benoetigt else 0
    teleskop = st.checkbox("Teleskop-Endstück")
    gurtrolle = st.checkbox("Gurtrolle")
    zubehoer_frei = st.text_input("Sonstiges Zubehör", "")
    
    st.header("4. Gurt & Wickler")
    gurt_bed = st.checkbox("Gurtbedienung?", value=True)
    gurt_wick = st.selectbox("Gurtwickler", GURTWICKLER_MASSE[1:]) if gurt_bed else "-"
    gurt_f = st.selectbox("Gurtfarbe", FARBEN_GURT) if gurt_bed else "-"
    
    st.header("5. Bleche")
    f_blech = st.selectbox("Farbe Blech", FARBEN_BLECH)
    
    st.header("6. Sonstiges")
    bemerkungen = st.text_area("Bemerkungen")

    if st.button("💾 Pos. Speichern"):
        kastentiefe = dt1 + b_tiefe_alt
        bautiefe_neu = profil_t + schiene_t
        deckeltiefe_neu = runden_auf_5(kastentiefe - bautiefe_neu + 10)
        br_b, br_h = b1 - 12, (h1 if kasten_typ == "Mit Kasten" else h1 - 6)
        pz_b, pz_h = br_b - 35, br_h + 150
        ausl_bestell = berechne_bestellmass(laibung + 10 + schiene_t + 45, LIEFERANTEN_MASSE)
        welle_text = f"{b1 + welle_plus:.1f} mm" if welle_benoetigt else "-"
        
        extras_liste = []
        if teleskop: extras_liste.append("Teleskop")
        if gurtrolle: extras_liste.append("Gurtrolle")
        if zubehoer_frei: extras_liste.append(zubehoer_frei)

        st.session_state.daten.append({
            "Pos": pos, "Art": f_art, "Glas": f"{v_fach} {glas_typ}",
            "Ø Alt (BxH)": f"{b1}x{h1}", "Fenster (BxH)": f"{br_b:.1f}x{br_h:.1f}",
            "Kastent.": f"{kastentiefe:.1f}", "Deckel Neu": f"{b1+50}x{deckeltiefe_neu:.0f}",
            "Bau Neu": f"{profil_t} mm", "Schienen": f"Ja ({schiene_t}mm)" if kasten_typ=="Mit Kasten" else "Nein",
            "Traverse": "Ja" if kasten_typ=="Mit Kasten" else "Nein", "Panzer": f"{pz_b:.0f}x{pz_h:.0f}",
            "Welle": welle_text, "Wickler": gurt_wick, "Gurt-L": "5/6m", "Gurt-F": gurt_f,
            "Blech Fertigmaß": f"{m_b_aus+30}x{ausl_bestell}", "Blech-F": f_blech,
            "Extras": ", ".join(extras_liste), "Bemerkungen": bemerkungen,
            "Foto": Image.open(foto_file) if foto_file else None
        })
        st.rerun()

# --- HAUPTBEREICH: TABELLE & EDIT ---
if st.session_state.daten:
    st.subheader("Aktuelle Aufmaßliste")
    df_view = pd.DataFrame(st.session_state.daten).drop(columns=["Foto"])
    st.dataframe(df_view, use_container_width=True)

    st.markdown("---")
    st.subheader("Positionen sortieren & löschen")
    for i, row in enumerate(st.session_state.daten):
        with st.expander(f"Pos {row['Pos']} - {row['Art']} ({row['Fenster (BxH)']})", expanded=False):
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                if row["Foto"]: st.image(row["Foto"], width=100)
            with c2:
                st.write(f"**Maße:** {row['Fenster (BxH)']} | **Schienen:** {row['Schienen']} | **Blech:** {row['Blech Fertigmaß']}")
                st.write(f"**Extras:** {row['Extras']} | **Bemerkung:** {row['Bemerkungen']}")
            with c3:
                # Steuerung
                st.write("Aktion:")
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
    
    # Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_view.to_excel(writer, index=False)
    e1.download_button("📊 Excel Export", data=output.getvalue(), file_name="Aufmass.xlsx")
    
    # PDF
    pdf_data = generate_pdf(st.session_state.daten)
    e2.download_button("📄 PDF Export (Fotos)", data=pdf_data, file_name="Protokoll.pdf")
    
    if e3.button("⚠️ Alles löschen"):
        st.session_state.daten = []
        st.rerun()
