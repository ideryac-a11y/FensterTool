import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Profi-Fensteraufmaß v3.9", layout="wide")

# --- STAMMDATEN ---
LIEFERANTEN_MASSE = [50, 70, 90, 110, 130, 150, 165, 180, 195, 210, 225, 240, 260, 280, 300, 320, 340, 360, 380, 400]
FARBEN_BLECH = ["Silber", "Weiß", "Anthrazit", "Bronze"]
FARBEN_GURT = ["Silber", "Beige", "Weiß"]
GURTWICKLER_MASSE = ["Kein Gurtwickler", "13,8 cm", "16,5 cm", "18,5 cm", "20,5 cm"]
PROFILTIEFEN = [70, 76, 80, 82]
FENSTERARTEN = ["DKR", "DKL", "Festverglasung", "DKL-DKR", "D-DKR", "DKL-D", "Fest-DKR", "DKL-Fest"]

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

with st.sidebar:
    st.header("1. Altmaße")
    pos = st.text_input("Position", "01")
    
    st.subheader("Lichte Breite Innen (mm)")
    b1 = st.number_input("Breite 1", value=1000, min_value=0)
    b2 = st.number_input("Breite 2 (opt.)", value=0, min_value=0)
    b3 = st.number_input("Breite 3 (opt.)", value=0, min_value=0)
    breiten_liste = [b for b in [b1, b2, b3] if b > 0]
    m_b_in_avg = sum(breiten_liste) / len(breiten_liste) if breiten_liste else 0
    st.caption(f"Ø Breite: {m_b_in_avg:.1f} mm")

    st.subheader("Lichte Höhe Innen (mm)")
    h1 = st.number_input("Höhe 1", value=1250, min_value=0)
    h2 = st.number_input("Höhe 2 (opt.)", value=0, min_value=0)
    h3 = st.number_input("Höhe 3 (opt.)", value=0, min_value=0)
    hoehen_liste = [h for h in [h1, h2, h3] if h > 0]
    m_h_in_avg = sum(hoehen_liste) / len(hoehen_liste) if hoehen_liste else 0
    st.caption(f"Ø Höhe: {m_h_in_avg:.1f} mm")
    
    st.markdown("---")
    st.subheader("Deckeltiefe alt (mm)")
    dt1 = st.number_input("Deckeltiefe 1", value=140, min_value=0)
    dt2 = st.number_input("Deckeltiefe 2 (opt.)", value=0, min_value=0)
    d_tiefen_liste = [dt for dt in [dt1, dt2] if dt > 0]
    d_tiefe_alt_avg = sum(d_tiefen_liste) / len(d_tiefen_liste) if d_tiefen_liste else 0
    st.caption(f"Ø Deckeltiefe: {d_tiefe_alt_avg:.1f} mm")

    b_tiefe_alt = st.number_input("Bautiefe alt (mm)", value=70)
    m_b_aus = st.number_input("Lichte Breite Außen (mm)", value=1000)
    laibung = st.number_input("Laibungstiefe (mm)", value=150)
    
    st.markdown("---")
    st.header("2. Technik (Neu)")
    f_art = st.selectbox("Fensterart", FENSTERARTEN)
    kasten_typ = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    schiene_t = st.radio("Schienentiefe (mm)", [40, 48])
    profil_t = st.selectbox("Profiltiefe Fenster (mm)", PROFILTIEFEN)
    
    st.markdown("---")
    st.header("3. Rollladen-Zubehör")
    welle_benoetigt = st.checkbox("Welle SW60 benötigt?", value=True)
    welle_plus = st.number_input("Welle SW60 Zusatzmaß (mm)", value=0) if welle_benoetigt else 0
    teleskop = st.checkbox("Teleskop-Endstück")
    gurtrolle = st.checkbox("Gurtrolle")
    zubehoer_frei = st.text_input("Sonstiges Zubehör (Freitext)", "")
    
    st.markdown("---")
    st.header("4. Gurt & Wickler")
    gurt_bed = st.checkbox("Gurtbedienung?", value=True)
    gurt_wick, gurt_f, v_laenge = "-", "-", "-"
    if gurt_bed:
        gurt_wick = st.selectbox("Gurtwickler (Lochabstand)", GURTWICKLER_MASSE[1:])
        gurt_f = st.selectbox("Gurtfarbe", FARBEN_GURT, index=0)
        v_laenge = "5 m" if m_h_in_avg <= 1300 else "6 m"
    
    st.markdown("---")
    st.header("5. Bleche")
    f_blech = st.selectbox("Farbe Blech", FARBEN_BLECH)
    endstueck = st.radio("Endstück", ["Putzendstück", "Gleitendstück"])

    if st.button("💾 Pos. Speichern"):
        kastentiefe = d_tiefe_alt_avg + b_tiefe_alt
        bautiefe_neu = profil_t + schiene_t
        deckeltiefe_neu = kastentiefe - bautiefe_neu + 10
        br_b = m_b_in_avg - 15
        br_h = (m_h_in_avg if kasten_typ == "Mit Kasten" else m_h_in_avg - 7.5)
        pz_b, pz_h = br_b - 35, br_h + 150
        blech_b = m_b_aus + 30
        ausl_bestell = berechne_bestellmass(laibung + 10 + schiene_t + 45, LIEFERANTEN_MASSE)
        deckel_b = m_b_in_avg + 50
        welle_text = f"{m_b_in_avg + welle_plus:.1f} mm" if welle_benoetigt else "-"
        
        extras = [endstueck]
        if teleskop: extras.append("Teleskop")
        if gurtrolle: extras.append("Gurtrolle")
        if zubehoer_frei: extras.append(zubehoer_frei)
        
        st.session_state.daten.append({
            "Pos": pos, "Fensterart": f_art, "Ø Maße": f"{m_b_in_avg:.1f}x{m_h_in_avg:.1f}",
            "Fenster (BxH)": f"{br_b:.1f}x{br_h:.1f}", "Kastentiefe": f"{kastentiefe:.1f}",
            "Deckel Neu": f"{deckel_b:.1f}x{deckeltiefe_neu:.1f}", "Bautiefe Neu": bautiefe_neu,
            "Panzer": f"{pz_b:.1f}x{pz_h:.1f}", "Welle": welle_text, "Blech": f"{blech_b}x{ausl_bestell}",
            "Wickler/Gurt": f"{gurt_wick}/{v_laenge} ({gurt_f})" if gurt_bed else "-", "Extras": ", ".join(extras)
        })
        st.success(f"Position {pos} gespeichert.")

if st.session_state.daten:
    df = pd.DataFrame(st
