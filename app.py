import streamlit as st
import pandas as pd
import google.generativeai as genai
import re
from io import BytesIO

# 1. Cấu hình ban đầu
st.set_page_config(page_title="SMART TOOLS HUB", layout="wide")

# Kết nối AI (Lấy key từ Secrets)
if "GEMINI_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Chưa cấu hình API Key trong Secrets!")
    st.stop()

# 2. Hàm xử lý và trang trí file Excel
def hieu_chinh_excel(df):
    # Chuẩn hóa Họ Tên
    for col in df.columns:
        if 'tên' in col.lower():
            df[col] = df[col].apply(lambda x: " ".join(str(x).strip().title().split()) if pd.notnull(x) else x)
    
    # Chuẩn hóa Số điện thoại
    for col in df.columns:
        if 'sđt' in col.lower() or 'điện thoại' in col.lower():
            def clean_p(p):
                n = re.sub(r'\D', '', str(p))
                return '0' + n[-9:] if len(n) >= 9 else n
            df[col] = df[col].apply(clean_p)

    # Tạo file Excel có định dạng
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']

        # Định dạng Header màu xanh, chữ trắng, font Arial
        fmt_header = workbook.add_format({'bold':True, 'bg_color':'#2563eb', 'font_color':'white', 'border':1, 'font_name':'Arial'})
        # Định dạng nội dung font Arial, kẻ bảng
        fmt_body = workbook.add_format({'border':1, 'font_name':'Arial'})

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, fmt_header)
            worksheet.set_column(col_num, col_num, 20, fmt_body)
    return output.getvalue()

# 3. Giao diện App
st.title("🚀 CÔNG CỤ XỬ LÝ DỮ LIỆU THÔNG MINH")

tab1, tab2 = st.tabs(["📊 Hiệu chỉnh Excel", "🤖 AI Content"])

with tab1:
    st.subheader("Tải file Excel để chuẩn hóa Họ tên & SĐT")
    file = st.file_uploader("Chọn file Excel của bạn", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        st.write("Dữ liệu xem trước:", df.head(5))
        if st.button("✨ Bắt đầu hiệu chỉnh"):
            processed_data = hieu_chinh_excel(df)
            st.success("Đã chuẩn hóa xong Font chữ Arial, Họ tên và SĐT!")
            st.download_button("📥 TẢI FILE EXCEL ĐÃ LÀM ĐẸP", data=processed_data, file_name="du_lieu_chuan_hoa.xlsx")

with tab2:
    st.subheader("AI viết bài quảng cáo")
    sp = st.text_input("Sản phẩm của bạn là gì?")
    if st.button("Tạo bài viết"):
        res = model.generate_content(f"Viết bài quảng cáo FB cho: {sp}")
        st.write(res.text)