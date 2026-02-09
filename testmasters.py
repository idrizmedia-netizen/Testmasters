import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import random

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Smart Test System", layout="centered")

# 2. Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit"

# 3. Savollarni bazadan yuklab olish va aralashtirish
@st.cache_data(ttl=60)
def load_and_shuffle(subject_name):
    # 'Questions' varag'idan hamma savollarni o'qiymiz
    df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    # Faqat tanlangan fanga tegishlisini ajratamiz
    filtered_df = df[df['Fan'] == subject_name]
    # Savollarni tasodifiy tartibda aralashtiramiz
    shuffled_df = filtered_df.sample(frac=1).reset_index(drop=True)
    return shuffled_df

st.title("🚀 Smart Test Masters")

# Foydalanuvchi ma'lumotlari
name = st.text_input("To'liq ismingizni kiriting:")

# Fanlar ro'yxatini bazadan olish
all_data = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
subjects_list = all_data['Fan'].unique()
subject = st.selectbox("Imtihon topshiradigan fanni tanlang:", subjects_list)

if name and subject:
    # Savollarni yuklaymiz (faqat bir marta aralashtiriladi)
    if 'current_test' not in st.session_state or st.session_state.test_subject != subject:
        st.session_state.current_test = load_and_shuffle(subject)
        st.session_state.test_subject = subject
        st.session_state.start_time = time.time()

    q_df = st.session_state.current_test
    
    # --- TAYMER ---
    time_limit = 120  # 2 daqiqa (xohlagancha o'zgartiring)
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = int(time_limit - elapsed_time)

    if remaining_time > 0:
        st.sidebar.header("📊 Holat")
        st.sidebar.metric("⏳ Qolgan vaqt", f"{remaining_time} sek")
        
        # Har 10 soniyada sahifani yangilash
        if remaining_time % 10 == 0:
            time.sleep(1)
            st.rerun()

        score = 0
        user_answers = {}

        with st.form("quiz_form"):
            st.info(f"Diqqat {name}, sizda {len(q_df)} ta savol bor.")
            
            for i, row in q_df.iterrows():
                st.write(f"**{i+1}. {row['Savol']}**")
                options = [row['O1'], row['O2'], row['O3'], row['O4']]
                # Javoblar variantlarini ham aralashtirish mumkin
                user_answers[i] = st.radio(f"Variantlardan birini tanlang:", options, key=f"ans_{i}")
                
            submitted = st.form_submit_button("Testni yakunlash")

            if submitted:
                # Ballni hisoblash
                for i, row in q_df.iterrows():
                    if user_answers[i] == row['Javob']:
                        score += 1
                
                try:
                    # Natijani saqlash (Sheet1 ga)
                    new_res = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/{len(q_df)}"}])
                    results_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
                    updated_results = pd.concat([results_df, new_res], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated_results, worksheet="Sheet1")
                    
                    st.success(f"Natijangiz saqlandi! Jami ball: {score}")
                    st.balloons()
                    # Test tugagach xotirani tozalash
                    del st.session_state.current_test
                    del st.session_state.start_time
                except Exception as e:
                    st.error(f"Xatolik: {e}")
    else:
        st.error("⌛ Vaqt tugadi! Natijangiz saqlanmadi.")
        if st.button("Qayta urinish"):
            del st.session_state.current_test
            del st.session_state.start_time
            st.rerun()
