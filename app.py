import streamlit as st
import pandas as pd  # Korrigiert: import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Profi-Fensteraufmaß v3.0", layout="wide")

# --- STAMMDATEN ---
LIEFERANTEN_MASSE = [50, 70, 90, 110, 130, 150, 165, 180, 195, 210, 225, 240, 260, 280, 300, 320, 340, 360, 380, 400]
FARBEN_BLECH = ["Silber", "Weiß", "Anthrazit", "Bronze"]
FARBEN_GURT = ["Silber", "Beige", "Weiß"]
GURTWICKLER_MASSE = ["Kein Gurtwickler", "13,8 cm", "16,5 cm", "18,5 cm", "20,5 cm"]

def berechne_bestellmass(rechenwert, liste):
    unterer_wert = 0
    index = 0
    for i, wert in enumerate(liste):
        if wert <= rechenwert:
            unterer_wert = wert
            index = i
        else: 
            break
    if unterer_wert == 0: 
        return liste[0]
    # Wenn Differenz > 5mm, nimm das nächste Maß aus der Liste
    return unterer_wert if (rechenwert - unterer_wert) <= 5 else (liste[index + 1] if index + 1 < len(liste) else liste[-1])

if 'daten' not in st.session_state:
    st.session_state.daten = []

st.title("🏗️ Komplett-System: Fenster, Rollladen & Zubehör")

# --- SEITENLEISTE (EINGABE) ---
with st.sidebar:
    st.header("1. Grundmaße")
    pos = st.text_input("Position", "01")
    m_b_in = st.number_input("Lichte Breite Innen (mm)", value=1000)
    m_b_aus = st.number_input("Lichte Breite Außen (mm)", value=1000)
    m_h = st.number_input("Mauerhöhe (mm)", value=1250)
    laibung = st.number_input("Laibungstiefe (mm)", value=150)
    
    st.markdown("---")
    st.header("2. Technik")
    kasten_typ = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    schiene_t = st.radio("Schienentiefe (mm)", [40, 48])
    profil_t = st.number_input("Profiltiefe Fenster (mm)", value=76)
    kasten_t = st.number_input("Kastentiefe (mm)", value=210)
    
    st.markdown("---")
    st.header("3. Rollladen-Zubehör")
    welle_plus = st.number_input("Welle SW60 Zusatzmaß (mm)", value=0)
    teleskop = st.checkbox("Teleskop-Endstück")
    gurtrolle = st.checkbox("Gurtrolle")
    
    st.markdown("---")
    st.header("4. Gurt & Wickler")
    gurt_bed = st.checkbox("Gurtbedienung?", value=True)
    gurt_wick, gurt_f, v_laenge = "-", "-", "-" # Standardwerte
    if gurt_bed:
        gurt_wick = st.selectbox("Gurtwickler (Lochabstand)", GURTWICKLER_MASSE[1:])
        gurt_f = st.selectbox("Gurtfarbe", FARBEN_GURT, index=0)
        v_laenge = "5 m" if m_h <= 1300 else "6 m"
    
    st.markdown("---")
    st.header("5. Bleche")
    f_blech = st.selectbox("Farbe Blech", FARBEN_BLECH)
    endstueck = st.radio("Endstück", ["Putzendstück", "Gleitendstück"])

    if st.button("💾 Speichern"):
        # BERECHNUNGEN
        br_b = m_b_in - 15
        br_h = (m_h if kasten_typ == "Mit Kasten" else m_h - 7.5)
        pz_b, pz_h = br_b - 35, br_h + 150
        blech_b = m_b_aus + 30
        ausl_bestell = berechne_bestellmass(laibung + 10 + schiene_t + 45, LIEFERANTEN_MASSE)
        deckel_b = m_b_in + 50
        deckel_t = kasten_t - profil_t - schiene_t + 10
        welle_ges = m_b_in + welle_plus

        st.session_state.daten.append({
            "Pos": pos,
            "Fenster (BxH)": f"{br_b}x{br_h}",
            "Panzer (BxH)": f"{pz_b}x{pz_h}",
            "Welle SW60": f"{welle_ges} mm",
            "Blech (BxA)": f"{blech_b}x{ausl_bestell}",
            "Deckel (BxT)": f"{deckel_b}x{deckel_t}",
            "Wickler/Gurt": f"{gurt_wick} / {v_laenge} ({gurt_f})" if gurt_bed else "-",
            "Extras": f"{'Teleskop, ' if teleskop else ''}{'Gurtrolle, ' if gurtrolle else ''}{endstueck}"
        })
        st.success(f"Pos {pos} gespeichert.")

# --- HAUPTBEREICH ---
if st.session_state.daten:
    df = pd.DataFrame(st.session_state.daten)
    st.subheader("Ihre Bestellliste")
    st.dataframe(df, use_container_width=True)

    output = BytesIO()
    # Engine 'xlsxwriter' muss installiert sein (pip install xlsxwriter)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Bestellung')
    
    st.download_button("📊 Excel exportieren", data=output.getvalue(), file_name="Fenster_Bestellung_V3.xlsx")
    
    if st.button("🗑️ Liste leeren"):
        st.session_state.daten = []
        st.rerun()
