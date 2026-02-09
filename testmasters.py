import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="📚")

# 2. SOZLAMALAR
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmaster_LC" # Kanalingiz manzili to'g'riligini tekshiring
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- TELEGRAM FUNKSIYASI ---
def send_to_telegram(name, score, total, percent, subject):
    emoji = "🏆" if percent >= 80 else "📈"
    msg = (
        f"🌟 *YANGI TEST NATIJASI* 🌟\n\n"
        f"👤 *O'quvchi:* {name}\n"
        f"📚 *Fan:* {subject}\n"
        f"✅ *To'g'ri javob:* {score} ta\n"
        f"🏁 *Jami savollar:* {total} ta\n"
        f"📊 *Ko'rsatkich:* {percent:.1f}%\n\n"
        f"{emoji} *Testmasters - Bilim cho'qqisi sari!*"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        # Timeoutni oshirdik va xatoni ko'rsatadigan qildik
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        if response.status_code != 200:
            st.error(f"Telegramga yuborishda xato: {response.text}")
    except Exception as e:
        st.error(f"Bot ulanishida xato: {e}")

# --- MA'LUMOTLARNI YUKLASH ---
@st.cache_data(ttl=300)
def load_questions():
    return conn.read(spreadsheet=SHEET_URL, worksheet="Questions")

def load_users():
    # Natijalar endi Sheet1 dan olinadi va tekshiriladi
    return conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)

try:
    q_df = load_questions()
    u_df = load_users()
    available_subjects = q_df['Fan'].unique().tolist()
    existing_users = [str(name).strip().lower() for name in u_df['Ism'].tolist()]
except Exception as e:
    st.error(f"Bazaga ulanishda xato (Varaq nomini tekshiring): {e}")
    st.stop()

# SESSION STATE
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None

st.title("🚀 Testmasters Online Testlar Markazi")

u_name_raw = st.text_input("Ism-familiyangizni kiriting:").strip()

if u_name_raw:
    if u_name_raw.lower() in existing_users:
        st.error(f"🛑 {u_name_raw}, siz avval test topshirgansiz!")
    else:
        selected_subject = st.selectbox("Fanni tanlang:", available_subjects)

        if not st.session_state.test_run and st.session_state.final_score is None:
            if st.button(f"🚀 {selected_subject} fanidan boshlash"):
                sub_qs = q_df[q_df['Fan'] == selected_subject]
                st.session_state.questions = sub_qs.sample(n=min(len(sub_qs), 30))
                st.session_state.total_time = int(st.session_state.questions['Vaqt'].sum())
                st.session_state.start_time = time.time()
                st.session_state.selected_subject = selected_subject
                st.session_state.test_run = True
                st.rerun()

        if st.session_state.test_run:
            timer_place = st.sidebar.empty()
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.total_time - int(elapsed))
            m, s = divmod(remaining, 60)
            timer_place.markdown(f"## ⏳ {m:02d}:{s:02d}")
            
            if remaining <= 0:
                st.session_state.test_run = False
                st.rerun()
            
            with st.form("quiz_form"):
                u_ans = {}
                for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
                    st.write(f"**{i+1}. {row['Savol']}**")
                    u_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
                
                if st.form_submit_button("🏁 Yakunlash"):
                    corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    total = len(st.session_state.questions)
                    percent = (corrects / total) * 100
                    
                    # --- NATIJANI SHEET1 GA SAQLASH ---
                    new_data = pd.concat([u_df, pd.DataFrame([{"Ism": u_name_raw, "Natija": f"{corrects}/{total}", "Fan": st.session_state.selected_subject}])], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=new_data, worksheet="Sheet1")
                    
                    send_to_telegram(u_name_raw, corrects, total, percent, st.session_state.selected_subject)
                    st.session_state.final_score = {"score": corrects, "total": total, "percent": percent}
                    st.session_state.test_run = False
                    st.rerun()
            
            time.sleep(1)
            st.rerun()

# 3. NATIJA VA MOTIVATSION QISM
if st.session_state.final_score is not None:
    res = st.session_state.final_score
    st.balloons()
    st.success(f"### 🎉 Tabriklaymiz! Natijangiz: {res['score']} / {res['total']} ({res['percent']:.1f}%)")
    
    st.markdown("""
        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 5px solid #ff4b4b;">
            <h4 style="color:#1f77b4;">💡 Unutmang!</h4>
            <p>Bugungi kichik muvaffaqiyat ertangi buyuk g'alabalarning poydevoridir. 
            Bilim olishdan hech qachon to'xtamang!</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    # Chiroyli motivatsion tugma
    st.link_button("🚀 Bilimlar dunyosiga qaytish (Telegram Kanal)", 
                   "https://t.me/Testmasters_LC", 
                   use_container_width=True, 
                   help="Kanalimizda yangi testlar va natijalarni kuzatib boring!")
