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

# --- 3. PROFESSIONAL SERTIFIKAT FUNKSIYASI ---
def create_certificate(name, score, subject):
    W, H = 1000, 750 
    img = Image.new('RGB', (W, H), color=(10, 30, 60)) # To'q ko'k fon
    draw = ImageDraw.Draw(img)
    
    # Oltin hoshiyalar
    draw.rectangle([20, 20, 980, 730], outline=(212, 175, 55), width=12)
    draw.rectangle([40, 40, 960, 710], outline=(212, 175, 55), width=2)

    # Shriftlarni yuklash
    try:
        font_path = "Montserrat-Bold.ttf" 
        font_title = ImageFont.truetype(font_path, 75)
        font_name = ImageFont.truetype(font_path, 85)
        font_info = ImageFont.truetype(font_path, 35)
        font_dir = ImageFont.truetype(font_path, 28)
    except:
        font_title = font_name = font_info = font_dir = ImageFont.load_default()

    # 1. LOGOTIP (Yuqori chap burchakda)
    try:
        logo = Image.open("logo.png").convert("RGBA")
        logo = logo.resize((120, 120))
        img.paste(logo, (70, 60), logo)
    except:
        draw.text((70, 70), "[ LOGO ]", fill="gray", font=font_info)

    # 2. MATNLAR
    draw.text((W/2, 160), "SERTIFIKAT", fill=(212, 175, 55), font=font_title, anchor="mm")
    draw.text((W/2, 270), "Ushbu hujjat egasi:", fill="white", font=font_info, anchor="mm")
    
    # O'quvchi ismi (Oltin rangda)
    draw.text((W/2, 380), name.upper(), fill=(212, 175, 55), font=font_name, anchor="mm")
    
    draw.text((W/2, 500), f"Fan: {subject}", fill="white", font=font_info, anchor="mm")
    draw.text((W/2, 560), f"Natija: {score}", fill=(100, 255, 100), font=font_info, anchor="mm")

    # 3. SANA (Pastki chapda)
    draw.text((70, 660), f"Sana: {time.strftime('%d.%m.%Y')}", fill="gray", font=font_info)

    # 4. IMZO VA DIREKTOR (Pastki o'ngda)
    try:
        sig = Image.open("signature.png").convert("RGBA")
        sig = sig.resize((180, 90))
        img.paste(sig, (720, 600), sig)
    except:
        draw.line((720, 650, 930, 650), fill="white", width=2) # Imzo yo'q bo'lsa chiziq
    
    draw.text((650, 660), "Direktor: Normurodov Izzatillo", fill="white", font=font_dir)

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
    except:
        return pd.DataFrame()

all_q = load_questions()

# --- 5. ASOSIY INTERFEYS ---
st.title("🎓 Smart Test Masters")

# Sidebar - Admin panel
st.sidebar.title("🔐 Nazorat Paneli")
admin_pass = st.sidebar.text_input("Admin paroli:", type="password", help="Yuklab olish uchun parolni kiriting")

if not all_q.empty:
    st.info("Iltimos, testni boshlashdan oldin ism-familiyangizni to'liq yozing.")
    user_name = st.text_input("Ism-familiyangiz:")
    subjects = all_q['Fan'].unique()
    subject = st.selectbox("Fanni tanlang:", subjects)

    if user_name and subject:
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
            st.sidebar.metric("⏳ Qolgan vaqt", f"{remaining // 60}:{remaining % 60:02d}")
            
            with st.form(key="quiz_form"):
                user_answers = {}
                for i, (idx, row) in enumerate(q_df.iterrows()):
                    st.subheader(f"{i+1}. {row['Savol']}")
                    opts = [f"A) {row['A']}", f"B) {row['B']}", f"C) {row['C']}", f"D) {row['D']}"]
                    user_answers[idx] = st.radio("Javobingizni tanlang:", opts, key=f"q_{idx}", index=None)
                
                submitted = st.form_submit_button("Testni yakunlash va natijani ko'rish")

            if submitted:
                score = 0
                for idx, row in q_df.iterrows():
                    ans_label = user_answers[idx]
                    if ans_label:
                        val = ans_label.split(") ", 1)[1]
                        if str(val).strip() == str(row['Javob']).strip():
                            score += 1
                
                # Google Sheets'ga saqlash
                try:
                    res = pd.DataFrame([{"Ism": user_name, "Fan": subject, "Ball": f"{score}/{len(q_df)}"}])
                    old = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
                    updated = pd.concat([old, res], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated, worksheet="Sheet1")
                except:
                    pass

                st.success(f"Tabriklaymiz, {user_name}! Sizning natijangiz: {score}/{len(q_df)}")
                
                # Sertifikat generatsiyasi
                cert_bytes = create_certificate(user_name, f"{score}/{len(q_df)}", subject)
                st.image(cert_bytes, caption="Sertifikatingiz tayyor!")
                
                # Faqat siz uchun yuklab olish tugmasi
                if admin_pass == "Izzat06":
                    st.sidebar.success("Xush kelibsiz, Izzatillo!")
                    st.download_button(
                        label="📥 Sertifikatni yuklab olish (PNG)",
                        data=cert_bytes,
                        file_name=f"Sertifikat_{user_name}.png",
                        mime="image/png"
                    )
                else:
                    st.sidebar.warning("Yuklab olish tugmasini ochish uchun parolni kiriting.")
                
                st.balloons()
        else:
            st.error("🛑 Vaqt tugadi! Iltimos, sahifani yangilab qaytadan urinib ko'ring.")
