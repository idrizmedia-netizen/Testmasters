# Testlarni chiqarish
    for i, q_item in enumerate(questions[subject]):
        st.write(f"{i+1}. {q_item['q']}")
        ans = st.radio(f"Javobni tanlang ({i}):", q_item['options'], key=f"q{i}")
        user_answers.append(ans)
        if ans == q_item['a']:
            score += 1

    # Natijani jo'natish
    if st.button("Testni yakunlash"):
        # Jadvalga ma'lumot tayyorlash
        new_data = pd.DataFrame([{"Ism": name, "Fan": subject, "Natija": f"{score}/10"}])
        
        # Google Sheets'ga yozish (URL ni o'zingizniki bilan almashtiring)
        sheet_url = "https://docs.google.com/spreadsheets/d/1zNTrtJwVzR0X07v6oKqf7324..." # O'zingizning URLingizni qo'ying
        
        try:
            # Mavjud ma'lumotlarni olish va yangisini qo'shish
            existing_data = conn.read(spreadsheet=sheet_url)
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(spreadsheet=sheet_url, data=updated_data)
            
            st.success(f"Tabriklaymiz {name}! Natijangiz saqlandi: {score}/10")
            st.balloons()
        except Exception as e:
            st.error(f"Xatolik yuz berdi: {e}")
