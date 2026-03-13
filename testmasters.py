import streamlit as st
import pandas as pd
import time
import requests
import random
from datetime import datetime
import streamlit.components.v1 as components
import gspread
from google.oauth2 import service_account
import plotly.express as px  # Grafiklar uchun

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="ZiyoMap", page_icon="🎓", layout="centered")

# 2. SECRETS VA ULANISH
try:
    TELEGRAM_TOKEN = st.secrets["general"]["telegram_token"]
    CHAT_ID = st.secrets["general"]["chat_id"]
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U")
    result_sheet = sh.worksheet("Results")
except Exception as e:
    st.error(f"Sozalamalarda xatolik: {e}")
    st.stop()

# --- YORDAMCHI FUNKSIYALAR ---

@st.cache_data(ttl=600)
def load_questions():
    try:
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTA1Ws84mZCqZvmj53YWxR3Xd7_Qd8V-Ro_w_79eklEXyDOt0BP6Vr8WJUodsXUo3WYb3sYMBijM5k9/pub?output=csv"
        df = pd.read_csv(csv_url)
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            return df
        return None
    except: return None

@st.cache_data(ttl=300)
def get_results_cached():
    try: return pd.DataFrame(result_sheet.get_all_records())
    except: return pd.DataFrame()

def background_tasks(name, subject, category, corrects, total, ball):
    try:
        row = [datetime.now().strftime("%Y-%m-%d %H:%M"), str(name), str(category), str(subject), int(corrects), int(total - corrects), f"{ball}%"]
        result_sheet.append_row(row)
        st.cache_data.clear() 
    except: pass
    try:
        text = f"🏆 YANGI NATIJA!\n👤: {name}\n📂: {category}\n📚: {subject}\n✅ To'g'ri: {corrects}\n❌ Noto'g'ri: {total - corrects}\n📊 Ball: {ball}%"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except: pass

# --- TAYMER VA STIL ---
def show_smooth_timer(seconds):
    timer_html = f"""
    <div id="timer" style="font-size: 30px; font-weight: bold; color: #00C9FF; text-align: center; 
           background: rgba(0,0,0,0.5); padding: 15px; border-radius: 10px; border: 1px solid #00C9FF;">
        {seconds//60:02d}:{seconds%60:02d}
    </div>
    <script>
        var timeLeft = {seconds};
        var timerDiv = document.getElementById("timer");
        var interval = setInterval(function() {{
            timeLeft--;
            var minutes = Math.floor(timeLeft / 60);
            var seconds = timeLeft % 60;
            timerDiv.innerHTML = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
            if (timeLeft <= 0) {{ clearInterval(interval); }}
        }}, 1000);
    </script>
    """
    st.sidebar.markdown("### ⏱ VAQT")
    components.html(timer_html, height=100)

def apply_styles(subject="Default"):
    st.markdown(f"""
    <style>
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000") no-repeat center center fixed !important; 
        background-size: cover !important; 
    }}
    h1, h2, h3, p, label, .stMarkdown, .stText, div[role="radiogroup"] label {{ 
        color: #ffffff !important; 
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important;
    }}
    div[role="radiogroup"] > label {{ 
        background: rgba(255, 255, 255, 0.1) !important; 
        border: 1px solid rgba(0, 201, 255, 0.5) !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        margin-bottom: 5px !important;
        transition: 0.3s !important;
    }}
    div.stButton > button {{ 
        width: 100%; 
        border: none !important;
        border-radius: 15px !important;
        background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important; 
        color: #001f3f !important; 
        font-weight: 900 !important; 
        padding: 12px !important;
        transition: transform 0.2s !important;
    }}
    div.stButton > button:hover {{ transform: scale(1.03); filter: brightness(1.1); }}
    .stMarkdown p, .stForm p {{ font-size: 18px !important; line-height: 1.5 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- SAHIFALAR ---
if 'page' not in st.session_state: st.session_state.page = "HOME"

if st.session_state.page == "RESULT":
    apply_styles()
    res = st.session_state.final_score
    st.markdown(f'<div class="main-card" style="text-align:center;"><h1>{res["ball"]}%</h1><h2>{res["name"]}</h2></div>', unsafe_allow_html=True)
    with st.expander("🔍 Natijalar tahlilini ko'rish"):
        for log in st.session_state.user_logs:
            color = "#92FE9D" if log['correct'] else "#FF4B4B"
            st.markdown(f"""
            <div class="analysis-card" style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 10px; background: rgba(255,255,255,0.05);">
                <p><b>Savol:</b> {log["question"]}</p>
                <p>Sizning javobingiz: {log["user_ans"]}</p>
                <p style='color:{color};'><b>To'g'ri javob:</b> {log['correct_ans']}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")
    if st.button("📊 GRAFIK TAHLILNI KO'RISH"):
        df_history = get_results_cached()
        if not df_history.empty:
            my_history = df_history[df_history['Ism-familiya'] == res["name"]].copy()
            my_history['Ball_Num'] = my_history['Ball'].astype(str).str.replace('%', '').astype(float)
            fig = px.bar(my_history, x='Sana', y='Ball_Num', title=f"{res['name']} ning test natijalari dinamikasi", labels={'Ball_Num': 'Ball (%)', 'Sana': 'Topshirilgan vaqt'}, color='Ball_Num', color_continuous_scale='Viridis', text='Ball_Num')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig, use_container_width=True)
        else: st.warning("Hozircha grafik uchun yetarli ma'lumot yo'q.")
    st.markdown("---")
    st.link_button("📢 ZiyoMap kanalimizga o'tish", "https://t.me/ZiyoMap")
    if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"): 
        st.session_state.page = "HOME"; st.rerun()

elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    show_smooth_timer(st.session_state.total_time)
    st.markdown(f"### 📚 Fan: {st.session_state.selected_subject} ({st.session_state.category})")
    with st.form(key="quiz_form"):
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"**{i+1}. {item['q']}**")
            if pd.notna(item['image']) and str(item['image']) != '0': st.image(item['image'])
            user_answers[i] = st.radio("Tanlang:", item['o'], index=None, key=f"q_{i}")
        if st.form_submit_button("🏁 TESTNI TUGATISH"):
            logs = []
            corrects = 0
            for i, item in enumerate(st.session_state.test_items):
                u_ans = user_answers[i]
                sheet_answer = str(item['c']).strip().upper()
                c_ans = item['map'].get(sheet_answer) if sheet_answer in ['A', 'B', 'C', 'D'] else sheet_answer
                is_correct = (str(u_ans).strip().lower() == str(c_ans).strip().lower())
                if is_correct: corrects += 1
                logs.append({"question": item['q'], "user_ans": u_ans, "correct": is_correct, "correct_ans": c_ans})
            ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
            st.session_state.update({"user_logs": logs, "final_score": {"name": st.session_state.full_name, "ball": ball}, "page": "RESULT"})
            background_tasks(st.session_state.full_name, st.session_state.selected_subject, st.session_state.category, corrects, len(st.session_state.test_items), ball)
            st.rerun()

elif st.session_state.page == "HOME":
    apply_styles()
    st.markdown("<h1 style='text-align:center;'>🎓 ZiyoMap Online</h1>", unsafe_allow_html=True)
    with st.expander("🏆 FANLAR BO'YICHA REYTING"):
        df_all = get_results_cached()
        if not df_all.empty:
            df_all['Ball_Num'] = df_all['Ball'].astype(str).str.replace('%', '').astype(float)
            all_subjects = sorted(df_all['Fan'].unique().tolist())
            selected_rating_subject = st.selectbox("Reytingni ko'rish uchun fanni tanlang:", all_subjects)
            rating_df = df_all[df_all['Fan'] == selected_rating_subject]
            
            # Reytingni tartiblash va tartib raqami qo'shish
            top10 = rating_df.sort_values(by='Ball_Num', ascending=False).head(10).copy()
            top10.insert(0, "№", range(1, len(top10) + 1))
            
            # hide_index=True yordamida Google Sheet indekslari yashiriladi
            st.dataframe(top10[['№', 'Ism-familiya', 'Ball']], hide_index=True, use_container_width=True)
        else: st.write("Hozircha natijalar yo'q.")
    
    category = st.radio("Bo'limni tanlang:", ["O'quvchi", "Attestatsiya", "Sertifikat"], index=None)
    
    if category:
        u_name = st.text_input("Ism-familiyangizni kiriting:")
        q_df = load_questions()
        if q_df is not None:
            filtered_subs = q_df[q_df['Tur'] == category]['Fan'].dropna().unique().tolist()
            selected_subject = st.selectbox("Fanni tanlang:", sorted(filtered_subs))
            
       if st.button("🚀 TESTNI BOSHLASH"):
                if not u_name: 
                    st.error("Iltimos, ism-familiyangizni kiriting!")
                else:
                    # 1. PARAMETRLARNI BELGILASH
                    # Attestatsiya va Sertifikat uchun qat'iy vaqt (sekundda)
                    # 90 daqiqa = 5400 sekund, 150 daqiqa = 9000 sekund
                    config = {
                        "O'quvchi": {"count": 30},
                        "Attestatsiya": {"count": 40, "time_fixed": 5400}, 
                        "Sertifikat": {"count": 45, "time_fixed": 9000}
                    }
                    
                    limit = config[category]["count"]
                    sub_qs_all = q_df[(q_df['Fan'] == selected_subject) & (q_df['Tur'] == category)].copy()
                    
                    # Bazadagi vaqt ustunini raqamga o'tkazish (sekundda bo'lgani uchun o'zgarishsiz qoldiramiz)
                    # Agar vaqt yozilmagan bo'lsa, har bir savolga default 60 sekund beramiz
                    sub_qs_all['Vaqt'] = pd.to_numeric(sub_qs_all['Vaqt'], errors='coerce').fillna(60)
                    
                    # 2. SAVOLLARNI TANLASH
                    if len(sub_qs_all) <= limit:
                        sampled_qs = sub_qs_all
                    else:
                        sampled_qs = sub_qs_all.sample(n=limit)
                    
                    # 3. VAQTNI HISOBLASH
                    if category == "O'quvchi":
                        # O'quvchi: savollardagi sekundlarni qo'shamiz
                        total_time = int(sampled_qs['Vaqt'].sum())
                    else:
                        # Attestatsiya va Sertifikat: qat'iy vaqt
                        total_time = config[category]["time_fixed"]
                    
                    # 4. TEST ITEMLARINI SHAKLLANTIRISH
                    test_items = []
                    for _, r in sampled_qs.iterrows():
                        options = [str(v) for v in {'A':str(r.get('A','')), 'B':str(r.get('B','')), 'C':str(r.get('C','')), 'D':str(r.get('D',''))}.values() if str(v) != 'nan']
                        test_items.append({
                            "q": r['Savol'], 
                            "o": options, 
                            "c": r['Javob'], 
                            "map": {'A':str(r.get('A','')), 'B':str(r.get('B','')), 'C':str(r.get('C','')), 'D':str(r.get('D',''))}, 
                            "image": r.get('Rasm')
                        })
                    
                    st.session_state.update({
                        "full_name": u_name, 
                        "category": category, 
                        "selected_subject": selected_subject, 
                        "test_items": test_items, 
                        "total_time": total_time, 
                        "page": "TEST"
                    })
                    st.rerun()
