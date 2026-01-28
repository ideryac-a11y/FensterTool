import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Profi-Fensteraufmaß v4.0", layout="wide")

# --- Lade-Funktionen & Stammdaten ---
L_MASSE = [50, 70, 90, 110, 130, 150, 165, 180, 195, 210, 225, 240, 260, 280, 300, 320, 340, 360, 380, 400]
PROFILTIEFEN = [70, 76, 80, 82]
FENSTERARTEN = ["DKR", "DKL", "Festverglasung", "DKL-DKR", "D-DKR", "DKL-D", "Fest-DKR", "DKL-Fest"]

def hole_bestell_blech(wert, liste):
    unter = 0
    idx = 0
    for i, w in enumerate(liste):
        if w <= wert:
            unter = w
            idx = i
        else: break
    if unter == 0: return liste[0]
    return unter if (wert - unter) <= 5 else (liste[idx + 1] if idx + 1 < len(liste) else liste[-1])

if 'daten' not in st.session_state:
    st.session_state.daten = []

st.title("🏗️ Profi-Aufmaß: Fenster & Rollladen")

with st.sidebar:
    st.header("1. Altmaße")
    pos = st.text_input("Position", "01")
    
    b1 = st.number_input("Breite 1 (mm)", value=1000)
    b2 = st.number_input("Breite 2 (mm)", value=0)
    b3 = st.number_input("Breite 3 (mm)", value=0)
    bl = [x for x in [b1, b2, b3] if x > 0]
    avg_b = sum(bl)/len(bl) if bl else 0
    
    h1 = st.number_input("Höhe 1 (mm)", value=1250)
    h2 = st.number_input("Höhe 2 (mm)", value=0)
    h3 = st.number_input("Höhe 3 (mm)", value=0)
    hl = [x for x in [h1, h2, h3] if x > 0]
    avg_h = sum(hl)/len(hl) if hl else 0
    st.caption(f"Ø Maß: {avg_b:.1f} x {avg_h:.1f}")

    dt1 = st.number_input("Deckeltiefe 1", value=140)
    dt2 = st.number_input("Deckeltiefe 2", value=0)
    dl = [x for x in [dt1, dt2] if x > 0]
    avg_dt = sum(dl)/len(dl) if dl else 0
    
    bau_alt = st.number_input("Bautiefe alt", value=70)
    b_aus = st.number_input("Lichte Breite Außen", value=1000)
    laibung = st.number_input("Laibungstiefe", value=150)

    st.header("2. Technik")
    f_art = st.selectbox("Fensterart", FENSTERARTEN)
    kasten = st.radio("Ausführung", ["Mit Kasten", "Ohne Kasten"])
    schiene = st.radio("Schienentiefe", [40, 48])
    prof = st.selectbox("Profiltiefe", PROFILTIEFEN)
    
    st.header("3. Zubehör")
    w_ja = st.checkbox("Welle SW60?", value=True)
    w_plus = st.number_input("Welle Zusatzmaß", value=0) if w_ja else 0
    frei = st.text_input("Zubehör Freitext", "")
    
    st.header("4. Gurt")
    g_ja = st.checkbox("Gurtbedienung?", value=True)
    g_wick, g_f, g_l = "-", "-", "-"
    if g_ja:
        g_wick = st.selectbox("Wickler", ["13,8 cm", "16,5 cm", "18,5 cm", "20,5 cm"])
        g_f = st.selectbox("Gurtfarbe", ["Silber", "Beige", "Weiß"])
        g_l = "5 m" if avg_h <= 1300 else "6 m"

    if st.button("💾 Speichern"):
        kt = avg_dt + bau_alt
        b_neu = prof + schiene
        d_neu_t = kt - b_neu + 10
        f_b, f_h = avg_b - 15, (avg_h if kasten == "Mit Kasten" else avg_h - 7.5)
        p_b, p_h = f_b - 35, f_h + 150
        bl_b = b_aus + 30
        bl_a = hole_bestell_blech(laibung + 10 + schiene + 45, L_MASSE)
        w_t = f"{avg_b + w_plus:.1f}" if w_ja else "-"
        
        st.session_state.daten.append({
            "Pos": pos, "Art": f_art, "Ø Alt": f"{avg_b:.0f}x{avg_h:.0f}",
            "Fenster": f"{f_b:.1f}x{f_h:.1f}", "Kastent.": f"{kt:.1f}",
            "Deckel Neu": f"{avg_b+50:.1f}x{d_neu_t:.1f}", "Bau Neu": b_neu,
            "Panzer": f"{p_b:.0f}x{p_h:.0f}", "Welle": w_t, "Blech": f"{bl_b}x{bl_a}",
            "Gurt": f"{g_wick}/{g_l}" if g_ja else "-", "Extras": frei
        })
        st.success("Gespeichert!")

if st.session_state.daten:
    df = pd.DataFrame(st.session_state.daten)
    st.dataframe(df, use_container_width=True)
    
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df.to_excel(wr, index=False)
    
    c1, c2 = st.columns(2)
    with c1: st.download_button("Excel laden", out.getvalue(), "Aufmass.xlsx")
    with c2: 
        if st.button("Liste leeren"):
            st.session_state.daten = []
            st.rerun()
