import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

# =========================================================
# CẤU HÌNH TRANG & GIAO DIỆN (DASHBOARD CHUẨN WEB)
# =========================================================
st.set_page_config(page_title="Quản lý Tàu cá NHVN", layout="wide", page_icon="🚢")

# Custom CSS giao diện chuyên nghiệp
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #3498db; color: white; font-weight: bold; }
    .btn-success>button { background-color: #198754 !important; }
    .btn-warning>button { background-color: #ff9800 !important; }
    
    /* Box Nổi Thẻ Thông Tin */
    .vessel-card {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        overflow: hidden;
    }
    .card-header {
        background-color: #0d6efd;
        color: white;
        padding: 20px;
    }
    .card-header h4 { color: white; margin: 0; font-size: 14px; font-weight: bold; }
    .card-header h2 { color: white; margin: 5px 0 10px 0; font-size: 28px; font-weight: bold; }
    .badge-loc {
        background-color: white; color: #212529; padding: 5px 12px;
        border-radius: 15px; font-size: 12px; font-weight: bold; display: inline-block;
    }
    .card-body { padding: 20px; }
    .info-row { display: grid; grid-template-columns: 1fr 1fr; border-bottom: 1px solid #f8f9fa; padding-bottom: 10px; margin-bottom: 10px; }
    .info-label { color: #6c757d; font-size: 13px; font-weight: bold; margin-bottom: 2px; }
    .info-val { color: #212529; font-size: 15px; font-weight: bold; }
    .date-box {
        background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;
        padding: 12px 15px; display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 10px;
    }
    .date-label { color: #6c757d; font-size: 13px; font-weight: bold; margin: 0; }
    .date-val { font-size: 14px; font-weight: bold; margin: 0; }
    .val-valid { color: #198754; }
    .val-expired { color: #dc3545; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# TỪ ĐIỂN AI & BIẾN TOÀN CỤC
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

GLOBAL_EXCLUDES = ["phú yên", "ninh thuận", "bình thuận", "đắk lắk", "lâm đồng", "tp.hcm", "hồ chí minh", "hà nội", "đà nẵng", "quảng nam", "quảng ngãi", "bình định"]
KH_EXCLUDES = ["nha trang", "cam ranh", "diên khánh", "cam lâm", "khánh vĩnh", "khánh sơn", "xã ninh hải"]
mapping_rules = {
    "Xã Đại Lãnh": {"keywords": ["vạn thạnh", "vạn thọ", "đại lãnh"], "exclude": KH_EXCLUDES},
    "Xã Tu Bông": {"keywords": ["vạn khánh", "vạn long", "vạn phước", "tu bông"], "exclude": KH_EXCLUDES},
    "Xã Vạn Hưng": {"keywords": ["xuân sơn", "vạn hưng"], "exclude": KH_EXCLUDES},
    "Xã Vạn Ninh": {"keywords": ["vạn giã", "tt vạn giã", "thị trấn vạn giã", "vạn phú", "vạn lương", "xã vạn ninh"], "exclude": KH_EXCLUDES},
    "Xã Vạn Thắng": {"keywords": ["vạn bình", "vạn thắng"], "exclude": KH_EXCLUDES},
    "Phường Đông Ninh Hoà": {"keywords": ["ninh diêm", "ninh hải", "ninh thủy", "ninh thuỷ", "ninh phước", "ninh vân", "đông ninh hòa", "đông ninh hoà"], "exclude": KH_EXCLUDES},
    "Phường Hoà Thắng": {"keywords": ["ninh giang", "ninh hà", "ninh phú", "hòa thắng", "hoà thắng"], "exclude": KH_EXCLUDES},
    "Xã Bắc Ninh Hoà": {"keywords": ["ninh an", "ninh sơn", "ninh thọ", "bắc ninh hòa", "bắc ninh hoà"], "exclude": KH_EXCLUDES},
    "Xã Nam Ninh Hoà": {"keywords": ["ninh lộc", "ninh ích", "ninh hưng", "ninh tân", "nam ninh hòa", "nam ninh hoà"], "exclude": KH_EXCLUDES},
    "Bắc Nha Trang": {"keywords": ["lương sơn", "vĩnh lương", "văn đăng", "cát lợi", "võ tánh", "phạm văn đồng"], "exclude": ["ninh hòa", "ninh hoà", "vạn ninh", "cam ranh", "diên khánh", "cam lâm"]}
}

T3_COL_MAP = {
    "Số đăng ký": "SO_DANG_KY", "Tên chủ tàu": "CHU_TAU", "SĐT": "SDT", "CCCD": "CCCD",
    "Địa chỉ": "DIA_CHI", "Lmax": "LMAX", "Công suất": "CONG_SUAT", "Hạn Đăng kiểm": "HAN_DK", "Hạn GPKTTS": "HAN_GP"
}

# =========================================================
# CÁC HÀM XỬ LÝ LÕI (AI QUÉT TIÊU ĐỀ)
# =========================================================

def read_excel_auto_header(file_obj):
    """Hàm AI Tự động quét và tìm dòng Tiêu đề chuẩn trong File Excel báo cáo"""
    file_obj.seek(0)
    df_temp = pd.read_excel(file_obj, header=None, nrows=50)
    best_idx = 0
    max_valid_cells = 0
    
    for i, row in df_temp.iterrows():
        valid_cells = sum(1 for x in row.values if pd.notna(x) and str(x).strip() != '')
        if valid_cells > max_valid_cells:
            max_valid_cells = valid_cells
            best_idx = i
            
    file_obj.seek(0)
    df = pd.read_excel(file_obj, header=best_idx)
    df.columns = df.columns.astype(str).str.strip()
    return df

def map_columns(df_columns):
    mapping = {}
    for std_name, alias_list in COLUMN_ALIASES.items():
        for col in df_columns:
            if any(alias in str(col).lower().strip() for alias in alias_list):
                mapping[std_name] = str(col).strip(); break
    return mapping

def get_new_address(old_address):
    if pd.isna(old_address) or str(old_address).strip() == 'nan': return None
    address_str = str(old_address).lower()
    for exc in GLOBAL_EXCLUDES:
        if exc in address_str: return None 
    for new_name, rule in mapping_rules.items():
        is_excluded = False
        for ex_word in rule["exclude"]:
            if ex_word in address_str: is_excluded = True; break
        if is_excluded: continue 
        for keyword in rule["keywords"]:
            if keyword in address_str: return new_name
    return None

def check_expired(date_str):
    if not date_str or date_str == '-': return False
    try:
        if '/' in date_str: return datetime.strptime(date_str, '%d/%m/%Y') < datetime.now()
        elif '-' in date_str: return datetime.strptime(date_str, '%Y-%m-%d') < datetime.now()
    except: return False
    return False

# Lưu trữ Session State để dùng trên Web
if 'db_df' not in st.session_state: st.session_state.db_df = None
if 'db_mapping' not in st.session_state: st.session_state.db_mapping = {}
if 'last_update' not in st.session_state: st.session_state.last_update = None

# =========================================================
# SIDEBAR ĐIỀU HƯỚNG
# =========================================================
with st.sidebar:
    try:
        st.image("logo_kiem_ngu.png", width=90)
    except:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Vietnam_Fisheries_Surveillance_Logo.svg/1200px-Vietnam_Fisheries_Surveillance_Logo.svg.png", width=90)
    
    st.markdown("### QUẢN LÝ TÀU CÁ")
    st.markdown("---")
    menu = st.radio("MENU CHÍNH", ["🔍 Tra cứu thông tin", "🔄 Đối chiếu dữ liệu", "📊 Lọc & Xuất báo cáo"])
    st.markdown("---")
    st.caption("© 2026 - Chi cục Thủy sản NHVN")


# =========================================================
# TRANG 1: TRA CỨU THÔNG TIN
# =========================================================
if menu == "🔍 Tra cứu thông tin":
    st.header("TRA CỨU THÔNG TIN TÀU CÁ")
    
    # Khung Nạp CSDL
    with st.expander("📁 Cập nhật Cơ sở dữ liệu (Nạp file Excel)", expanded=st.session_state.db_df is None):
        uploaded_db = st.file_uploader("Chọn file dữ liệu để tra cứu", type=["xlsx", "xls"], key="db_uploader")
        if uploaded_db:
            df = read_excel_auto_header(uploaded_db)
            st.session_state.db_df = df
            st.session_state.db_mapping = map_columns(df.columns)
            st.session_state.last_update = datetime.now().strftime('%H:%M %d/%m/%Y')
            st.success(f"Đã nạp {len(df)} tàu thành công!")
            st.rerun()

    # Khung Tìm kiếm
    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
    with col_s1: keyword = st.text_input("Nhập từ khóa:", placeholder="Số đăng ký hoặc tên chủ tàu...")
    with col_s2: search_type = st.selectbox("Tìm theo", ["Tất cả", "Số đăng ký", "Tên chủ tàu"])
    with col_s3: 
        st.write("##")
        btn_search = st.button("🔍 TÌM KIẾM")

    if st.session_state.last_update:
        st.caption(f"Trạng thái: Đã tải dữ liệu (Cập nhật: {st.session_state.last_update})")

    # Xử lý Tìm kiếm
    if btn_search or keyword:
        if st.session_state.db_df is None:
            st.warning("Vui lòng Nạp file Cơ sở dữ liệu trước!")
        else:
            df_search = st.session_state.db_df
            mmap = st.session_state.db_mapping
            
            col_dk = mmap.get('SO_DANG_KY')
            col_ten = mmap.get('CHU_TAU')
            
            if search_type == "Số đăng ký" and col_dk:
                res = df_search[df_search[col_dk].astype(str).str.lower().str.contains(keyword.lower(), na=False)]
            elif search_type == "Tên chủ tàu" and col_ten:
                res = df_search[df_search[col_ten].astype(str).str.lower().str.contains(keyword.lower(), na=False)]
            else:
                mask = df_search.apply(lambda row: row.astype(str).str.lower().str.contains(keyword.lower(), na=False).any(), axis=1)
                res = df_search[mask]

            if res.empty:
                st.info(f"Không tìm thấy kết quả cho: '{keyword}'")
            else:
                # CHIA ĐÔI MÀN HÌNH 50 - 50
                left_col, right_col = st.columns([1.2, 1])
                
                # --- TRÁI: BẢNG DANH SÁCH ---
                with left_col:
                    st.markdown("**DANH SÁCH KẾT QUẢ**")
                    
                    disp_cols = []
                    disp_data = []
                    
                    for idx, row in res.iterrows():
                        item = {}
                        for title, alias in T3_COL_MAP.items():
                            orig_c = mmap.get(alias)
                            val = row[orig_c] if orig_c and orig_c in res.columns else None
                            
                            if pd.notna(val) and not isinstance(val, (datetime, pd.Timestamp)) and alias not in ['SDT', 'CCCD', 'HAN_GP', 'HAN_DK']:
                                if str(val).endswith('.0'): val = str(val)[:-2]
                            if alias == 'CCCD' and pd.notna(val):
                                v_str = str(val).strip().split('.')[0]
                                if v_str.isdigit(): val = v_str.zfill(12)
                            elif alias == 'SDT' and pd.notna(val):
                                v_str = str(val).strip().split('.')[0]
                                if v_str.isdigit() and len(v_str) >= 9 and v_str[0] != '0': val = '0' + v_str
                            elif alias in ['HAN_GP', 'HAN_DK'] and pd.notna(val):
                                try:
                                    parsed = pd.to_datetime(val, errors='coerce', dayfirst=True)
                                    if pd.notna(parsed): val = parsed.strftime('%d/%m/%Y')
                                    else: val = str(val).split(' ')[0].strip()
                                except: pass
                            item[title] = str(val) if pd.notna(val) else "-"
                        
                        dc_col = mmap.get('DIA_CHI')
                        item['Địa phương'] = get_new_address(row[dc_col]) if dc_col and dc_col in res.columns else "-"
                        
                        disp_data.append(item)
                    
                    df_display = pd.DataFrame(disp_data)
                    
                    selected_vessel = st.selectbox("Chọn tàu để xem chi tiết:", df_display['Số đăng ký'].tolist())
                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                # --- PHẢI: BOX NỔI THẺ THÔNG TIN ---
                with right_col:
                    st.markdown("**THẺ CHI TIẾT**")
                    if selected_vessel:
                        selected_item = df_display[df_display['Số đăng ký'] == selected_vessel].iloc[0]
                        
                        loc_str = selected_item['Địa phương'] if selected_item['Địa phương'] != "-" else "CHƯA XÁC ĐỊNH"
                        lmax_str = f"{selected_item['Lmax']} m" if selected_item['Lmax'] != "-" else "-"
                        cs_str = f"{selected_item['Công suất']} KW" if selected_item['Công suất'] != "-" else "-"
                        
                        hdk_str = selected_item['Hạn Đăng kiểm']
                        hgp_str = selected_item['Hạn GPKTTS']
                        
                        hdk_class = "val-expired" if check_expired(hdk_str) else "val-valid"
                        hgp_class = "val-expired" if check_expired(hgp_str) else "val-valid"
                        
                        html_card = f"""
                        <div class="vessel-card">
                            <div class="card-header">
                                <h4>CHI TIẾT TÀU CÁ</h4>
                                <h2>{selected_item['Số đăng ký']}</h2>
                                <span class="badge-loc">{loc_str}</span>
                            </div>
                            <div class="card-body">
                                <div class="info-row">
                                    <div><p class="info-label">👤 CHỦ PHƯƠNG TIỆN</p><p class="info-val">{selected_item['Tên chủ tàu']}</p></div>
                                    <div><p class="info-label">💳 SỐ CCCD/CMND</p><p class="info-val">{selected_item['CCCD']}</p></div>
                                </div>
                                <div class="info-row">
                                    <div><p class="info-label">📞 SỐ ĐIỆN THOẠI</p><p class="info-val">{selected_item['SĐT']}</p></div>
                                    <div><p class="info-label">📏 LMAX</p><p class="info-val">{lmax_str}</p></div>
                                </div>
                                <div class="info-row" style="border-bottom:none;">
                                    <div><p class="info-label">⚡ CÔNG SUẤT</p><p class="info-val">{cs_str}</p></div>
                                    <div><p class="info-label">📍 ĐỊA CHỈ</p><p class="info-val">{selected_item['Địa chỉ']}</p></div>
                                </div>
                                
                                <div style="margin-top:20px;">
                                    <div class="date-box">
                                        <p class="date-label">🗓 HẠN GIẤY PHÉP KTTS</p>
                                        <p class="date-val {hgp_class}">{hgp_str}</p>
                                    </div>
                                    <div class="date-box">
                                        <p class="date-label">🗓 NGÀY HẾT HẠN ĐĂNG KIỂM</p>
                                        <p class="date-val {hdk_class}">{hdk_str}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(html_card, unsafe_allow_html=True)


# =========================================================
# TRANG 2: ĐỐI CHIẾU DỮ LIỆU ĐA FILE
# =========================================================
elif menu == "🔄 Đối chiếu dữ liệu":
    st.header("ĐỐI CHIẾU VÀ ĐẮP DỮ LIỆU")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. File Gốc (Cần đắp thêm)")
        src_file = st.file_uploader("Tải lên File gốc", type=["xlsx", "xls"], key="src_upload")
    with col2:
        st.subheader("2. File Đích (Nguồn đối chiếu)")
        tgt_files = st.file_uploader("Tải lên 1 hoặc nhiều File Đích", type=["xlsx", "xls"], accept_multiple_files=True, key="tgt_upload")

    if src_file and tgt_files:
        st.markdown("### 3. Thiết lập Đối chiếu")
        
        # Dùng AI đọc file gốc
        df_src = read_excel_auto_header(src_file)
        cols_src = list(df_src.columns)
        
        # Gộp cột từ các file đích
        cols_tgt = []
        for f in tgt_files:
            temp_df = read_excel_auto_header(f)
            for c in temp_df.columns:
                c_str = str(c).strip()
                if c_str not in cols_tgt and not c_str.lower().startswith('unnamed'): cols_tgt.append(c_str)

        cc1, cc2 = st.columns(2)
        with cc1: key_src = st.selectbox("Cột Nối của File Gốc:", cols_src)
        with cc2: key_tgt = st.selectbox("Cột Nối của File Đích:", ["<Tự động nhận diện bằng AI>"] + cols_tgt)
        
        vals_to_get = st.multiselect("Chọn (các) Cột muốn lấy từ File Đích mang sang:", cols_tgt)

        st.markdown('<div class="btn-warning">', unsafe_allow_html=True)
        if st.button("▶ CHẠY ĐỐI CHIẾU"):
            if not vals_to_get:
                st.warning("Vui lòng chọn ít nhất 1 cột cần lấy!")
            else:
                with st.spinner("Đang tiến hành đối chiếu thông minh..."):
                    df_src['_key_match'] = df_src[key_src].astype(str).str.strip().str.upper()
                    
                    for file_idx, t_file in enumerate(tgt_files):
                        df_t = read_excel_auto_header(t_file)
                        
                        local_key = None
                        if key_tgt == "<Tự động nhận diện bằng AI>":
                            m_t = map_columns(df_t.columns)
                            local_key = m_t.get('SO_DANG_KY')
                        else:
                            local_key = key_tgt if key_tgt in df_t.columns else None

                        if not local_key: continue
                        
                        local_vals = [c for c in vals_to_get if c in df_t.columns]
                        if not local_vals: continue

                        df_t['_key_match'] = df_t[local_key].astype(str).str.strip().str.upper()
                        df_t_unique = df_t.drop_duplicates(subset=['_key_match'])

                        short_fname = t_file.name.split('.')[0][:15]
                        rename_dict = {c: f"{c} ({short_fname}...)" for c in local_vals}
                        df_t_sub = df_t_unique[['_key_match'] + local_vals].rename(columns=rename_dict)

                        df_src = pd.merge(df_src, df_t_sub, on='_key_match', how='left')

                    df_src.drop(columns=['_key_match'], inplace=True)
                    
                    st.success("✅ Đã đối chiếu và đắp dữ liệu thành công!")
                    
                    output = io.BytesIO()
                    df_src.to_excel(output, index=False, engine='openpyxl')
                    st.download_button(label="📥 TẢI FILE KẾT QUẢ", data=output.getvalue(), file_name=f"Ket_qua_Doi_chieu_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# TRANG 3: LỌC BÁO CÁO VÀ DASHBOARD PREVIEW
# =========================================================
elif menu == "📊 Lọc & Xuất báo cáo":
    st.header("LỌC DỮ LIỆU & XUẤT BÁO CÁO")
    
    upload_filter = st.file_uploader("1. Tải lên File Dữ liệu cần lọc", type=["xlsx", "xls"], key="filter_upload")
    
    if upload_filter:
        df_raw = read_excel_auto_header(upload_filter)
        all_cols = list(df_raw.columns)
        mmap = map_columns(all_cols)
        
        st.markdown("---")
        st.markdown("### 2. Thiết lập xuất báo cáo")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            default_cols = [c for c in all_cols if c in mmap.values()]
            selected_cols = st.multiselect("Cột sẽ xuất ra báo cáo:", all_cols, default=default_cols)
            
            commune_opts = ["Tất cả", "Xã Đại Lãnh", "Xã Tu Bông", "Xã Vạn Hưng", "Xã Vạn Ninh", "Xã Vạn Thắng", "Phường Đông Ninh Hoà", "Phường Hoà Thắng", "Xã Bắc Ninh Hoà", "Xã Nam Ninh Hoà", "Bắc Nha Trang"]
            selected_commune = st.selectbox("Lọc theo Địa phương:", commune_opts)
            
        with col_c2:
            default_date_col = 0
            if 'HAN_DK' in mmap: default_date_col = all_cols.index(mmap['HAN_DK'])
            elif 'HAN_GP' in mmap: default_date_col = all_cols.index(mmap['HAN_GP'])
            
            selected_date_col = st.selectbox("Cột Mốc Tính Hạn:", all_cols, index=default_date_col)
            selected_date = st.text_input("Lọc đến ngày (Bỏ trống lấy tất cả):", placeholder="VD: 30/06/2026")
            
            split_expired = st.checkbox("Tách mỗi Xã/Phường thành 1 Sheet (Đối với Tàu Hết hạn)")
            
        st.markdown('<div class="btn-success">', unsafe_allow_html=True)
        if st.button("▶ XEM TRƯỚC DASHBOARD & XUẤT BÁO CÁO"):
            with st.spinner("Hệ thống AI đang xử lý dữ liệu..."):
                col_diachi_goc = mmap.get('DIA_CHI', '')
                if not col_diachi_goc:
                    st.error("Không tìm thấy Cột Địa chỉ trong file!")
                else:
                    df_raw['Xã/Phường mới'] = df_raw[col_diachi_goc].apply(get_new_address)
                    df_filtered = df_raw[df_raw['Xã/Phường mới'].notna()].copy()
                    if selected_commune != "Tất cả": df_filtered = df_filtered[df_filtered['Xã/Phường mới'] == selected_commune]

                    col_cccd = mmap.get('CCCD', '')
                    if col_cccd and col_cccd in df_filtered.columns:
                        def format_cccd_export(x):
                            if pd.isna(x): return x
                            v_str = str(x).strip().split('.')[0]
                            if v_str.lower() in ['nan', 'none', ''] or not v_str.isdigit(): return x
                            return v_str.zfill(12) 
                        df_filtered[col_cccd] = df_filtered[col_cccd].apply(format_cccd_export)

                    parsed_dates = pd.to_datetime(df_filtered[selected_date_col], dayfirst=True, errors='coerce')
                    mask_old = (parsed_dates.dt.year < 1950) & parsed_dates.notna()
                    if mask_old.any(): parsed_dates.loc[mask_old] = parsed_dates.loc[mask_old].apply(lambda x: x.replace(year=x.year + 100))
                    df_filtered['Ngày_dt_temp'] = parsed_dates
                    
                    if selected_date != "":
                        target_date = pd.to_datetime(selected_date, dayfirst=True)
                        df_filtered = df_filtered[df_filtered['Ngày_dt_temp'] <= target_date]

                    if len(df_filtered) == 0:
                        st.warning("Không có tàu nào thỏa mãn điều kiện lọc!")
                    else:
                        final_dict = {col: df_filtered[col] for col in selected_cols if col in df_filtered.columns}
                        df_final = pd.DataFrame(final_dict)
                        df_final.insert(0, 'TT', range(1, len(df_final) + 1))

                        current_date = pd.Timestamp.now().normalize()
                        df_filtered['_da_het_han'] = df_filtered['Ngày_dt_temp'] < current_date

                        df_filtered['Lmax_num'] = pd.to_numeric(df_filtered[mmap.get('LMAX', '')], errors='coerce') if 'LMAX' in mmap else None

                        def phan_loai_lmax(lmax):
                            if pd.isna(lmax): return 'Không rõ'
                            if lmax < 6: return '<6'
                            elif 6 <= lmax < 12: return '6 đến <12'
                            elif 12 <= lmax < 15: return '12 đến <15'
                            elif 15 <= lmax < 24: return '15 đến <24'
                            else: return '>=24'

                        df_filtered['Nhom_Lmax'] = df_filtered['Lmax_num'].apply(phan_loai_lmax)
                        col_id = mmap.get('SO_DANG_KY', df_filtered.columns[0])
                        df_thong_ke_main = df_filtered.groupby('Xã/Phường mới').agg(Tong_tau=(col_id, 'count'), Tau_het_han=('_da_het_han', 'sum')).reset_index()
                        lmax_pivot = pd.crosstab(df_filtered['Xã/Phường mới'], df_filtered['Nhom_Lmax']).reset_index()
                        df_thong_ke = pd.merge(df_thong_ke_main, lmax_pivot, on='Xã/Phường mới', how='left')

                        for col in ['<6', '6 đến <12', '12 đến <15', '15 đến <24', '>=24', 'Không rõ']:
                            if col not in df_thong_ke.columns: df_thong_ke[col] = 0

                        df_thong_ke.rename(columns={'Tong_tau': 'Tổng số tàu', 'Tau_het_han': 'Tàu hết hạn'}, inplace=True)
                        final_cols_tk = ['Xã/Phường mới', 'Tổng số tàu', 'Tàu hết hạn']
                        if df_thong_ke['<6'].sum() > 0: final_cols_tk.append('<6')
                        final_cols_tk.extend(['6 đến <12', '12 đến <15', '15 đến <24', '>=24'])
                        if df_thong_ke['Không rõ'].sum() > 0: final_cols_tk.append('Không rõ')
                        df_thong_ke = df_thong_ke[final_cols_tk]

                        tong_cong_row = {'Xã/Phường mới': 'TỔNG CỘNG'}
                        for col in df_thong_ke.columns:
                            if col != 'Xã/Phường mới': tong_cong_row[col] = df_thong_ke[col].sum()
                        df_thong_ke = pd.concat([df_thong_ke, pd.DataFrame([tong_cong_row])], ignore_index=True)

                        df_het_han_full = df_filtered[df_filtered['_da_het_han'] == True].copy()
                        cols_to_export_hh = [c for c in selected_cols if c in df_het_han_full.columns]
                        if selected_date_col not in cols_to_export_hh and selected_date_col in df_het_han_full.columns: cols_to_export_hh.append(selected_date_col)
                        df_het_han_export = df_het_han_full[cols_to_export_hh].copy()
                        if not df_het_han_export.empty: df_het_han_export.insert(0, 'TT', range(1, len(df_het_han_export) + 1))

                        # ===================
                        # DASHBOARD PREVIEW 
                        # ===================
                        st.markdown("---")
                        st.markdown("### 📊 DASHBOARD TỔNG HỢP")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("TỔNG SỐ TÀU LỌC ĐƯỢC", tong_cong_row['Tổng số tàu'])
                        m2.metric("SỐ TÀU ĐÃ HẾT HẠN", tong_cong_row['Tàu hết hạn'])
                        tyle = round((tong_cong_row['Tàu hết hạn'] / tong_cong_row['Tổng số tàu'] * 100), 1) if tong_cong_row['Tổng số tàu'] > 0 else 0
                        m3.metric("TỶ LỆ HẾT HẠN", f"{tyle}%")
                        
                        st.dataframe(df_thong_ke, use_container_width=True, hide_index=True)

                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_final.to_excel(writer, sheet_name='Danh sách chi tiết', index=False)
                            df_thong_ke.to_excel(writer, sheet_name='Bảng thống kê', index=False)
                            
                            if not df_het_han_export.empty: 
                                df_het_han_export.to_excel(writer, sheet_name='Tàu Hết Hạn (Tổng)', index=False)
                                if split_expired:
                                    unique_locs = df_het_han_full['Xã/Phường mới'].dropna().unique()
                                    for loc in unique_locs:
                                        df_loc = df_het_han_full[df_het_han_full['Xã/Phường mới'] == loc].copy()
                                        df_loc_export = df_loc[cols_to_export_hh].copy()
                                        df_loc_export.insert(0, 'TT', range(1, len(df_loc_export) + 1))
                                        sn = f"HH_{str(loc).replace('/', '_').replace(chr(92), '_')}"[:31] 
                                        df_loc_export.to_excel(writer, sheet_name=sn, index=False)
                        
                        st.download_button(label="📥 XÁC NHẬN TẢI BÁO CÁO EXCEL", data=output.getvalue(), file_name=f"Bao_Cao_Loc_TauCa_{datetime.now().strftime('%d%m%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.markdown('</div>', unsafe_allow_html=True)
