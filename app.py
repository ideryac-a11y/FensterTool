import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Profi-Fensteraufmaß v3.8", layout="wide")

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

# --- SEITENLEISTE (EINGABE) ---
with st.sidebar:
    st.header("1. Altmaße")
    pos = st.text_input("Position", "01")
    
    st.subheader("Lichte Breite Innen (mm)")
    b1 = st.number_input("Breite 1", value=1000, min_value=0)
    b2 = st.number_input("Breite 2 (opt.)", value=0, min_value=0)
    b3 = st.number_input("Breite 3 (opt.)", value=0, min_value=0)
    breiten = [b for b in
