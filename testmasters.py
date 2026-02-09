import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Test Masters Pro", layout="centered")

# 2. Ulanish
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit"

st.title("🎓 Smart Test Masters")

# 3. Savollarni yuklash
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions", ttl=0)
        return df
    except Exception as e:
        st.error(f"Jadval o'qilmadi: {e}")
        return pd.DataFrame()

all_q = load_questions()

if not all_q.empty:
    name = st.text_input("F.I.SH kiriting:")
    subjects = all_q['Fan'].unique()
    subject = st.selectbox("Fanni tanlang:", subjects)

    if name and subject:
        # Savollarni bir marta yuklash va aralashtirish
        if 'test_data' not in st.session_state or st.session_state.get('last_sub') != subject:
            filtered = all_q[all_q['Fan'] == subject].sample(frac=1)
            st.session_state.test_data = filtered
            st.session_state.last_sub = subject
            st.session_state.start_time = time.time()

        q_df = st.session_state.test_data

        # --- TAYMER (5 daqiqa) ---
        time_limit = 300 
        elapsed = time.time() - st.session_state.start_time
        remaining = int(time_limit - elapsed)

        if remaining > 0:
            st.sidebar.metric("⏳ Qolgan vaqt", f"{remaining // 60}:{remaining % 60:02d}")
            
            # Har 5 soniyada taymerni yangilash
            if remaining % 5 == 0:
                time.sleep(1)
                st.rerun()

            with st.form("test_form"):
                score = 0
                for i, row in q_df.iterrows():
                    st.write(f"### {i+1}-savol: {row['Savol']}")
                    
                    # Variantlarni A, B, C, D formatida ko'rsatish
                    options = {
                        f"A) {row['A']}": row['A'],
                        f"B) {row['B']}": row['B'],
                        f"C) {row['C']}": row['C'],
                        f"D) {row['D']}": row['D']
                    }
                    
                    # Foydalanuvchi tanlovi
                    user_choice_label = st.radio(
                        "Javobni tanlang:", 
                        options.keys(), 
                        key=f"q_{i}", 
                        index=None
                    )
                    
                    # To'g'ri javobni tekshirish
                    if user_choice_label:
                        actual_answer = options[user_choice_label]
                        if str(actual_answer).strip() == str(row['Javob']).strip():
                            score += 1
                
                submitted = st.form_submit_button("Testni yakunlash va natijani yuborish")
                
                if submitted:
                    try:
                        # Natijani Sheet1 ga saqlash
                        res = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/{len(q_df)}"}])
                        old_res = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
                        updated = pd.concat([old_res, res], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, data=updated, worksheet="Sheet1")
                        
                        st.success(f"Tabriklaymiz {name}! Natijangiz saqlandi: {score} ball")
                        st.balloons()
                        
                        # Sessiyani tozalash
                        for key in ['test_data', 'start_time', 'last_sub']:
                            st.session_state.pop(key, None)
                    except Exception as e:
                        st.error(f"Natijani saqlashda xato: {e}")
        else:
            st.error("🛑 Vaqt tugadi! Test yopildi.")
else:
    st.warning("Savollar topilmadi. Jadvalingizda 'Questions' varag'i borligini tekshiring.")
