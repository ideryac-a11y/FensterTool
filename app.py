import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Profi-Fensteraufmaß v3.3", layout="wide")

# --- STAMMDATEN ---
LIEFERANTEN_MASSE = [50, 70, 90, 110, 130, 150, 165, 180, 195, 210, 225, 240, 260, 280, 300, 320, 340, 360, 380, 400]
FARBEN_BLECH = ["Silber", "Weiß", "Anthrazit", "Bronze"]
FARBEN_GURT = ["Silber", "Beige", "Weiß"]
GURTWICKLER_MASSE = ["Kein Gurtwickler", "13,8 cm", "16,5 cm", "18,5 cm", "20,5 cm"]
PROFILTIEFEN = [70, 76, 80, 82]
FENSTERARTEN = [
    "DKR", 
    "DKL", 
    "Festverglasung", 
    "DKL-DKR", 
    "D-DKR", 
    "DKL-D", 
    "Fest-DKR", 
    "DKL-Fest"
]

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

if 'daten' not in st.session_state:
    st.session_state.daten = []

st.title("🏗️ Profi-Aufmaß: Fenster & Rollladen")

# --- SEITENLEISTE (EINGABE) ---
with st.sidebar:
    st.header("1. Altmaße")
    pos = st.text_input("Position", "01")
    m_b_in = st.number_input("Lichte Breite Innen (mm)", value=1000)
    m_b_aus = st.number_input("Lichte Breite Außen (mm)", value=1000)
    m_h_in = st.number_input("Lichte Höhe Innen (mm)", value=1250)
    laibung = st.number_input("Laibungstiefe (mm)", value=150)
    d_tiefe_alt = st.number_input("Deckeltiefe alt (mm)", value=140)
    b_tiefe_alt = st.number_input("Bautiefe alt (mm)", value=70)
    
    st.markdown("---")
    st.header("2. Technik (Neu)")
    f_art = st.selectbox("Fensterart", FENSTERARTEN)
    kasten_typ = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    schiene_t = st.radio("Schienentiefe (mm)", [40, 48])
    profil_t = st.selectbox("Profiltiefe Fenster (mm)", PROFILTIEFEN)
    
    st.markdown("---")
    st.header("3. Rollladen-Zubehör")
    welle_plus = st.number_input("Welle SW60 Zusatzmaß (mm)", value=0)
    teleskop = st.checkbox("Teleskop-Endstück")
    gurtrolle = st.checkbox("Gurtrolle")
    
    st.markdown("---")
    st.header("4. Gurt & Wickler")
    gurt_bed = st.checkbox("Gurtbedienung?", value=True)
    gurt_wick, gurt_f, v_laenge = "-", "-", "-"
    if gurt_bed:
        gurt_wick = st.selectbox("Gurtwickler (Lochabstand)", GURTWICKLER_MASSE[1:])
        gurt_f = st.selectbox("Gurtfarbe", FARBEN_GURT, index=0)
        v_laenge = "5 m" if m_h_in <= 1300 else "6 m"
    
    st.markdown("---")
    st.header("5. Bleche")
    f_blech = st.selectbox("Farbe Blech", FARBEN_BLECH)
    endstueck = st.radio("Endstück", ["Putzendstück", "Gleitendstück"])

    if st.button("💾 Pos. Speichern"):
        # --- BERECHNUNGSLOGIK ---
        kastentiefe = d_tiefe_alt + b_tiefe_alt
        bautiefe_neu = profil_t + schiene_t
        deckeltiefe_neu = kastentiefe - bautiefe_neu + 10
        
        br_b = m_b_in - 15
        br_h = (m_h_in if kasten_typ == "Mit Kasten" else m_h_in - 7.5)
        pz_b, pz_h = br_b - 35, br_h + 150
        blech_b = m_b_aus + 30
        ausl_bestell = berechne_bestellmass(laibung + 10 + schiene_t + 45, LIEFERANTEN_MASSE)
        deckel_b = m_b_in + 50
        welle_ges = m_b_in + welle_plus

        st.session_state.daten.append({
            "Pos": pos,
            "Fensterart": f_art,
            "Fenster (BxH)": f"{br_b}x{br_h}",
            "Bautiefe Neu": f"{bautiefe_neu} mm",
            "Deckel Neu (BxT)": f"{deckel_b}x{deckeltiefe_neu}",
            "Kastentiefe": f"{kastentiefe} mm",
            "Panzer (BxH)": f"{pz_b}x{pz_h}",
            "Welle SW60": f"{welle_ges} mm",
            "Blech (BxA)": f"{blech_b}x{ausl_bestell}",
            "Wickler/Gurt": f"{gurt_wick} / {v_laenge} ({gurt_f})" if gurt_bed else "-",
            "Extras": f"{'Teleskop, ' if teleskop else ''}{'Gurtrolle, ' if gurtrolle else ''}{endstueck}"
        })
        st.success(f"Position {pos} ({f_art}) gespeichert!")

# --- HAUPTBEREICH ---
if st.session_state.daten:
    df = pd.DataFrame(st.session_state.daten)
    st.subheader("Aktuelle Bestellliste")
    st.dataframe(df, use_container_width=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Bestellung')
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📊 Excel exportieren", data=output.getvalue(), file_name="Fenster_Bestellung_V3_3.xlsx")
    with col2:
        if st.button("🗑️ Gesamte Liste leeren"):
            st.session_state.daten = []
            st.rerun()
