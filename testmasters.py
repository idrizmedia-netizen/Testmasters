import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

st.set_page_config(page_title="Test Masters Pro", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit"

st.title("🎓 Smart Test Masters")

@st.cache_data(ttl=10)
def load_questions():
    try:
        # worksheet="Questions" ekanligini aniq tekshiring
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions", ttl=0)
        return df
    except Exception as e:
        st.error(f"Jadval o'qilmadi. 'Questions' varag'i bormi? Xato: {e}")
        return pd.DataFrame()

all_q = load_questions()

if not all_q.empty:
    # Jadvaldagi ustun nomlarini kichik harfga o'tkazib tekshiramiz (Xato bermasligi uchun)
    all_q.columns = [c.strip() for c in all_q.columns]
    
    name = st.text_input("F.I.SH kiriting:")
    subjects = all_q['Fan'].unique()
    subject = st.selectbox("Fanni tanlang:", subjects)

    if name and subject:
        if 'test_data' not in st.session_state or st.session_state.get('last_sub') != subject:
            filtered = all_q[all_q['Fan'] == subject].sample(frac=1)
            st.session_state.test_data = filtered
            st.session_state.last_sub = subject
            st.session_state.start_time = time.time()

        q_df = st.session_state.test_data

        # TAYMER
        time_limit = 600 # 10 daqiqa
        elapsed = time.time() - st.session_state.start_time
        remaining = int(time_limit - elapsed)

        if remaining > 0:
            st.sidebar.metric("⏳ Qolgan vaqt", f"{remaining // 60}:{remaining % 60:02d}")
            
            # MUHIM: Form yaratish
            with st.form(key="quiz_form"):
                score = 0
                user_choices = {}

                for i, (idx, row) in enumerate(q_df.iterrows()):
                    st.write(f"### {i+1}-savol: {row['Savol']}")
                    
                    # Ustunlar borligini tekshirish (A, B, C, D)
                    try:
                        options_map = {
                            f"A) {row['A']}": row['A'],
                            f"B) {row['B']}": row['B'],
                            f"C) {row['C']}": row['C'],
                            f"D) {row['D']}": row['D']
                        }
                        user_choices[idx] = st.radio("Javobingiz:", options_map.keys(), key=f"q_{idx}", index=None)
                    except KeyError:
                        st.error("Xato: Jadvalda A, B, C yoki D ustuni topilmadi!")
                        st.stop()
                
                # SHU TUGMA BO'LMASA FORM ISHLAMAYDI
                submitted = st.form_submit_button("Testni yakunlash")
                
                if submitted:
                    for idx, row in q_df.iterrows():
                        selected_label = user_choices[idx]
                        if selected_label:
                            # Tanlangan matnni to'g'ri javob bilan solishtirish
                            user_ans_val = selected_label.split(") ", 1)[1]
                            if str(user_ans_val).strip() == str(row['Javob']).strip():
                                score += 1
                    
                    # Natijani saqlash
                    try:
                        res = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/{len(q_df)}"}])
                        old_res = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
                        updated = pd.concat([old_res, res], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, data=updated, worksheet="Sheet1")
                        st.success(f"Natijangiz saqlandi: {score} ball")
                        st.balloons()
                        # Sessiyani tozalash
                        st.session_state.pop('test_data', None)
                        st.session_state.pop('start_time', None)
                    except:
                        st.warning("Natija ko'rsatildi, lekin bazaga saqlashda muammo bo'ldi.")

        else:
            st.error("Vaqt tugadi!")
else:
    st.info("Savollar yuklanmoqda yoki jadval bo'sh...")
