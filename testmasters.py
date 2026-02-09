import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from PIL import Image, ImageDraw, ImageFont
import io

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Smart Test Masters Pro", layout="centered")

# 2. Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit"

# --- 3. SERTIFIKAT YASASH FUNKSIYASI ---
def create_certificate(name, score, subject):
    W, H = 1000, 700
    # To'q ko'k fon va oltin hoshiya
    img = Image.new('RGB', (W, H), color=(10, 30, 60))
    draw = ImageDraw.Draw(img)
    
    # Oltin hoshiya chizish
    draw.rectangle([20, 20, 980, 680], outline=(212, 175, 55), width=12)
    draw.rectangle([40, 40, 960, 660], outline=(212, 175, 55), width=2)

    # Shriftni yuklash
    try:
        # GitHub'ga yuklagan shrift faylingiz nomi bilan bir xil bo'lishi kerak
        font_path = "Montserrat-Bold.ttf" 
        font_title = ImageFont.truetype(font_path, 70)
        font_name = ImageFont.truetype(font_path, 80)
        font_info = ImageFont.truetype(font_path, 35)
    except:
        # Agar shrift topilmasa standart shrift ishlatiladi
        font_title = font_name = font_info = ImageFont.load_default()

    # Matnlarni chizish (Markazlashtirilgan)
    draw.text((W/2, 150), "SERTIFIKAT", fill=(212, 175, 55), font=font_title, anchor="mm")
    draw.text((W/2, 260), "Ushbu hujjat egasi:", fill="white", font=font_info, anchor="mm")
    
    # Ism (Oltin rangda va katta)
    draw.text((W/2, 360), name.upper(), fill=(212, 175, 55), font=font_name, anchor="mm")
    
    draw.text((W/2, 480), f"Fan: {subject}", fill="white", font=font_info, anchor="mm")
    draw.text((W/2, 540), f"Natija: {score}", fill=(100, 255, 100), font=font_info, anchor="mm")
    
    # Sana va quyi matn
    draw.text((W/2, 630), f"Sana: {time.strftime('%d.%m.%Y')}", fill="gray", font=font_info, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 4. SAVOLLARNI YUKLASH ---
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

# --- 5. ASOSIY INTERFEYS ---
st.title("🎓 Smart Test Masters")

if not all_q.empty:
    name = st.text_input("To'liq ism-familiyangizni kiriting:")
    subjects = all_q['Fan'].unique()
    subject = st.selectbox("Test topshirmoqchi bo'lgan fanni tanlang:", subjects)

    if name and subject:
        # Sessiyada ma'lumotlarni saqlash
        if 'test_data' not in st.session_state or st.session_state.get('last_sub') != subject:
            filtered = all_q[all_q['Fan'] == subject].sample(frac=1)
            st.session_state.test_data = filtered
            st.session_state.last_sub = subject
            st.session_state.start_time = time.time()
            st.session_state.total_time = int(filtered['Vaqt'].sum())

        q_df = st.session_state.test_data
        time_limit = st.session_state.total_time
        elapsed = time.time() - st.session_state.start_time
        remaining = int(time_limit - elapsed)

        if remaining > 0:
            st.sidebar.subheader("⏳ Qolgan vaqt:")
            st.sidebar.title(f"{remaining // 60}:{remaining % 60:02d}")
            st.sidebar.progress(max(0.0, min(1.0, remaining / time_limit)))
            
            # Har 5 soniyada yangilab turish
            if remaining % 5 == 0:
                time.sleep(1)
                st.rerun()

            with st.form(key="quiz_form"):
                user_answers = {}
                for i, (idx, row) in enumerate(q_df.iterrows()):
                    st.write(f"### {i+1}-savol: {row['Savol']}")
                    opts = {
                        f"A) {row['A']}": row['A'],
                        f"B) {row['B']}": row['B'],
                        f"C) {row['C']}": row['C'],
                        f"D) {row['D']}": row['D']
                    }
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
                    
                    # Natijani Google Sheets-ga saqlash
                    try:
                        res_row = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/{len(q_df)}"}])
                        old_res = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
                        updated = pd.concat([old_res, res_row], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, data=updated, worksheet="Sheet1")
                    except:
                        st.warning("Natija bazaga saqlanmadi, lekin sertifikat tayyor!")

                    # SERTIFIKATNI CHIQARISH
                    st.success(f"Test yakunlandi! Sizning natijangiz: {score}/{len(q_df)}")
                    cert_bytes = create_certificate(name, f"{score}/{len(q_df)}", subject)
                    st.image(cert_bytes, caption="Sertifikatingiz")
                    
                    st.download_button(
                        label="📄 Sertifikatni yuklab olish (PNG)",
                        data=cert_bytes,
                        file_name=f"Sertifikat_{name}.png",
                        mime="image/png"
                    )
                    st.balloons()
        else:
            st.error("🛑 Vaqt tugadi! Iltimos, qaytadan urinib ko'ring.")
            if st.button("Qayta boshlash"):
                st.session_state.pop('test_data', None)
                st.rerun()
else:
    st.warning("Savollar yuklanmadi. Google Sheets jadvalingizni tekshiring.")
