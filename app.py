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
        
        # B. CHUẨN HÓA SỐ ĐIỆN THOẠI (FIX MẠNH TAY)
        elif any(keyword in col_lower for keyword in ['sđt', 'điện thoại', 'phone', 'tel']):
            def clean_p(p):
                val = str(p).strip()
                if val == "" or val == "nan": return ""
                
                # Xóa hết ký tự không phải số
                n = re.sub(r'\D', '', val) 
                
                # Nếu bắt đầu bằng 84 -> chuyển thành 0
                if n.startswith('84'):
                    n = '0' + n[2:]
                
                # Nếu không có số 0 ở đầu -> bù số 0
                if len(n) > 0 and not n.startswith('0'):
                    n = '0' + n
                
                return n
            
            # Ép kiểu dữ liệu cột thành chuỗi để giữ số 0
            df_clean[col] = df_clean[col].astype(str).apply(clean_p)
            
        # C. Chuẩn hóa Ngày tháng
        elif any(keyword in col_lower for keyword in ['ngày', 'date']):
            temp_date = pd.to_datetime(df_clean[col], errors='coerce', dayfirst=True)
            df_clean[col] = temp_date.dt.strftime('%d/%m/%Y').fillna('')

    # --- TẠO FILE EXCEL VỚI ĐỊNH DẠNG TEXT ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Data')
        workbook  = writer.book
        worksheet = writer.sheets['Data']

        # Format tiêu đề
        fmt_header = workbook.add_format({
            'bold': True, 'bg_color': '#1e3a8a', 'font_color': 'white', 
            'border': 1, 'font_name': 'Arial', 'align': 'center'
        })
        
        # ĐỊNH DẠNG QUAN TRỌNG: Buộc toàn bộ ô dữ liệu là TEXT (Mã hóa là @)
        fmt_text = workbook.add_format({
            'border': 1, 'font_name': 'Arial', 'num_format': '@'
        })

        for col_num, value in enumerate(df_clean.columns.values):
            # Ghi tiêu đề
            worksheet.write(0, col_num, value, fmt_header)
            
            # Tính độ rộng cột
            max_len = max(df_clean[value].astype(str).map(len).max(), len(value)) + 2
            
            # Áp dụng fmt_text cho toàn bộ cột để Excel không tự ý bỏ số 0
            worksheet.set_column(col_num, col_num, min(max_len, 50), fmt_text)
            
    return output.getvalue()

# 3. Giao diện App
st.title("🚀 SMART TOOLS HUB")
tab1, tab2 = st.tabs(["📊 Hiệu chỉnh Excel", "🤖 AI Content"])

with tab1:
    # LƯU Ý: Thêm dtype=str khi đọc để không bị mất số 0 ngay từ lúc đầu
    file = st.file_uploader("Tải file Excel", type=["xlsx"])
    if file:
        try:
            # Đọc file và ép tất cả các cột liên quan đến SĐT về dạng chữ (string)
            df = pd.read_excel(file, dtype=str) 
            st.write("Xem trước dữ liệu gốc:", df.head())
            
            if st.button("✨ Thực hiện hiệu chỉnh"):
                data = hieu_chinh_excel(df)
                st.success("Đã bổ sung số 0 và khóa định dạng Text cho cột SĐT!")
                st.download_button("📥 TẢI FILE", data, f"Da_Sua_{file.name}")
        except Exception as e:
            st.error(f"Lỗi: {e}")

with tab2:
    sp = st.text_input("Sản phẩm:")
    if st.button("Viết bài"):
        res = model.generate_content(f"Viết bài quảng cáo cho {sp}")
        st.write(res.text)
