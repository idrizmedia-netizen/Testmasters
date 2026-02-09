import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="TestMasters Pro Online", page_icon="🎓", layout="centered")

# 2. TELEGRAM VA GOOGLE SHEETS SOZLAMALARI
TELEGRAM_TOKEN = "7713876041:AAHLtJ7F-kGv9p4C8U7A3x-8-U8l9Y8S5U"
CHAT_ID = "@Testmaster_LC" # Sizning kanalingiz
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- TELEGRAMGA NATIJANI YUBORISH FUNKSIYASI ---
def send_to_telegram(name, score, total, percent, subject):
    status = "✅ MUVAFFAQIYATLI" if percent >= 70 else "❌ YAXSHI EMAS"
    msg = (
        f"📊 *YANGI TEST NATIJASI*\n\n"
        f"👤 *O'quvchi:* {name}\n"
        f"📚 *Fan:* {subject}\n"
        f"✅ *To'g'ri:* {score} ta\n"
        f"🏁 *Jami:* {total} ta\n"
        f"📈 *Foiz:* {percent:.1f}%\n"
        f"📝 *Holat:* {status}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        pass

# --- MA'LUMOTLARNI YUKLASH ---
try:
    q_df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    s_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    u_df = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    
    s_df['Parameter'] = s_df['Parameter'].astype(str).str.strip()
    active_sub = str(s_df.loc[s_df['Parameter'] == 'ActiveSubject', 'Value'].values[0]).strip()
    q_df['Fan'] = q_df['Fan'].astype(str).str.strip()
except Exception as e:
    st.error(f"Ma'lumotlar bazasida xatolik: {e}")
    st.stop()

# SESSION STATE
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None
if 'questions' not in st.session_state: st.session_state.questions = None
if 'total_time' not in st.session_state: st.session_state.total_time = 0
if 'start_time' not in st.session_state: st.session_state.start_time = 0

st.title(f"🎓 {active_sub} Fanidan Online Test")

u_name = st.text_input("Ism-familiyangizni kiriting:").strip()

if u_name:
    if u_name in u_df['Ism'].values:
        st.warning("Siz ushbu testni topshirib bo'lgansiz!")
    else:
        if not st.session_state.test_run and st.session_state.final_score is None:
            available_qs = q_df[q_df['Fan'] == active_sub]
            
            if available_qs.empty:
                st.error(f"Hozirda '{active_sub}' fani bo'yicha savollar mavjud emas.")
            else:
                st.info(f"Savollar soni: {len(available_qs.head(30))} ta. Vaqt savollarga ko'ra hisoblanadi.")
                if st.button("🚀 Testni Boshlash"):
                    sample_n = min(len(available_qs), 30)
                    selected_qs = available_qs.sample(n=sample_n)
                    
                    st.session_state.total_time = int(selected_qs['Vaqt'].sum())
                    st.session_state.questions = selected_qs
                    st.session_state.start_time = time.time()
                    st.session_state.test_run = True
                    st.rerun()

        # TEST JARAYONI
        if st.session_state.test_run:
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.total_time - int(elapsed))
            
            m, s = divmod(remaining, 60)
            st.sidebar.markdown(f"## ⏳ Vaqt: {m:02d}:{s:02d}")
            
            if remaining <= 0:
                st.session_state.test_run = False
                st.rerun()
            
            with st.form("quiz_form"):
                u_ans = {}
                for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    u_ans[idx] = st.radio(f"Javobni tanlang:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
                
                if st.form_submit_button("🏁 Testni Yakunlash"):
                    corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    st.session_state.final_score = corrects
                    
                    # Natijani saqlash
                    total = len(st.session_state.questions)
                    percent = (corrects / total) * 100
                    new_u = pd.concat([u_df, pd.DataFrame([{"Ism": u_name}])], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=new_u, worksheet="Users")
                    
                    # Telegramga yuborish
                    send_to_telegram(u_name, corrects, total, percent, active_sub)
                    
                    st.session_state.test_run = False
                    st.rerun()
            
            time.sleep(1) # Taymer yangilanishi uchun
            st.rerun()

# NATIJA KO'RSATISH
if st.session_state.final_score is not None:
    score = st.session_state.final_score
    total = len(st.session_state.questions)
    percent = (score / total) * 100
    
    st.divider()
    st.subheader(f"📊 {u_name}, natijangiz:")
    st.progress(score / total)
    
    c1, c2 = st.columns(2)
    c1.metric("To'g'ri javoblar", f"{score} / {total}")
    c2.metric("Foiz ko'rsatkichi", f"{percent:.1f}%")

    if percent >= 70:
        st.balloons()
        st.success("🔥 Ajoyib natija! Bilimingiz yuqori darajada.")
    else:
        st.warning("💪 Yomon emas. Ko'proq mutolaa qilish tavsiya etiladi.")

    if st.button("🔄 Bosh sahifaga qaytish"):
        st.session_state.final_score = None
        st.session_state.questions = None
        st.rerun()
