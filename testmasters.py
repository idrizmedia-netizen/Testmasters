import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Smart Test System", layout="centered")

# 2. Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

# --- 3. MA'LUMOTLARNI YUKLASH ---
try:
    q_df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    s_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    u_df = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    
    # Sozlamalarni o'qish
    s_df['Parameter'] = s_df['Parameter'].str.strip()
    active_sub = s_df.loc[s_df['Parameter'] == 'ActiveSubject', 'Value'].values[0]
    # Google Sheets-dan vaqtni olish (masalan: 15)
    test_duration_min = int(s_df.loc[s_df['Parameter'] == 'TestDuration', 'Value'].values[0])
except:
    st.error("Google Sheets ma'lumotlarida xatolik! 'TestDuration' parametri borligini tekshiring.")
    st.stop()

if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None

st.title(f"🚀 {active_sub} Fanidan Bilim Sinovi")

u_name = st.text_input("Ism-familiyangiz:").strip()

if u_name:
    if u_name in u_df['Ism'].values:
        st.warning("Siz test topshirib bo'lgansiz!")
    else:
        if not st.session_state.test_run and st.session_state.final_score is None:
            st.info(f"Test davomiyligi: {test_duration_min} daqiqa. Omad!")
            if st.button("🚀 Testni boshlash"):
                st.session_state.test_run = True
                st.session_state.start_time = time.time()
                st.rerun()

        if st.session_state.test_run:
            # Jonli Taymer
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, test_duration_min * 60 - int(elapsed))
            
            m, s = divmod(remaining, 60)
            st.sidebar.metric("⏳ Qolgan vaqt", f"{m:02d}:{s:02d}")
            
            if remaining == 0:
                st.error("Vaqt tugadi!")
                st.session_state.test_run = False
                st.rerun()

            with st.form("quiz_form"):
                f_qs = q_df[q_df['Fan'] == active_sub].sample(n=30)
                u_ans = {}
                for i, (idx, row) in enumerate(f_qs.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    u_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
                
                if st.form_submit_button("🏁 Yakunlash"):
                    # Natijani hisoblash
                    corrects = sum(1 for idx, row in f_qs.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    st.session_state.final_score = corrects
                    
                    # Bazaga saqlash
                    new_u = pd.concat([u_df, pd.DataFrame([{"Ism": u_name}])], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=new_u, worksheet="Users")
                    
                    st.session_state.test_run = False
                    st.rerun()

# --- 4. QIYINLIK DARAJASI BO'YICHA NATIJA ---
if st.session_state.final_score is not None:
    score = st.session_state.final_score
    percent = (score / 30) * 100
    
    st.success(f"### Natijangiz: {score} / 30")
    
    # Qiyinlik darajasi shkalasi
    if percent < 40:
        level = "🔴 BOSHLANG'ICH (O'qishingiz kerak)"
        color = "red"
    elif percent < 70:
        level = "🟡 O'RTA (Yaxshi, lekin harakat qiling)"
        color = "orange"
    elif percent < 90:
        level = "🟢 YUQORI (Juda yaxshi natija!)"
        color = "green"
    else:
        level = "💎 EKSPERT (Mukammal bilim!)"
        color = "blue"

    st.markdown(f"#### Bilim darajangiz: :{color}[{level}]")
    st.progress(score / 30)

    # Vizual xarita
    

    if st.button("🔄 Bosh sahifaga qaytish"):
        st.session_state.final_score = None
        st.rerun()
