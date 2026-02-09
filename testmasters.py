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
@st.cache_data(ttl=5)
def load_questions():
    try:
        # Questions varag'idan o'qish
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions", ttl=0)
        # Ustun nomlaridagi ortiqcha bo'sh joylarni olib tashlaymiz
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Jadval o'qilmadi: {e}")
        return pd.DataFrame()

all_q = load_questions()

# Jadvalda ustunlar borligini tekshirish
required_columns = ['Fan', 'Savol', 'A', 'B', 'C', 'D', 'Javob']

if not all_q.empty:
    # Ustunlar yetishmovchiligini tekshirish
    missing = [col for col in required_columns if col not in all_q.columns]
    if missing:
        st.error(f"Jadvalda quyidagi ustunlar topilmadi: {', '.join(missing)}")
        st.info("Iltimos, Google Sheets jadvalingizning 1-qatorini tekshiring.")
        st.stop()

    name = st.text_input("F.I.SH kiriting:")
    subjects = all_q['Fan'].unique()
    subject = st.selectbox("Fanni tanlang:", subjects)

    if name and subject:
        # Savollarni tayyorlash
        if 'test_data' not in st.session_state or st.session_state.get('last_sub') != subject:
            filtered = all_q[all_q['Fan'] == subject].sample(frac=1)
            st.session_state.test_data = filtered
            st.session_state.last_sub = subject
            st.session_state.start_time = time.time()

        q_df = st.session_state.test_data

        # --- TAYMER ---
        time_limit = 600 # 10 daqiqa
        elapsed = time.time() - st.session_state.start_time
        remaining = int(time_limit - elapsed)

        if remaining > 0:
            st.sidebar.metric("⏳ Qolgan vaqt", f"{remaining // 60}:{remaining % 60:02d}")
            
            # FORM BOSHLANISHI
            with st.form(key="my_quiz_form"):
                user_answers = {}
                
                for i, (idx, row) in enumerate(q_df.iterrows()):
                    st.write(f"### {i+1}-savol: {row['Savol']}")
                    
                    # Variantlarni shakllantirish
                    opts = {
                        f"A) {row['A']}": row['A'],
                        f"B) {row['B']}": row['B'],
                        f"C) {row['C']}": row['C'],
                        f"D) {row['D']}": row['D']
                    }
                    
                    user_answers[idx] = st.radio(
                        "Javobingiz:", 
                        options=list(opts.keys()), 
                        key=f"q_{idx}", 
                        index=None
                    )
                
                # SUBMIT TUGMASI (Formaning ichida bo'lishi shart!)
                submitted = st.form_submit_button("Testni yakunlash")
                
                if submitted:
                    score = 0
                    for idx, row in q_df.iterrows():
                        ans_label = user_answers[idx]
                        if ans_label:
                            # Matnni variantdan ajratib olish: "A) Javob" -> "Javob"
                            selected_val = ans_label.split(") ", 1)[1]
                            if str(selected_val).strip() == str(row['Javob']).strip():
                                score += 1
                    
                    # Natijani saqlash
                    try:
                        res_data = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/{len(q_df)}"}])
                        old_res = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
                        updated = pd.concat([old_res, res_data], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, data=updated, worksheet="Sheet1")
                        
                        st.success(f"Tabriklaymiz! Natijangiz saqlandi: {score}/{len(q_df)}")
                        st.balloons()
                        # Tozalash
                        st.session_state.pop('test_data', None)
                        st.session_state.pop('start_time', None)
                    except Exception as save_error:
                        st.error(f"Saqlashda xato: {save_error}")
        else:
            st.error("⌛ Vaqt tugadi!")
            if st.button("Qayta urinish"):
                st.session_state.pop('test_data', None)
                st.rerun()
else:
    st.warning("Savollar yuklanmadi. Google Sheets ulanishini tekshiring.")
