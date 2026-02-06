import streamlit as st
import pandas as pd
import time

# Sahifa sozlamalari
st.set_page_config(page_title="Testmasters", page_icon="🎓")

# 1. Savollar bazasi (30 ta savol)
if 'questions' not in st.session_state:
    st.session_state.questions = [
        # OSON (10s)
        {"q": "Tezlik birligi nima?", "a": "m/s", "o": ["m/s", "kg", "J", "N"], "level": "oson"},
        {"q": "Kuch birligi nima?", "a": "Nyuton", "o": ["Vatt", "Nyuton", "Paskal", "Kulon"], "level": "oson"},
        {"q": "Zichlik formulasi qaysi?", "a": "ρ = m/V", "o": ["ρ = m/V", "F = ma", "P = F/S", "E = mc2"], "level": "oson"},
        {"q": "Bosim birligi nima?", "a": "Paskal", "o": ["Joul", "Vatt", "Paskal", "Gerts"], "level": "oson"},
        {"q": "Vaqt birligi nima?", "a": "sekund", "o": ["metr", "sekund", "kilogram", "amper"], "level": "oson"},
        {"q": "Massa birligi nima?", "a": "kg", "o": ["kg", "N", "m", "s"], "level": "oson"},
        {"q": "Energiya birligi nima?", "a": "Joul", "o": ["Vatt", "Joul", "Paskal", "Nyuton"], "level": "oson"},
        {"q": "Kuchlanish nima bilan o'lchanadi?", "a": "Voltmetr", "o": ["Ampermetr", "Voltmetr", "Ommetr", "Vattmetr"], "level": "oson"},
        {"q": "Tok kuchi birligi nima?", "a": "Amper", "o": ["Volt", "Om", "Amper", "Vatt"], "level": "oson"},
        {"q": "Issiqlik miqdori birligi nima?", "a": "Joul", "o": ["Kelvin", "Selsiy", "Joul", "Kaloriya"], "level": "oson"},
        # O'RTA (20s)
        {"q": "Nyutonning ikkinchi qonuni?", "a": "F=ma", "o": ["F=ma", "a=v/t", "E=mgh", "P=mv"], "level": "o'rta"},
        {"q": "Erkin tushish tezlanishi (g)?", "a": "9.8 m/s²", "o": ["10.5 m/s²", "9.8 m/s²", "8.9 m/s²", "7.5 m/s²"], "level": "o'rta"},
        {"q": "Ishning formulasi?", "a": "A = F·s", "o": ["A = F·s", "A = P/t", "A = mgh", "A = F/v"], "level": "o'rta"},
        {"q": "Guk qonuni formulasi?", "a": "F = kx", "o": ["F = ma", "F = kx", "F = mg", "F = qE"], "level": "o'rta"},
        {"q": "Impuls formulasi?", "a": "p = mv", "o": ["p = mv", "p = m/v", "p = F·t", "p = mgh"], "level": "o'rta"},
        {"q": "Quvvat formulasi?", "a": "N = A/t", "o": ["N = A·t", "N = A/t", "N = F·s", "N = mgh"], "level": "o'rta"},
        {"q": "Kinetik energiya?", "a": "Ek = mv²/2", "o": ["Ek = mgh", "Ek = mv²/2", "Ek = Fs", "Ek = pv"], "level": "o'rta"},
        {"q": "Potensial energiya?", "a": "Ep = mgh", "o": ["Ep = mgh", "Ep = mv²/2", "Ep = kx²/2", "Ep = Fs"], "level": "o'rta"},
        {"q": "Om qonuni formulasi?", "a": "I = U/R", "o": ["U = I/R", "I = U/R", "R = UI", "P = UI"], "level": "o'rta"},
        {"q": "Elektr sig'imi birligi?", "a": "Farada", "o": ["Genri", "Farada", "Tesla", "Veber"], "level": "o'rta"},
        # QIYIN (30s)
        {"q": "Lorens kuchi?", "a": "F = qvBsinα", "o": ["F = BILsinα", "F = qvBsinα", "F = ma", "F = kx"], "level": "qiyin"},
        {"q": "Eynshteyn formulasi?", "a": "E = mc²", "o": ["E = hf", "E = mc²", "E = mgh", "E = kx²/2"], "level": "qiyin"},
        {"q": "Ideal gaz holati?", "a": "PV = nRT", "o": ["P = F/S", "PV = nRT", "V = IR", "F = Gmm/r²"], "level": "qiyin"},
        {"q": "Yorug'lik tezligi?", "a": "3·10⁸ m/s", "o": ["3·10⁵ m/s", "3·10⁸ m/s", "340 m/s", "1500 m/s"], "level": "qiyin"},
        {"q": "Gidrostatik bosim?", "a": "p = ρgh", "o": ["p = F/S", "p = ρgh", "p = mv", "p = A/t"], "level": "qiyin"},
        {"q": "Koulomb qonuni?", "a": "F = kq₁q₂/r²", "o": ["F = mg", "F = Gmm/r²", "F = kq₁q₂/r²", "F = qE"], "level": "qiyin"},
        {"q": "Foton energiyasi?", "a": "E = hf", "o": ["E = mc²", "E = hf", "E = hλ", "E = p²/2m"], "level": "qiyin"},
        {"q": "Magnit oqimi birligi?", "a": "Veber", "o": ["Tesla", "Veber", "Genri", "Lyuks"], "level": "qiyin"},
        {"q": "Induktivlik birligi?", "a": "Genri", "o": ["Tesla", "Veber", "Genri", "Farada"], "level": "qiyin"},
        {"q": "Bosh kvant soni nimani bildiradi?", "a": "Qobiq o'lchamini", "o": ["Spinni", "Orbitalni", "Qobiq o'lchamini", "Magnitni"], "level": "qiyin"}
    ]

if 'results' not in st.session_state: st.session_state.results = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'score' not in st.session_state: st.session_state.score = 0

# --- ADMIN PANEL ---
with st.sidebar:
    st.title("⚙️ Admin")
    pw = st.text_input("Parol:", type="password")
    if pw == "1234":
        st.write("📊 Natijalar:")
        st.table(pd.DataFrame(st.session_state.results))

# --- TEST ---
st.title("⚛️ Testmasters: Fizika")

if st.session_state.idx < len(st.session_state.questions):
    q = st.session_state.questions[st.session_state.idx]
    st.subheader(f"Savol {st.session_state.idx + 1} / 30")
    st.write(f"### {q['q']}")
    ans = st.radio("Javoblar:", q['o'], key=f"q_{st.session_state.idx}")
    
    if st.button("Keyingi ➡️"):
        if ans == q['a']: st.session_state.score += 1
        st.session_state.idx += 1
        st.rerun()
else:
    st.success(f"Tugadi! Ball: {st.session_state.score}/30")
    name = st.text_input("Ismingiz:")
    if st.button("Saqlash"):
        st.session_state.results.append({"Ism": name, "Ball": st.session_state.score})
        st.write("Saqlandi!")
