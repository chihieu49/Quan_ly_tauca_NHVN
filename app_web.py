import streamlit as st
import pandas as pd
import os
from datetime import datetime
import shutil
from io import BytesIO

# =========================================================
# CẤU HÌNH TRANG & GIAO DIỆN CƠ BẢN
# =========================================================
st.set_page_config(page_title="Quản lý Tàu cá NH-VN", layout="wide")

# Đường dẫn lưu trữ CSDL nội bộ
APP_DIR = os.path.join(os.path.expanduser('~'), "PhanMem_TauCa_NHVN_Web")
os.makedirs(APP_DIR, exist_ok=True)
DB_FILE = os.path.join(APP_DIR, "CSDL_TauCa_Local.xlsx")

# --- CSS Tùy chỉnh cho "Box Nổi" chi tiết ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .detail-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .expired-red { color: #dc3545; font-weight: bold; }
    .valid-green { color: #198754; font-weight: bold; }
    .label-text { color: #6c757d; font-size: 0.9rem; font-weight: bold; }
    .value-text { color: #212529; font-size: 1.1rem; font-weight: bold; }
    .location-badge {
        background-color: #0d6efd;
        color: white;
        padding: 2px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# DANH MỤC TỪ ĐIỂN & QUY TẮC (Giữ nguyên từ bản cũ)
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
    'HAN_GP': ['hạn giấy phép', 'hạn gp', 'hết hạn gp', 'hạn gpktts', 'giấy phép ktts', 'ngày hết hạn (đối chiếu)', 'ngày hết hạn'],
    'NGAY_HET_HAN': ['hết hạn']
}

mapping_rules = {
    "Xã Đại Lãnh": ["vạn thạnh", "vạn thọ", "đại lãnh"],
    "Xã Tu Bông": ["vạn khánh", "vạn long", "vạn phước", "tu bông"],
    "Xã Vạn Hưng": ["xuân sơn", "vạn hưng"],
    "Xã Vạn Ninh": ["vạn giã", "tt vạn giã", "vạn phú", "vạn lương", "xã vạn ninh"],
    "Xã Vạn Thắng": ["vạn bình", "vạn thắng"],
    "Phường Đông Ninh Hoà": ["ninh diêm", "ninh hải", "ninh thủy", "đông ninh hòa"],
    "Phường Hoà Thắng": ["ninh giang", "ninh hà", "ninh phú", "hòa thắng"],
    "Xã Bắc Ninh Hoà": ["ninh an", "ninh sơn", "ninh thọ", "bắc ninh hòa"],
    "Xã Nam Ninh Hoà": ["ninh lộc", "ninh ích", "ninh hưng", "nam ninh hòa"],
    "Bắc Nha Trang": ["lương sơn", "vĩnh lương", "văn đăng", "cát lợi"]
}

# =========================================================
# HÀM BỔ TRỢ XỬ LÝ DỮ LIỆU
# =========================================================
def get_commune(address):
    if pd.isna(address): return "CHƯA XÁC ĐỊNH"
    addr = str(address).lower()
    for commune, keywords in mapping_rules.items():
        if any(kw in addr for kw in keywords):
            return commune
    return "CHƯA XÁC ĐỊNH"

def check_expiry(date_val):
    if pd.isna(date_val): return False
    try:
        now = datetime.now()
        dt = pd.to_datetime(date_val, dayfirst=True, errors='coerce')
        return dt < now
    except: return False

def find_columns(df):
    std_to_orig = {}
    for col in df.columns:
        c_low = str(col).lower().strip()
        for std, aliases in COLUMN_ALIASES.items():
            if std not in std_to_orig and any(a in c_low for a in aliases):
                std_to_orig[std] = col
    return std_to_orig

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Vietnamese_Fisheries_Surveillance_Logo.png", width=80) # Thay bằng logo nội bộ nếu cần
    st.title("KIỂM NGƯ NH-VN")
    menu = st.radio("MENU CHÍNH", ["🔍 Tra Cứu Thông Tin", "🔄 Đối Chiếu Dữ Liệu", "📊 Lọc & Thống Kê Báo Cáo"])
    
    st.markdown("---")
    # Quản lý CSDL
    st.subheader("Cơ Sở Dữ Liệu")
    uploaded_db = st.file_uploader("Nạp/Cập nhật CSDL (Excel)", type=["xlsx"])
    if uploaded_db:
        with open(DB_FILE, "wb") as f:
            f.write(uploaded_db.getbuffer())
        st.success("Đã cập nhật CSDL mới!")
        st.rerun()
    
    if os.path.exists(DB_FILE):
        mtime = os.path.getmtime(DB_FILE)
        st.info(f"Cập nhật lần cuối:\n{datetime.fromtimestamp(mtime).strftime('%H:%M %d/%m/%Y')}")

# =========================================================
# TRANG 1: TRA CỨU THÔNG TIN
# =========================================================
if menu == "🔍 Tra Cứu Thông Tin":
    st.header("🔍 Hệ Thống Tra Cứu Tàu Cá")
    
    if not os.path.exists(DB_FILE):
        st.warning("Vui lòng nạp file CSDL ở Sidebar bên trái để bắt đầu.")
    else:
        df = pd.read_excel(DB_FILE)
        cols_map = find_columns(df)
        
        # Thanh tìm kiếm
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            query = st.text_input("Nhập số đăng ký hoặc tên chủ tàu:", placeholder="Ví dụ: 90279 hoặc Nguyễn Văn A")
        with search_col2:
            st.write("##") # Offset
            if st.button("Làm mới"): st.rerun()

        if query:
            # Lọc dữ liệu
            mask = df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)
            results = df[mask]
            
            if results.empty:
                st.error("Không tìm thấy dữ liệu phù hợp.")
            else:
                # CHIA ĐỀU 50-50 (Danh sách - Chi tiết)
                list_col, detail_col = st.columns([1, 1])
                
                with list_col:
                    st.subheader("📋 Danh sách kết quả")
                    # Hiển thị bảng rút gọn
                    display_df = results.copy()
                    st.dataframe(display_df, use_container_width=True, height=500)
                    st.caption(f"Tìm thấy {len(results)} kết quả.")

                with detail_col:
                    st.subheader("📄 Chi tiết tàu cá")
                    # Lấy dòng đầu tiên hoặc dòng được chọn (mặc định lấy dòng đầu)
                    row = results.iloc[0]
                    
                    # Tự động lấy các trường dữ liệu
                    dk = row.get(cols_map.get('SO_DANG_KY'), '-')
                    ten = row.get(cols_map.get('CHU_TAU'), '-')
                    sdt = row.get(cols_map.get('SDT'), '-')
                    cccd = row.get(cols_map.get('CCCD'), '-')
                    diachi = row.get(cols_map.get('DIA_CHI'), '-')
                    lmax = row.get(cols_map.get('LMAX'), '-')
                    cs = row.get(cols_map.get('CONG_SUAT'), '-')
                    hdk = row.get(cols_map.get('HAN_DK'), '-')
                    hgp = row.get(cols_map.get('HAN_GP'), '-')
                    
                    xa = get_commune(diachi)
                    
                    # Hiển thị BOX NỔI
                    st.markdown(f"""
                        <div class="detail-card">
                            <div style="background-color: #0d6efd; color: white; padding: 15px; border-radius: 5px 5px 0 0; margin: -20px -20px 20px -20px;">
                                <small>CHI TIẾT TÀU CÁ</small>
                                <h2 style="margin:0; color: white;">{dk}</h2>
                                <span class="location-badge">{xa}</span>
                            </div>
                            <table style="width:100%; border-collapse: collapse;">
                                <tr>
                                    <td style="width:50%; padding: 10px 0;">
                                        <div class="label-text">👤 CHỦ PHƯƠNG TIỆN</div>
                                        <div class="value-text">{ten}</div>
                                    </td>
                                    <td style="width:50%; padding: 10px 0;">
                                        <div class="label-text">💳 SỐ CCCD/CMND</div>
                                        <div class="value-text">{str(cccd).split('.')[0] if pd.notna(cccd) else '-'}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div class="label-text">📞 SỐ ĐIỆN THOẠI</div>
                                        <div class="value-text">{sdt}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div class="label-text">📏 CHIỀU DÀI LMAX</div>
                                        <div class="value-text">{lmax} m</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div class="label-text">⚡ TỔNG CÔNG SUẤT</div>
                                        <div class="value-text">{cs} KW/CV</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div class="label-text">📍 ĐỊA CHỈ THƯỜNG TRÚ</div>
                                        <div class="value-text">{diachi}</div>
                                    </td>
                                </tr>
                            </table>
                            <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; border: 1px solid #eee;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <span class="label-text">🗓️ HẠN GPKTTS:</span>
                                    <span class="{'expired-red' if check_expiry(hgp) else 'valid-green'}">{hgp if pd.notna(hgp) else '-'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span class="label-text">🗓️ HẾT HẠN ĐĂNG KIỂM:</span>
                                    <span class="{'expired-red' if check_expiry(hdk) else 'valid-green'}">{hdk if pd.notna(hdk) else '-'}</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

# =========================================================
# TRANG 2: ĐỐI CHIẾU DỮ LIỆU
# =========================================================
elif menu == "🔄 Đối Chiếu Dữ Liệu":
    st.header("🔄 Đối Chiếu & Cập Nhật Dữ Liệu")
    
    col_src, col_ref = st.columns(2)
    with col_src:
        file_src = st.file_uploader("1. Chọn File Gốc (Cần đắp thêm dữ liệu)", type=["xlsx"])
    with col_ref:
        files_ref = st.file_uploader("2. Chọn (các) File Đích để tham chiếu", type=["xlsx"], accept_multiple_files=True)
    
    if file_src and files_ref:
        df_src = pd.read_excel(file_src)
        # Gộp các file đích
        df_refs = [pd.read_excel(f) for f in files_ref]
        df_ref_all = pd.concat(df_refs, ignore_index=True)
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            key_src = st.selectbox("Cột nối của File Gốc (Số ĐK):", df_src.columns)
        with c2:
            key_ref = st.selectbox("Cột nối của File Đích (Số ĐK):", df_ref_all.columns)
        
        vals_to_get = st.multiselect("Chọn các cột muốn lấy từ File Đích sang:", [c for c in df_ref_all.columns if c != key_ref])
        
        if st.button("▶ BẮT ĐẦU ĐỐI CHIẾU"):
            with st.spinner("Đang xử lý..."):
                df_src['_key'] = df_src[key_src].astype(str).str.strip().str.upper()
                df_ref_all['_key'] = df_ref_all[key_ref].astype(str).str.strip().str.upper()
                df_ref_unique = df_ref_all.drop_duplicates(subset=['_key'])
                
                df_final = pd.merge(df_src, df_ref_unique[['_key'] + vals_to_get], on='_key', how='left')
                df_final.drop(columns=['_key'], inplace=True)
                
                # Download
                output = BytesIO()
                df_final.to_excel(output, index=False)
                st.success("Đối chiếu thành công!")
                st.download_button("📥 Tải File Kết Quả", output.getvalue(), file_name=f"Doi_chieu_{datetime.now().strftime('%d%m%Y')}.xlsx")

# =========================================================
# TRANG 3: LỌC & THỐNG KÊ
# =========================================================
elif menu == "📊 Lọc & Thống Kê Báo Cáo":
    st.header("📊 Lọc Dữ Liệu Tàu Cá & Xuất Báo Cáo")
    
    file_input = st.file_uploader("Chọn File Excel đầu vào:", type=["xlsx"])
    if file_input:
        df = pd.read_excel(file_input)
        cmap = find_columns(df)
        
        st.markdown("---")
        loc_choice = st.selectbox("Chọn địa phương cần lọc:", ["Tất cả"] + list(mapping_rules.keys()))
        date_col = st.selectbox("Chọn cột tính hạn (Đăng kiểm/GP):", df.columns, index=list(df.columns).index(cmap.get('HAN_DK')) if cmap.get('HAN_DK') in df.columns else 0)
        
        split_sheets = st.checkbox("Tách mỗi địa phương thành một Sheet riêng (Trong danh sách hết hạn)")
        
        if st.button("▶ XUẤT BÁO CÁO EXCEL"):
            with st.spinner("Đang phân tích và lập báo cáo..."):
                df['Xã/Phường mới'] = df[cmap.get('DIA_CHI', df.columns[0])].apply(get_commune)
                df_filtered = df if loc_choice == "Tất cả" else df[df['Xã/Phường mới'] == loc_choice]
                
                # Tách tàu hết hạn
                df_filtered['_expired'] = df_filtered[date_col].apply(check_expiry)
                df_expired = df_filtered[df_filtered['_expired'] == True].copy()
                
                # Xuất file
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtered.drop(columns=['_expired']).to_excel(writer, sheet_name="Danh sách chi tiết", index=False)
                    
                    if not df_expired.empty:
                        df_expired.drop(columns=['_expired']).to_excel(writer, sheet_name="Tổng Tàu Hết Hạn", index=False)
                        if split_sheets:
                            for loc in df_expired['Xã/Phường mới'].unique():
                                df_loc = df_expired[df_expired['Xã/Phường mới'] == loc].drop(columns=['_expired'])
                                df_loc.to_excel(writer, sheet_name=f"HH_{loc[:20]}", index=False)
                
                st.success("Báo cáo đã sẵn sàng!")
                st.download_button("📥 Tải Báo Cáo (3+ Sheets)", output.getvalue(), file_name=f"Bao_cao_Tau_ca_{datetime.now().strftime('%d%m%Y')}.xlsx")
