import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="TestMasters Pro", page_icon="🎓", layout="centered")

# 2. SOZLAMALAR (TOKEN VA KANAL)
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmaster_LC" 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- TELEGRAM FUNKSIYASI ---
def send_to_telegram(name, score, total, percent, subject):
    status = "✅ O'TDI" if percent >= 70 else "❌ O'TMADI"
    msg = (
        f"📊 *TEST YAKUNLANDI*\n\n"
        f"👤 *O'quvchi:* {name}\n"
        f"📚 *Fan:* {subject}\n"
        f"✅ *Natija:* {score}/{total} ({percent:.1f}%)\n"
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
    
    existing_users = u_df['Ism'].astype(str).str.strip().tolist()
except:
    st.error("Ma'lumotlar bazasi bilan ulanishda xato yuz berdi!")
    st.stop()

# SESSION STATE
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None

st.title(f"🏛 {active_sub} Imtihon Platformasi")

# 3. KIRISH VA TEKSHIRUV
u_name = st.text_input("To'liq ism-familiyangizni kiriting:").strip()

if u_name:
    if u_name in existing_users:
        st.error(f"🛑 {u_name}, siz ushbu testni topshirib bo'lgansiz. Qayta urinish taqiqlanadi!")
    else:
        if not st.session_state.test_run and st.session_state.final_score is None:
            available_qs = q_df[q_df['Fan'] == active_sub]
            if not available_qs.empty:
                st.info(f"Testga xush kelibsiz! Savollar soni: {min(len(available_qs), 30)} ta.")
                if st.button("🚀 Imtihonni boshlash"):
                    sample_n = min(len(available_qs), 30)
                    st.session_state.questions = available_qs.sample(n=sample_n)
                    st.session_state.total_time = int(st.session_state.questions['Vaqt'].sum())
                    st.session_state.start_time = time.time()
                    st.session_state.test_run = True
                    st.rerun()

        # TEST JARAYONI
        if st.session_state.test_run:
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.total_time - int(elapsed))
            m, s = divmod(remaining, 60)
            
            # DOIMIY TEPADA TURUVCHI TAYMER
            st.markdown(f"""
                <div style="position: fixed; top: 10px; right: 10px; background-color: #1E1E1E; color: #FF4B4B; 
                padding: 10px 20px; border-radius: 10px; font-size: 24px; font-weight: bold; z-index: 1000; border: 2px solid #FF4B4B;">
                    ⏳ {m:02d}:{s:02d}
                </div>
            """, unsafe_allow_html=True)
            
            if remaining <= 0:
                st.session_state.test_run = False
                st.rerun()
            
            with st.form("quiz_form"):
                u_ans = {}
                for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    u_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
                
                if st.form_submit_button("🏁 Testni yakunlash"):
                    corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    st.session_state.final_score = corrects
                    total = len(st.session_state.questions)
                    percent = (corrects / total) * 100
                    
                    # Google Sheets yangilash (Bloklash uchun)
                    new_user_row = pd.DataFrame([{"Ism": u_name}])
                    updated_df = pd.concat([u_df, new_user_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated_df, worksheet="Users")
                    
                    # Telegramga yuborish
                    send_to_telegram(u_name, corrects, total, percent, active_sub)
                    
                    st.session_state.test_run = False
                    st.rerun()
            
            time.sleep(1)
            st.rerun()

# NATIJA EKRANI
if st.session_state.final_score is not None:
    score = st.session_state.final_score
    total = len(st.session_state.questions)
    
    st.success(f"### Imtihon yakunlandi! Sizning natijangiz: {score} / {total}")
    
    st.markdown("---")
    st.markdown("#### 📢 Natijalar va yangiliklarni kanalda kuzatib boring:")
    st.link_button("🔗 Testmaster_LC kanaliga o'tish", "https://t.me/Testmasters_LC")
    
    st.info("⚠️ Natijangiz kanalda e'lon qilindi. Qayta topshirish imkoniyati mavjud emas.")
