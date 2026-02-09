import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

st.set_page_config(page_title="Smart Test Masters", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit"

st.title("🎓 Smart Test Masters")

@st.cache_data(ttl=5)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions", ttl=0)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Jadval o'qilmadi: {e}")
        return pd.DataFrame()

all_q = load_questions()

# Kerakli ustunlar ro'yxatiga 'Vaqt' qo'shildi
required_columns = ['Fan', 'Savol', 'A', 'B', 'C', 'D', 'Javob', 'Vaqt']

if not all_q.empty:
    missing = [col for col in required_columns if col not in all_q.columns]
    if missing:
        st.error(f"Jadvalda quyidagi ustunlar topilmadi: {', '.join(missing)}")
        st.info("Google Sheets-da 'Vaqt' ustunini oching va sonlar kiriting.")
        st.stop()

    name = st.text_input("F.I.SH kiriting:")
    subjects = all_q['Fan'].unique()
    subject = st.selectbox("Fanni tanlang:", subjects)

    if name and subject:
        if 'test_data' not in st.session_state or st.session_state.get('last_sub') != subject:
            filtered = all_q[all_q['Fan'] == subject].sample(frac=1)
            st.session_state.test_data = filtered
            st.session_state.last_sub = subject
            st.session_state.start_time = time.time()
            
            # --- DINAMIK VAQT HISOBLASH ---
            # Har bir savol uchun ajratilgan vaqtlarni qo'shib chiqamiz
            total_allocated_time = int(filtered['Vaqt'].sum())
            st.session_state.total_time = total_allocated_time

        q_df = st.session_state.test_data
        time_limit = st.session_state.total_time
        
        elapsed = time.time() - st.session_state.start_time
        remaining = int(time_limit - elapsed)

        if remaining > 0:
            # Taymer vizual ko'rinishi
            st.sidebar.subheader("⏳ Test vaqti")
            st.sidebar.title(f"{remaining // 60}:{remaining % 60:02d}")
            
            # Progress bar (vaqt o'tishini ko'rsatish uchun)
            progress = max(0.0, min(1.0, remaining / time_limit))
            st.sidebar.progress(progress)
            
            if remaining % 5 == 0:
                time.sleep(1)
                st.rerun()

            with st.form(key="dynamic_time_form"):
                user_answers = {}
                for i, (idx, row) in enumerate(q_df.iterrows()):
                    st.write(f"### {i+1}-savol ({row['Vaqt']} sek): {row['Savol']}")
                    opts = {f"A) {row['A']}": row['A'], f"B) {row['B']}": row['B'], 
                            f"C) {row['C']}": row['C'], f"D) {row['D']}": row['D']}
                    user_answers[idx] = st.radio("Javob:", options=list(opts.keys()), key=f"q_{idx}", index=None)
                
                submitted = st.form_submit_button("Testni yakunlash")
                
                if submitted:
                    score = 0
                    for idx, row in q_df.iterrows():
                        ans_label = user_answers[idx]
                        if ans_label:
                            selected_val = ans_label.split(") ", 1)[1]
                            if str(selected_val).strip() == str(row['Javob']).strip():
                                score += 1
                    
                    # Natijani saqlash
                    res_data = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/{len(q_df)}"}])
                    old_res = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
                    updated = pd.concat([old_res, res_data], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated, worksheet="Sheet1")
                    
                    st.success(f"Natijangiz saqlandi: {score}/{len(q_df)}")
                    st.balloons()
                    st.session_state.pop('test_data', None)
        else:
            st.error("🛑 Vaqt tugadi!")
            if st.button("Qayta urinish"):
                st.session_state.pop('test_data', None)
                st.rerun()
