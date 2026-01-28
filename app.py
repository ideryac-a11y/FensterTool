import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Profi-Aufmaß v5.8", layout="wide")

# --- HILFSFUNKTIONEN ---
def runden_auf_5(zahl):
    return 5 * round(zahl / 5)

def generate_pdf(daten):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Aufmaß- und Montageprotokoll", ln=True, align='C')
    pdf.ln(10)
    
    for entry in daten:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, txt=f"Position: {entry['Pos']} - {entry['Art']}", ln=True, fill=False)
        
        pdf.set_font("Arial", "", 10)
        info_text = (f"Maße: {entry['Fenster-Maß']} mm | Glas: {entry['Glas']} | "
                     f"Deckel: {entry['Deckel Neu']} mm\n"
                     f"Schienen: {entry['Schienen']} | Traverse: {entry['Traverse']}\n"
                     f"Bemerkung: {entry['Bemerkung']}")
        pdf.multi_cell(0, 5, txt=info_text)
        
        if entry["Foto"]:
            # Temporäres Speichern des Bildes für das PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                # Bild konvertieren und skalieren für PDF
                img = entry["Foto"].convert("RGB")
                img.save(tmpfile.name, format="JPEG", quality=75)
                # Bild im PDF platzieren (x, y, w)
                pdf.image(tmpfile.name, x=10, w=80)
                os.unlink(tmpfile.name) # Temp-Datei löschen
        
        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INITIALISIERUNG ---
if 'daten' not in st.session_state:
    st.session_state.daten = []

st.title("📸 Profi-Aufmaß: PDF & Foto")

# --- SEITENLEISTE ---
with st.sidebar:
    st.header("Dateneingabe")
    pos = st.text_input("Position", f"{len(st.session_state.daten) + 1:02d}")
    foto = st.camera_input("Foto aufnehmen")
    
    b_avg = st.number_input("Ø Breite (mm)", value=1000)
    h_avg = st.number_input("Ø Höhe (mm)", value=1250)
    dt_avg = st.number_input("Ø Deckeltiefe alt (mm)", value=140)
    bt_alt = st.number_input("Bautiefe alt (mm)", value=70)
    
    f_art = st.selectbox("Fensterart", ["DKR", "DKL", "Fest", "DKL-DKR"])
    v_fach = st.selectbox("Verglasung", ["2-fach", "3-fach"], index=1)
    kasten = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    profil = st.selectbox("Profiltiefe (mm)", [70, 76, 82])
    
    bemerkung = st.text_area("Bemerkung")

    if st.button("💾 Speichern"):
        br_b = b_avg - 12
        br_h = h_avg if kasten == "Mit Kasten" else h_avg - 6
        kastentiefe = dt_avg + bt_alt
        deckel_neu = runden_auf_5(kastentiefe - (profil + (40 if kasten=="Mit Kasten" else 0)) + 10)
        
        st.session_state.daten.append({
            "Pos": pos,
            "Foto": Image.open(foto) if foto else None,
            "Art": f_art,
            "Glas": v_fach,
            "Fenster-Maß": f"{br_b:.1f}x{br_h:.1f}",
            "Deckel Neu": f"{b_avg+50}x{deckel_neu}",
            "Schienen": "Ja" if kasten == "Mit Kasten" else "Nein",
            "Traverse": "Ja" if kasten == "Mit Kasten" else "Nein",
            "Bemerkung": bemerkung
        })
        st.success("Gespeichert!")

# --- HAUPTBEREICH ---
if st.session_state.daten:
    # PDF Button
    pdf_bytes = generate_pdf(st.session_state.daten)
    st.download_button(
        label="📄 PDF-Protokoll generieren",
        data=pdf_bytes,
        file_name="Aufmassprotokoll.pdf",
        mime="application/pdf"
    )
    
    # Vorschau-Tabelle
    for i, d in enumerate(st.session_state.daten):
        with st.expander(f"Pos {d['Pos']} - {d['Art']}", expanded=True):
            col1, col2 = st.columns([1, 2])
            if d["Foto"]: col1.image(d["Foto"], width=200)
            col2.write(f"**Maß:** {d['Fenster-Maß']} | **Deckel:** {d['Deckel Neu']}")
            col2.write(f"**Bemerkung:** {d['Bemerkung']}")
            if st.button(f"Löschen {i}", key=f"del_{i}"):
                st.session_state.daten.pop(i)
                st.rerun()

    # Excel Export (wie bisher)
    df_export = pd.DataFrame(st.session_state.daten).drop(columns=["Foto"])
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False)
    st.download_button("📊 Excel laden", data=buffer.getvalue(), file_name="Aufmass.xlsx")
