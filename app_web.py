import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# =========================================================
# CẤU HÌNH TRANG & GIAO DIỆN
# =========================================================
st.set_page_config(page_title="Quản lý Tàu cá NHVN", layout="wide")

# Custom CSS để tạo hiệu ứng "Box nổi" và giao diện hiện đại
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #3498db; color: white; }
    .vessel-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0d6efd;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .info-label { color: #6c757d; font-weight: bold; font-size: 0.9em; }
    .info-value { color: #212529; font-weight: bold; font-size: 1.1em; margin-bottom: 10px; }
    .status-expired { color: #dc3545; font-weight: bold; }
    .status-valid { color: #198754; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LOGIC XỬ LÝ DỮ LIỆU
# =========================================================
COLUMN_ALIASES = {
    'SO_DANG_KY': ['số đăng ký', 'biển số', 'số đk'],
    'CHU_TAU': ['chủ tàu', 'chủ phương tiện', 'họ tên chủ', 'tên chủ'],
    'SDT': ['số điện thoại', 'sđt', 'sdt', 'điện thoại'],
    'CCCD': ['cccd', 'cmnd', 'căn cước', 'chứng minh', 'số định danh', 'số cmnd'],
    'DIA_CHI': ['địa chỉ', 'nơi thường trú', 'địa chỉ thường trú', 'chỗ ở', 'địa chỉ chủ'],
    'LMAX': ['chiều dài lmax', 'lmax', 'chiều dài lớn nhất', 'l max', 'chiều dài'],
    'CONG_SUAT': ['công suất', 'cv', 'kw', 'máy chính'],
    'HAN_DK': ['hạn đăng kiểm', 'hết hạn đk', 'ngày hết hạn đăng kiểm (dd/mm/yyyy)', 'ngày hết hạn đăng kiểm', 'hạn đk'],
    'HAN_GP': ['hạn giấy phép', 'hạn gp', 'hết hạn gp', 'hạn gpktts', 'giấy phép ktts', 'ngày hết hạn (đối chiếu)', 'ngày hết hạn']
}

def map_columns(df_columns):
    mapping = {}
    for std_name, alias_list in COLUMN_ALIASES.items():
        for col in df_columns:
            if any(alias in str(col).lower() for alias in alias_list):
                mapping[std_name] = col
                break
    return mapping

def format_id_numbers(val, length=12):
    if pd.isna(val): return "-"
    s = str(val).split('.')[0].strip()
    if s.isdigit(): return s.zfill(length) if len(s) < length else s
    return s

# =========================================================
# SIDEBAR ĐIỀU HƯỚNG
# =========================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Vietnam_Fisheries_Surveillance_Logo.svg/1200px-Vietnam_Fisheries_Surveillance_Logo.svg.png", width=100)
    st.title("KIỂM NGƯ NHVN")
    st.markdown("---")
    menu = st.radio("MENU CHÍNH", ["🔍 Tra cứu thông tin", "🔄 Đối chiếu dữ liệu", "📊 Lọc & Xuất báo cáo"])
    st.markdown("---")
    st.info("Phiên bản Web 2026. Hỗ trợ cập nhật CSDL liên tục qua GitHub.")

# =========================================================
# TRANG 1: TRA CỨU THÔNG TIN (Giao diện 50-50)
# =========================================================
if menu == "🔍 Tra cứu thông tin":
    st.header("🔍 Hệ thống Tra cứu Tàu cá")
    
    # Nạp dữ liệu
    uploaded_file = st.file_uploader("Nạp file Cơ sở dữ liệu (Excel)", type=["xlsx", "xls"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        mapping = map_columns(df.columns)
        
        # Thanh tìm kiếm
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            keyword = st.text_input("Nhập Số đăng ký hoặc Tên chủ tàu:", placeholder="Ví dụ: KH-90279-TS")
        with search_col2:
            st.write("##")
            if st.button("Làm mới"): st.rerun()

        if keyword:
            col_dk = mapping.get('SO_DANG_KY')
            col_ten = mapping.get('CHU_TAU')
            
            res = df[
                df[col_dk].astype(str).str.lower().str.contains(keyword.lower()) | 
                df[col_ten].astype(str).str.lower().str.contains(keyword.lower())
            ] if col_dk and col_ten else pd.DataFrame()

            if not res.empty:
                # CHIA ĐÔI MÀN HÌNH 50-50
                left_col, right_col = st.columns(2)
                
                with left_col:
                    st.subheader("📋 Danh sách kết quả")
                    st.dataframe(res, use_container_width=True)
                
                with right_col:
                    st.subheader("📄 Chi tiết Tàu cá")
                    # Lấy dòng đầu tiên trong kết quả để hiển thị thẻ
                    item = res.iloc[0]
                    
                    # Tính toán trạng thái hết hạn
                    hdk_val = str(item.get(mapping.get('HAN_DK'), '-'))
                    hgp_val = str(item.get(mapping.get('HAN_GP'), '-'))
                    
                    st.markdown(f"""
                    <div class="vessel-card">
                        <h2 style='color:#0d6efd; margin-top:0;'>{item.get(mapping.get('SO_DANG_KY'), '-')}</h2>
                        <hr>
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                            <div>
                                <p class="info-label">CHỦ PHƯƠNG TIỆN</p>
                                <p class="info-value">{item.get(mapping.get('CHU_TAU'), '-')}</p>
                                <p class="info-label">SỐ ĐIỆN THOẠI</p>
                                <p class="info-value">{format_id_numbers(item.get(mapping.get('SDT'), '-'), 10)}</p>
                                <p class="info-label">CHIỀU DÀI LMAX</p>
                                <p class="info-value">{item.get(mapping.get('LMAX'), '-')} m</p>
                            </div>
                            <div>
                                <p class="info-label">SỐ CCCD/CMND</p>
                                <p class="info-value">{format_id_numbers(item.get(mapping.get('CCCD'), '-'), 12)}</p>
                                <p class="info-label">CÔNG SUẤT</p>
                                <p class="info-value">{item.get(mapping.get('CONG_SUAT'), '-')} KW</p>
                                <p class="info-label">ĐỊA CHỈ</p>
                                <p class="info-value">{item.get(mapping.get('DIA_CHI'), '-')}</p>
                            </div>
                        </div>
                        <div style='background-color:#f8f9fa; padding:15px; border-radius:5px; margin-top:10px;'>
                            <p class="info-label">HẠN GIẤY PHÉP KTTS: <span class="info-value">{hgp_val}</span></p>
                            <p class="info-label">HẠN ĐĂNG KIỂM: <span class="info-value">{hdk_val}</span></p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Không tìm thấy dữ liệu phù hợp.")

# =========================================================
# TRANG 2: ĐỐI CHIẾU (Đa file)
# =========================================================
elif menu == "🔄 Đối chiếu dữ liệu":
    st.header("🔄 Đối chiếu dữ liệu đa nguồn")
    
    c1, c2 = st.columns(2)
    with c1:
        src_file = st.file_uploader("File Gốc (Cần đắp thêm dữ liệu)", type=["xlsx"])
    with c2:
        tgt_files = st.file_uploader("File Đối chiếu (Có thể chọn nhiều)", type=["xlsx"], accept_multiple_files=True)

    if src_file and tgt_files:
        if st.button("🚀 Bắt đầu đối chiếu"):
            df_src = pd.read_excel(src_file)
            mapping_src = map_columns(df_src.columns)
            key_src = mapping_src.get('SO_DANG_KY')
            
            if not key_src:
                st.error("File gốc không có cột Số đăng ký!")
            else:
                df_src['_key'] = df_src[key_src].astype(str).str.strip().str.upper()
                
                for f in tgt_files:
                    df_t = pd.read_excel(f)
                    m_t = map_columns(df_t.columns)
                    k_t = m_t.get('SO_DANG_KY')
                    if k_t:
                        df_t['_key'] = df_t[k_t].astype(str).str.strip().str.upper()
                        # Lấy tất cả các cột trừ cột key
                        cols_to_get = [c for c in df_t.columns if c != '_key']
                        df_t_sub = df_t[['_key'] + cols_to_get].drop_duplicates('_key')
                        # Đổi tên cột để tránh trùng
                        df_t_sub.columns = ['_key'] + [f"{c} ({f.name[:10]}...)" for c in cols_to_get]
                        df_src = pd.merge(df_src, df_t_sub, on='_key', how='left')
                
                df_src.drop(columns=['_key'], inplace=True)
                st.success("Đã đối chiếu thành công!")
                st.dataframe(df_src.head())
                
                # Nút tải về
                towrite = io.BytesIO()
                df_src.to_excel(towrite, index=False, engine='openpyxl')
                st.download_button(label="📥 Tải file kết quả", data=towrite.getvalue(), file_name=f"Doi_chieu_{datetime.now().strftime('%d%m%Y')}.xlsx")

# =========================================================
# TRANG 3: LỌC & XUẤT BÁO CÁO (Tách Sheet)
# =========================================================
else:
    st.header("📊 Lọc & Xuất báo cáo thông minh")
    
    filter_file = st.file_uploader("Chọn file nguồn để lọc", type=["xlsx"])
    
    if filter_file:
        df_filter = pd.read_excel(filter_file)
        mapping_f = map_columns(df_filter.columns)
        
        st.markdown("### Thiết lập lọc")
        col_date = st.selectbox("Chọn cột tính Hạn:", df_filter.columns, index=list(df_filter.columns).index(mapping_f.get('HAN_DK')) if mapping_f.get('HAN_DK') in df_filter.columns else 0)
        
        col_check1, col_check2 = st.columns(2)
        with col_check1:
            split_sheet = st.checkbox("Tách mỗi Xã/Phường thành 1 Sheet riêng (Cho tàu hết hạn)")
        
        if st.button("⚡ Thực hiện lọc và Tạo báo cáo"):
            # Logic lọc (giả định lọc tàu hết hạn tính đến hôm nay)
            df_filter['dt_temp'] = pd.to_datetime(df_filter[col_date], errors='coerce', dayfirst=True)
            df_expired = df_filter[df_filter['dt_temp'] < datetime.now()].copy()
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filter.to_excel(writer, sheet_name='Tổng hợp', index=False)
                df_expired.to_excel(writer, sheet_name='Tàu Hết Hạn (Tổng)', index=False)
                
                if split_sheet:
                    # Giả định có cột địa chỉ để phân tích xã phường
                    col_addr = mapping_f.get('DIA_CHI')
                    if col_addr:
                        # Logic tách xã phường đơn giản
                        unique_locs = ["Xã Đại Lãnh", "Xã Vạn Thắng", "Xã Vạn Ninh", "Xã Tu Bông", "Phường Đông Ninh Hòa"]
                        for loc in unique_locs:
                            subset = df_expired[df_expired[col_addr].astype(str).str.contains(loc)]
                            if not subset.empty:
                                subset.to_excel(writer, sheet_name=loc[:30], index=False)
            
            st.success(f"Đã xử lý xong! Tìm thấy {len(df_expired)} tàu hết hạn.")
            st.download_button(label="📥 Tải báo cáo đa Sheet", data=output.getvalue(), file_name=f"Bao_cao_Tau_Ca_{datetime.now().strftime('%d%m%Y')}.xlsx")
