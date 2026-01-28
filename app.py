import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Profi-Fensteraufmaß v6.1", layout="wide")

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
        pdf.cell(0, 8, txt=f"Pos: {entry['Pos']} - Art: {entry['Art']}", ln=True)
        pdf.set_font("Arial", "", 9)
        protokoll_text = (f"Fenstermass: {entry['Fenster (BxH)']} | Glas: {entry['Glas']}\n"
                         f"Schienen: {entry['Schienen']} | Traverse: {entry['Traverse']}\n"
                         f"Bemerkungen: {entry['Bemerkungen']}")
        pdf.multi_cell(0, 5, txt=protokoll_text.encode('latin-1', 'replace').decode('latin-1'))
        if entry.get("Foto") is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                img = entry["Foto"].convert("RGB")
                img.save(tmpfile.name, format="JPEG", quality=75)
                pdf.image(tmpfile.name, w=40)
                os.unlink(tmpfile.name)
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1', 'replace')

if 'daten' not in st.session_state:
    st.session_state.daten = []

st.title("🏗️ Profi-Aufmaß v6.1 (Editierbar)")

# --- SEITENLEISTE ---
with st.sidebar:
    st.header("1. Neue Position")
    pos_val = st.text_input("Positions-ID", f"{len(st.session_state.daten) + 1:02d}")
    foto_file = st.camera_input("Foto")
    
    b1 = st.number_input("Breite (mm)", value=1000)
    h1 = st.number_input("Höhe (mm)", value=1250)
    dt1 = st.number_input("Deckeltiefe (mm)", value=140)
    bt_alt = st.number_input("Bautiefe alt (mm)", value=70)
    
    f_art = st.selectbox("Fensterart", FENSTERARTEN)
    v_fach = st.selectbox("Verglasung", ["2-fach", "3-fach"], index=1)
    glas_typ = st.text_input("Glasart", "Klarglas")
    kasten_typ = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    schiene_t = st.radio("Schiene (mm)", [40, 48]) if kasten_typ == "Mit Kasten" else 0
    profil_t = st.selectbox("Profiltiefe (mm)", PROFILTIEFEN)
    
    f_blech = st.selectbox("Farbe Blech", FARBEN_BLECH)
    laibung = st.number_input("Laibungstiefe (mm)", value=150)
    m_b_aus = st.number_input("Breite Außen (mm)", value=1000)
    bemerkungen = st.text_area("Bemerkungen")

    if st.button("💾 Pos. Speichern"):
        br_b, br_h = b1 - 12, (h1 if kasten_typ == "Mit Kasten" else h1 - 6)
        ausl_bestell = berechne_bestellmass(laibung + 10 + schiene_t + 45, LIEFERANTEN_MASSE)
        deckeltiefe_neu = runden_auf_5((dt1 + bt_alt) - (profil_t + schiene_t) + 10)
        
        st.session_state.daten.append({
            "Pos": pos_val, "Art": f_art, "Glas": f"{v_fach} {glas_typ}",
            "Fenster (BxH)": f"{br_b:.1f}x{br_h:.1f}", "Schienen": f"{schiene_t}mm" if kasten_typ=="Mit Kasten" else "Nein",
            "Traverse": "Ja" if kasten_typ=="Mit Kasten" else "Nein", "Blech-F": f_blech,
            "Blech Fertigmaß": f"{m_b_aus+30}x{ausl_bestell}", "Bemerkungen": bemerkungen,
            "Foto": Image.open(foto_file) if foto_file else None, "Deckel Neu": f"{b1+50}x{deckeltiefe_neu}"
        })
        st.rerun()

# --- HAUPTBEREICH: EDITIERMODUS ---
if st.session_state.daten:
    st.subheader("Aktuelle Liste & Bearbeitung")
    
    # Anzeige der Liste mit Steuerungs-Buttons
    for i, row in enumerate(st.session_state.daten):
        with st.container():
            c1, c2, c3, c4 = st.columns([0.5, 3, 4, 2.5])
            with c1:
                st.write(f"**{i+1}**")
            with c2:
                st.write(f"**Pos {row['Pos']}**: {row['Art']} ({row['Fenster (BxH)']})")
            with c3:
                st.write(f"Glas: {row['Glas']} | Blech: {row['Blech-F']}")
            with c4:
                # Buttons zum Verschieben und Löschen
                col_up, col_down, col_del = st.columns(3)
                if col_up.button("⬆️", key=f"up_{i}") and i > 0:
                    st.session_state.daten[i], st.session_state.daten[i-1] = st.session_state.daten[i-1], st.session_state.daten[i]
                    st.rerun()
                if col_down.button("⬇️", key=f"down_{i}") and i < len(st.session_state.daten)-1:
                    st.session_state.daten[i], st.session_state.daten[i+1] = st.session_state.daten[i+1], st.session_state.daten[i]
                    st.rerun()
                if col_del.button("🗑️", key=f"del_{i}"):
                    st.session_state.daten.pop(i)
                    st.rerun()
        st.divider()

    # EXPORT-BEREICH
    st.markdown("### Dokumente erzeugen")
    e1, e2, e3 = st.columns(3)
    
    df_excel = pd.DataFrame(st.session_state.daten).drop(columns=["Foto"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_excel.to_excel(writer, index=False)
    e1.download_button("📊 Excel Export", data=output.getvalue(), file_name="Aufmass.xlsx")
    
    pdf_data = generate_pdf(st.session_state.daten)
    e2.download_button("📄 PDF (mit Fotos)", data=pdf_data, file_name="Protokoll.pdf")
    
    if e3.button("⚠️ Liste komplett leeren"):
        st.session_state.daten = []
        st.rerun()
