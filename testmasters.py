import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import io

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Smart Test Pro", layout="centered")

# 2. Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

# --- 3. MA'LUMOTLARNI YUKLASH ---
try:
    q_df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    s_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    u_df = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    
    s_df['Parameter'] = s_df['Parameter'].astype(str).str.strip()
    active_sub = s_df.loc[s_df['Parameter'] == 'ActiveSubject', 'Value'].values[0]
except:
    st.error("Ma'lumotlar bazasiga ulanishda xato!")
    st.stop()

# Session State elementlarini tekshirish
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None
if 'total_time' not in st.session_state: st.session_state.total_time = 0
if 'start_time' not in st.session_state: st.session_state.start_time = 0
if 'questions' not in st.session_state: st.session_state.questions = None

st.title(f"🏛 {active_sub} fanidan onlayn test")

u_name = st.text_input("Ism-familiyangiz:").strip()

if u_name:
    if u_name in u_df['Ism'].values:
        st.warning("Siz test topshirib bo'lgansiz!")
    else:
        # TESTNI BOSHLASH
        if not st.session_state.test_run and st.session_state.final_score is None:
            if st.button("🚀 Testni boshlash"):
                # Savollarni tanlash
                f_qs = q_df[q_df['Fan'] == active_sub]
                sample_n = min(len(f_qs), 30)
                selected_qs = f_qs.sample(n=sample_n)
                
                # VAQTNI HISOBLASH (Har bir savolning vaqtini qo'shib chiqish)
                total_v = int(selected_qs['Vaqt'].sum()) 
                
                st.session_state.questions = selected_qs
                st.session_state.total_time = total_v
                st.session_state.start_time = time.time()
                st.session_state.test_run = True
                st.rerun()

        # TEST JARAYONI
        if st.session_state.test_run:
            # Taymer mantiqi
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.total_time - int(elapsed))
            
            # Sidebar taymer vizualizatsiyasi
            m, s = divmod(remaining, 60)
            st.sidebar.markdown(f"""
                <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border:2px solid #ff4b4b; text-align:center;">
                    <h1 style="color:#ff4b4b; margin:0;">{m:02d}:{s:02d}</h1>
                    <p style="margin:0;">Qolgan vaqt</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Avtomatik yangilash (Taymer yurishi uchun)
            if remaining > 0:
                time.sleep(1)
                st.rerun()
            else:
                st.error("Vaqt tugadi!")
                st.session_state.test_run = False
                st.rerun()

            # Test formasi
            with st.form("quiz_form"):
                u_ans = {}
                for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    u_ans[idx] = st.radio("Javobni tanlang:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
                
                if st.form_submit_button("🏁 Testni yakunlash"):
                    # Natijani hisoblash
                    corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    st.session_state.final_score = corrects
                    
                    # Google Sheets-ga foydalanuvchini qo'shish
                    new_u = pd.concat([u_df, pd.DataFrame([{"Ism": u_name}])], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=new_u, worksheet="Users")
                    
                    st.session_state.test_run = False
                    st.rerun()

# --- NATIJALARNI KO'RSATISH ---
if st.session_state.final_score is not None:
    score = st.session_state.final_score
    total = len(st.session_state.questions)
    percent = (score / total) * 100
    
    st.markdown(f"## {u_name}, natijangiz: {score} / {total}")
    st.progress(score / total)
    
    if percent >= 70:
        st.balloons()
        st.success(f"Dahshat! Siz {percent:.1f}% ko'rsatkich bilan EKSPERT darajasiga erishdingiz! 🏆")
    else:
        st.info(f"Sizning natijangiz: {percent:.1f}%. Yana biroz harakat qilsangiz, albatta erishasiz! 💪")

    if st.button("🔄 Bosh sahifaga qaytish"):
        st.session_state.final_score = None
        st.session_state.questions = None
        st.rerun()
