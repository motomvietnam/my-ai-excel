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

# 2. Hàm xử lý và trang trí file Excel chuyên sâu
def hieu_chinh_excel(df):
    # Tạo một bản sao để không ảnh hưởng dữ liệu gốc
    df_clean = df.copy()

    # --- CHUẨN HÓA DỮ LIỆU ---
    for col in df_clean.columns:
        col_lower = col.lower()
        
        # A. Chuẩn hóa Họ Tên
        if any(keyword in col_lower for keyword in ['tên', 'name', 'ho ten']):
            df_clean[col] = df_clean[col].apply(
                lambda x: " ".join(str(x).strip().title().split()) if pd.notnull(x) and str(x).strip() != "" else x
            )
        
        # B. Chuẩn hóa Số điện thoại
        elif any(keyword in col_lower for keyword in ['sđt', 'điện thoại', 'phone', 'tel']):
            def clean_p(p):
                if pd.isnull(p) or str(p).strip() == "": return p
                n = re.sub(r'\D', '', str(p)) # Chỉ giữ lại số
                if n.startswith('84'): n = '0' + n[2:] # Đổi 84 thành 0
                if len(n) >= 9:
                    return '0' + n[-9:] # Lấy 9 số cuối và thêm 0 để chuẩn 10 số
                return n
            df_clean[col] = df_clean[col].apply(clean_p)
            
        # C. CHUẨN HÓA NGÀY THÁNG (FIX LỖI 00:00:00 VÀ SAI ĐỊNH DẠNG)
        elif any(keyword in col_lower for keyword in ['ngày', 'date']):
            # Ép kiểu về datetime, tự động nhận diện các định dạng ngày khác nhau
            temp_date = pd.to_datetime(df_clean[col], errors='coerce', dayfirst=True)
            # Chuyển về dạng chuỗi DD/MM/YYYY và xóa các ô lỗi (NaT)
            df_clean[col] = temp_date.dt.strftime('%d/%m/%Y').fillna('')

    # --- TẠO FILE EXCEL ĐỊNH DẠNG ĐẸP ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Du_Lieu_Chuan_Hoa')
        workbook  = writer.book
        worksheet = writer.sheets['Du_Lieu_Chuan_Hoa']

        # Định dạng Header: Xanh đậm, chữ trắng, font Arial, căn giữa
        fmt_header = workbook.add_format({
            'bold': True, 
            'bg_color': '#1e3a8a', 
            'font_color': 'white', 
            'border': 1, 
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Định dạng nội dung: font Arial, kẻ bảng, căn dọc giữa
        fmt_body = workbook.add_format({
            'border': 1, 
            'font_name': 'Arial',
            'valign': 'vcenter'
        })

        # Áp dụng định dạng và tự động chỉnh độ rộng cột
        for col_num, value in enumerate(df_clean.columns.values):
            worksheet.write(0, col_num, value, fmt_header)
            # Tính toán độ rộng cột dựa trên nội dung dài nhất
            max_len = max(df_clean[value].astype(str).map(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, min(max_len, 50), fmt_body)
            
    return output.getvalue()

# 3. Giao diện App
st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🚀 SMART TOOLS HUB</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Giải pháp AI Marketing & Xử lý dữ liệu chuyên nghiệp</p>", unsafe_allow_html=True)
st.write("---")

tab1, tab2 = st.tabs(["📊 Hiệu chỉnh Excel", "🤖 AI Content Marketing"])

with tab1:
    st.subheader("🛠️ Chuẩn hóa Họ tên, SĐT & Ngày tháng hàng loạt")
    file = st.file_uploader("Kéo thả file Excel vào đây", type=["xlsx"])
    
    if file:
        try:
            df = pd.read_excel(file)
            st.info(f"Đã nhận file: {file.name} - Số dòng: {len(df)}")
            st.dataframe(df.head(10), use_container_width=True) 
            
            if st.button("✨ Bắt đầu hiệu chỉnh dữ liệu"):
                with st.spinner('Đang xử lý dữ liệu chuyên sâu...'):
                    processed_data = hieu_chinh_excel(df)
                    st.success("✅ Đã hoàn thành! Đã sửa lỗi Ngày tháng, Họ tên viết hoa chuẩn, SĐT định dạng lại.")
                    st.download_button(
                        label="📥 TẢI FILE EXCEL ĐÃ LÀM ĐẸP", 
                        data=processed_data, 
                        file_name=f"Chuan_Hoa_{file.name}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

with tab2:
    st.subheader("📝 Trợ lý Sáng tạo Content AI")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        sp = st.text_input("Tên sản phẩm/dịch vụ:", placeholder="Ví dụ: Kem chống nắng")
        style = st.selectbox("Phong cách bài viết:", ["Hài hước", "Chuyên nghiệp", "Gợi cảm xúc", "Giảm giá sốc"])
        btn_ai = st.button("Tạo bài viết ngay")
        
    with col2:
        if btn_ai and sp:
            with st.spinner('AI đang viết bài...'):
                prompt = f"Viết 1 bài quảng cáo Facebook hấp dẫn cho sản phẩm: {sp}. Phong cách: {style}. Có kèm emoji và hashtag."
                res = model.generate_content(prompt)
                st.markdown("### Kết quả gợi ý:")
                st.write(res.text)
        elif btn_ai:
            st.warning("Vui lòng nhập tên sản phẩm!")

st.write("---")
st.caption("© 2026 Smart Tools Hub | Hỗ trợ Zalo: 0869611000")
