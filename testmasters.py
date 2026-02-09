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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

# --- 3. SERTIFIKAT YARATISH FUNKSIYASI (XATOSIZ) ---
def create_certificate(name, score_text, subject):
    W, H = 1200, 850
    # Rasm o'lchami to'g'irlandi: (W, H)
    img = Image.new('RGB', (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Oltinrang bezaklar
    gold_color = (197, 160, 82) 
    draw.rectangle([60, 60, 1140, 790], outline=gold_color, width=2)
    
    # Burchaklardagi nafis hoshiyalar
    offset, length = 60, 100
    for i in [(offset, offset, 1, 1), (W-offset, offset, -1, 1), 
              (offset, H-offset, 1, -1), (W-offset, H-offset, -1, -1)]:
        draw.line([(i[0], i[1]), (i[0] + length*i[2], i[1])], fill=gold_color, width=12)
        draw.line([(i[0], i[1]), (i[0], i[1] + length*i[3])], fill=gold_color, width=12)

    try:
        font_path = "Montserrat-Bold.ttf"
        f_title = ImageFont.truetype(font_path, 100)
        f_sub = ImageFont.truetype(font_path, 30)
        f_name = ImageFont.truetype(font_path, 95)
        f_text = ImageFont.truetype(font_path, 35)
        f_dir = ImageFont.truetype(font_path, 32)
    except:
        f_title = f_sub = f_name = f_text = f_dir = ImageFont.load_default()

    # --- ELEMENTLAR KETMA-KETLIGI (HAMMASI MARKAZDA) ---
    
    # 1. LOGOTIP
    try:
        logo = Image.open("logo.jpg").convert("RGBA").resize((150, 150))
        img.paste(logo, (int(W/2 - 75), 90), logo)
    except: pass

    # 2. SARLAVHA
    draw.text((W/2, 290), "SERTIFIKAT", fill=(30, 30, 30), font=f_title, anchor="mm")
    draw.text((W/2, 365), "USHBU HUJJAT QUYIDAGI SHAXSGA TOPSHIRILADI:", fill=gold_color, font=f_sub, anchor="mm")

    # 3. ISM
    draw.text((W/2, 460), name.upper(), fill=(30, 30, 30), font=f_name, anchor="mm")
    
    # 4. TAVSIF
    info_text = f"'{subject}' fani bo'yicha o'tkazilgan test sinovlarida\nmuvaffaqiyatli ishtirok etib, yuqori natija ko'rsatgani uchun."
    draw.multiline_text((W/2, 580), info_text, fill=(60, 60, 60), font=f_text, anchor="mm", align="center")
    
    # 5. NATIJA
    draw.text((W/2, 670), f"NATIJA: {score_text}", fill=(46, 125, 50), font=f_sub, anchor="mm")

    # 6. IMZO VA DIREKTOR (PASTDA MARKAZDA)
    line_y = 760
    draw.line([(W/2 - 180, line_y), (W/2 + 180, line_y)], fill=gold_color, width=2)
    draw.text((W/2, line_y + 35), "Direktor: Normurodov Izzatillo", fill=(30, 30, 30), font=f_dir, anchor="mm")

    # Imzo (Fonsiz va o'rtada)
    try:
        sig = Image.open("signature.jpg").convert("RGBA")
        datas = sig.getdata()
        newData = []
        for item in datas:
            if item[0] > 210 and item[1] > 210 and item[2] > 210:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        sig.putdata(newData)
        sig = sig.resize((260, 130))
        img.paste(sig, (int(W/2 - 130), line_y - 110), sig)
    except: pass

    # 7. SANA (O'NG PASTDA)
    draw.text((1100, 780), f"Sana: {time.strftime('%d.%m.%Y')}", fill="gray", font=f_dir, anchor="rs")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 4. ASOSIY MANTIQ ---
try:
    q_df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    s_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    u_df = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    
    # Settingsdan fanni o'qish
    s_df['Parameter'] = s_df['Parameter'].str.strip()
    active_sub = s_df.loc[s_df['Parameter'] == 'ActiveSubject', 'Value'].values[0]
except Exception as e:
    st.error(f"Ma'lumotlar bazasida xatolik: {e}")
    st.stop()

if 'cert_file' not in st.session_state: st.session_state.cert_file = None
if 'test_run' not in st.session_state: st.session_state.test_run = False

st.title(f"🎓 {active_sub} fanidan onlayn test")

u_name = st.text_input("To'liq ism-familiyangizni kiriting:").strip()

if u_name:
    if u_name in u_df['Ism'].values:
        st.warning("Siz test topshirib bo'lgansiz!")
    else:
        if not st.session_state.test_run:
            if st.button("Testni boshlash"):
                st.session_state.test_run = True
                st.rerun()

        if st.session_state.test_run:
            with st.form("quiz_form"):
                # Savollarni filtrlash va tanlash
                f_qs = q_df[q_df['Fan'] == active_sub]
                sample_n = min(len(f_qs), 30)
                qs = f_qs.sample(n=sample_n)
                
                u_ans = {}
                for i, (idx, row) in enumerate(qs.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    u_ans[idx] = st.radio(f"Variantlar:", [row['A'], row['B'], row['C'], row['D']], key=f"q_{idx}")
                
                if st.form_submit_button("Testni yakunlash"):
                    corrects = sum(1 for idx, row in qs.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    
                    # Users varag'ini yangilash
                    new_u = pd.concat([u_df, pd.DataFrame([{"Ism": u_name}])], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=new_u, worksheet="Users")
                    
                    if corrects > 20:
                        st.session_state.cert_file = create_certificate(u_name, f"{corrects}/{len(qs)}", active_sub)
                        st.success(f"Natija: {corrects}/{len(qs)}. Tabriklaymiz!")
                        st.balloons()
                    else:
                        st.error(f"Natija: {corrects}/{len(qs)}. Sertifikat uchun kamida 21 ball kerak.")
                    
                    st.session_state.test_run = False
                    st.rerun()

if st.session_state.cert_file:
    st.image(st.session_state.cert_file, caption="Sertifikatingiz tayyor!")
    pass_input = st.sidebar.text_input("Yuklab olish paroli:", type="password")
    if pass_input == "Izzat06":
        st.download_button("📥 Yuklab olish", st.session_state.cert_file, "Sertifikat.png", "image/png")
