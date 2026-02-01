import streamlit as st
import pandas as pd
import google.generativeai as genai
import re
from io import BytesIO

# 1. Cấu hình ban đầu
st.set_page_config(page_title="SMART TOOLS HUB", layout="wide")

# Kết nối AI
if "GEMINI_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Chưa cấu hình API Key trong Secrets!")
    st.stop()

# 2. Hàm xử lý dữ liệu
def hieu_chinh_excel(df):
    df_clean = df.copy()

    for col in df_clean.columns:
        col_lower = col.lower()
        
        # A. Chuẩn hóa Họ Tên
        if any(keyword in col_lower for keyword in ['tên', 'name', 'ho ten']):
            df_clean[col] = df_clean[col].apply(
                lambda x: " ".join(str(x).strip().title().split()) if pd.notnull(x) and str(x).strip() != "" else x
            )
        
        # B. Chuẩn hóa Số điện thoại (ĐÃ FIX LỖI SỐ 0)
        elif any(keyword in col_lower for keyword in ['sđt', 'điện thoại', 'phone', 'tel']):
            def clean_p(p):
                if pd.isnull(p) or str(p).strip() == "": return ""
                # Chỉ giữ lại chữ số
                n = re.sub(r'\D', '', str(p)) 
                
                if n.startswith('84'): 
                    n = '0' + n[2:]
                elif not n.startswith('0') and len(n) > 0:
                    n = '0' + n
                
                # Trả về chuỗi 10 số chuẩn nhất
                if len(n) > 10: 
                    return n[-10:]
                return n
            
            # Ép kiểu sang string trước khi apply
            df_clean[col] = df_clean[col].astype(str).apply(clean_p)
            
        # C. Chuẩn hóa Ngày tháng
        elif any(keyword in col_lower for keyword in ['ngày', 'date']):
            temp_date = pd.to_datetime(df_clean[col], errors='coerce', dayfirst=True)
            df_clean[col] = temp_date.dt.strftime('%d/%m/%Y').fillna('')

    # --- TẠO FILE EXCEL ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Data')
        workbook  = writer.book
        worksheet = writer.sheets['Data']

        fmt_header = workbook.add_format({'bold': True, 'bg_color': '#1e3a8a', 'font_color': 'white', 'border': 1, 'font_name': 'Arial', 'align': 'center'})
        # Định dạng text_format để ép Excel giữ số 0
        text_format = workbook.add_format({'border': 1, 'font_name': 'Arial', 'num_format': '@'})

        for col_num, value in enumerate(df_clean.columns.values):
            worksheet.write(0, col_num, value, fmt_header)
            max_len = max(df_clean[value].astype(str).map(len).max(), len(value)) + 2
            # Áp dụng text_format cho toàn bộ cột để không mất số 0
            worksheet.set_column(col_num, col_num, min(max_len, 50), text_format)
            
    return output.getvalue()

# 3. Giao diện (Giữ nguyên phần UI của bạn)
st.title("🚀 SMART TOOLS HUB")
tab1, tab2 = st.tabs(["📊 Hiệu chỉnh Excel", "🤖 AI Content"])

with tab1:
    file = st.file_uploader("Tải file Excel", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        if st.button("✨ Thực hiện hiệu chỉnh"):
            data = hieu_chinh_excel(df)
            st.success("Đã bổ sung số 0 và chuẩn hóa dữ liệu!")
            st.download_button("📥 TẢI FILE", data, f"Da_Sua_{file.name}")

with tab2:
    sp = st.text_input("Sản phẩm:")
    if st.button("Viết bài"):
        res = model.generate_content(f"Viết bài quảng cáo cho {sp}")
        st.write(res.text)
