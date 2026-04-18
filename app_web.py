import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
import qrcode
import zipfile

# =========================================================
# CẤU HÌNH TRANG & GIAO DIỆN
# =========================================================
st.set_page_config(page_title="Quản lý Tàu cá NHVN", layout="wide", page_icon="🚢")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #3498db; color: white; font-weight: bold; }
    .btn-success>button { background-color: #198754 !important; }
    .btn-warning>button { background-color: #ff9800 !important; }
    .btn-danger>button { background-color: #dc3545 !important; }
    
    /* Box Nổi Thẻ Thông Tin Desktop */
    .vessel-card { background-color: white; border-radius: 8px; border: 1px solid #dee2e6; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; }
    .card-header { background-color: #0d6efd; color: white; padding: 20px; }
    .card-header h4 { color: white; margin: 0; font-size: 14px; font-weight: bold; }
    .card-header h2 { color: white; margin: 5px 0 10px 0; font-size: 28px; font-weight: bold; }
    .badge-loc { background-color: white; color: #212529; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: bold; display: inline-block; }
    .card-body { padding: 20px; }
    .info-row { display: grid; grid-template-columns: 1fr 1fr; border-bottom: 1px solid #f8f9fa; padding-bottom: 10px; margin-bottom: 10px; }
    .info-label { color: #6c757d; font-size: 13px; font-weight: bold; margin-bottom: 2px; }
    .info-val { color: #212529; font-size: 15px; font-weight: bold; word-wrap: break-word; white-space: normal; }
    .date-box { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .date-label { color: #6c757d; font-size: 13px; font-weight: bold; margin: 0; }
    .date-val { font-size: 14px; font-weight: bold; margin: 0; }
    .val-valid { color: #198754; }
    .val-expired { color: #dc3545; }
    
    /* Giao diện Mobile cho Cán bộ tuần tra */
    .mobile-container { max-width: 480px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); overflow: hidden; font-family: sans-serif; border: 1px solid #e9ecef;}
    .m-header { background: linear-gradient(135deg, #0d6efd, #0a58ca); color: white; padding: 25px 20px; text-align: center; }
    .m-header h4 { margin: 0; font-size: 12px; letter-spacing: 1px; opacity: 0.8; text-transform: uppercase; }
    .m-header h1 { margin: 5px 0 0 0; font-size: 32px; letter-spacing: 2px; font-weight: 900;}
    .m-body { padding: 20px; }
    .m-section { margin-bottom: 20px; }
    .m-title { font-size: 16px; color: #0d6efd; border-bottom: 2px solid #e9ecef; padding-bottom: 5px; margin-bottom: 15px; font-weight: bold; display:flex; align-items: center; gap: 8px;}
    .m-row { display: flex; flex-direction: column; margin-bottom: 12px; }
    .m-label { font-size: 12px; color: #6c757d; font-weight: bold; text-transform: uppercase; margin-bottom: 2px;}
    .m-val { font-size: 16px; color: #212529; font-weight: bold; word-wrap: break-word; white-space: normal;}
    .m-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 12px;}
    .m-badge { background: #e9ecef; color: #495057; padding: 5px 10px; border-radius: 6px; font-size: 14px; font-weight: bold; display: inline-block; margin-top:5px;}
    .m-alert-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; text-align: center;}
    .m-alert-green { background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc;}
    .m-alert-red { background-color: #f8d7da; color: #842029; border: 1px solid #f5c2c7;}
    .m-alert-title { font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; opacity: 0.8;}
    .m-alert-val { font-size: 18px; font-weight: 900; margin: 0;}
    
    .data-card { background: white; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LÕI DỮ LIỆU & AI
# =========================================================
DB_FILE = "CSDL_TauCa_Master.xlsx"
QR_LOG_FILE = "Da_Tao_QR_Log.txt"

COLUMN_ALIASES = {
    'SO_DANG_KY': ['số đăng ký', 'biển số', 'số đk'],
    'CHU_TAU': ['chủ tàu', 'chủ phương tiện', 'họ tên chủ', 'tên chủ'],
    'SDT': ['số điện thoại', 'sđt', 'sdt', 'điện thoại'],
    'CCCD': ['cccd', 'cmnd', 'căn cước', 'chứng minh', 'số định danh', 'số cmnd'],
    'DIA_CHI': ['địa chỉ', 'nơi thường trú', 'địa chỉ thường trú', 'chỗ ở', 'địa chỉ chủ'],
    'LMAX': ['chiều dài lmax', 'lmax', 'chiều dài lớn nhất', 'l max', 'chiều dài'],
    'CONG_SUAT': ['công suất', 'cv', 'kw', 'máy chính'],
    'NGHE': ['nghề', 'nghề khai thác', 'nghề nghiệp', 'hoạt động'],
    'HAN_DK': ['hạn đăng kiểm', 'hết hạn đk', 'ngày hết hạn đăng kiểm (dd/mm/yyyy)', 'ngày hết hạn đăng kiểm', 'hạn đk'],
    'HAN_GP': ['hạn giấy phép', 'hạn gp', 'hết hạn gp', 'hạn gpktts', 'giấy phép ktts', 'ngày hết hạn (đối chiếu)', 'ngày hết hạn']
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

def read_excel_auto_header(file_obj_or_path):
    if isinstance(file_obj_or_path, str):
        with open(file_obj_or_path, 'rb') as f: data = f.read()
        file_obj = io.BytesIO(data)
    else:
        file_obj_or_path.seek(0); file_obj = file_obj_or_path

    df_temp = pd.read_excel(file_obj, header=None, nrows=50)
    best_idx = 0; max_valid_cells = 0
    for i, row in df_temp.iterrows():
        valid_cells = sum(1 for x in row.values if pd.notna(x) and str(x).strip() != '')
        if valid_cells > max_valid_cells: max_valid_cells = valid_cells; best_idx = i
            
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

def generate_qr_code(vessel_id, base_url):
    url = f"{base_url}/?tau={vessel_id}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d6efd", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def load_master_db():
    if os.path.exists(DB_FILE):
        df = read_excel_auto_header(DB_FILE)
        return df, map_columns(df.columns)
    return None, {}


# =========================================================
# CHẾ ĐỘ QUÉT MÃ QR BẰNG ĐIỆN THOẠI (OFFICER MOBILE VIEW)
# =========================================================
params = st.query_params
if "tau" in params:
    vessel_id = str(params["tau"]).strip().upper()
    df_db, mmap = load_master_db()
    
    if df_db is None:
        st.error("⚠️ Máy chủ chưa được nạp Dữ liệu gốc. Vui lòng liên hệ Admin.")
        st.stop()
        
    col_dk = mmap.get('SO_DANG_KY')
    if not col_dk:
        st.error("⚠️ CSDL lỗi cấu trúc.")
        st.stop()
        
    vessel_data = df_db[df_db[col_dk].astype(str).str.strip().str.upper() == vessel_id]
    
    if vessel_data.empty:
        st.error(f"❌ Không tìm thấy dữ liệu cho tàu: {vessel_id}")
        st.stop()
        
    row = vessel_data.iloc[0]
    
    def _v(alias, is_id=False):
        c = mmap.get(alias)
        if not c or c not in df_db.columns: return "-"
        val = row[c]
        if pd.isna(val) or str(val).lower() in ['nan', 'none', 'nat']: return "-"
        if is_id:
            s = str(val).split('.')[0].strip()
            if alias == 'CCCD': return s.zfill(12) if s.isdigit() else s
            if alias == 'SDT': return ('0' + s) if s.isdigit() and not s.startswith('0') else s
        if alias in ['HAN_GP', 'HAN_DK']:
            try:
                p = pd.to_datetime(val, errors='coerce', dayfirst=True)
                return p.strftime('%d/%m/%Y') if pd.notna(p) else str(val).split(' ')[0]
            except: return str(val)
        if not isinstance(val, str) and str(val).endswith('.0'): return str(val)[:-2]
        return str(val).strip()

    chu_tau = _v('CHU_TAU'); cccd = _v('CCCD', True); sdt = _v('SDT', True)
    dc_cu = _v('DIA_CHI')
    dc_moi = get_new_address(dc_cu)
    dc_hien_thi = dc_moi if dc_moi else dc_cu
    
    lmax = _v('LMAX'); cs = _v('CONG_SUAT'); nghe = _v('NGHE')
    hdk = _v('HAN_DK'); hgp = _v('HAN_GP')
    
    hdk_css = "m-alert-red" if check_expired(hdk) else "m-alert-green"
    hdk_txt = "ĐÃ HẾT HẠN" if check_expired(hdk) else "ĐANG CÒN HẠN"
    
    hgp_css = "m-alert-red" if check_expired(hgp) else "m-alert-green"
    hgp_txt = "ĐÃ HẾT HẠN" if check_expired(hgp) else "ĐANG CÒN HẠN"

    html_mobile = f"""<div class="mobile-container">
<div class="m-header"><h4>TRUY XUẤT HỒ SƠ TÀU CÁ</h4><h1>{vessel_id}</h1><div class="m-badge">📍 {dc_hien_thi}</div></div>
<div class="m-body">
<div class="m-section"><div class="m-title">🛡️ TÌNH TRẠNG PHÁP LÝ</div>
<div class="m-grid"><div class="m-alert-box {hdk_css}"><div class="m-alert-title">Đăng kiểm</div><div class="m-alert-val">{hdk}</div><div style="font-size:10px; margin-top:2px;">{hdk_txt}</div></div>
<div class="m-alert-box {hgp_css}"><div class="m-alert-title">Giấy phép</div><div class="m-alert-val">{hgp}</div><div style="font-size:10px; margin-top:2px;">{hgp_txt}</div></div></div></div>
<div class="m-section"><div class="m-title">👤 THÔNG TIN CHỦ TÀU</div>
<div class="m-row"><span class="m-label">Họ và tên</span><span class="m-val" style="color:#0d6efd; font-size:18px;">{chu_tau}</span></div>
<div class="m-grid"><div class="m-row"><span class="m-label">Số CCCD/CMND</span><span class="m-val">{cccd}</span></div><div class="m-row"><span class="m-label">Số điện thoại</span><span class="m-val">{sdt}</span></div></div>
<div class="m-row"><span class="m-label">Địa chỉ gốc</span><span class="m-val" style="font-size: 14px; font-weight: normal;">{dc_cu}</span></div></div>
<div class="m-section"><div class="m-title">⚙️ THÔNG SỐ KỸ THUẬT</div>
<div class="m-row"><span class="m-label">Nghề khai thác</span><span class="m-val">{nghe}</span></div>
<div class="m-grid"><div class="m-row"><span class="m-label">Chiều dài Lmax</span><span class="m-val">{lmax} m</span></div><div class="m-row"><span class="m-label">Công suất máy</span><span class="m-val">{cs} KW</span></div></div></div>
</div></div>
<div style="text-align:center; padding: 20px; color: #adb5bd; font-size: 12px; font-family:sans-serif;">Ứng dụng nội bộ Chi cục Thủy sản và Biển đảo tỉnh Khánh Hoà</div>"""
    st.markdown(html_mobile, unsafe_allow_html=True)
    st.stop()


# =========================================================
# GIAO DIỆN QUẢN TRỊ TRÊN MÁY TÍNH (ADMIN DASHBOARD)
# =========================================================
with st.sidebar:
    try: st.image("logo_kiem_ngu.png", width=180)
    except: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Vietnam_Fisheries_Surveillance_Logo.svg/1200px-Vietnam_Fisheries_Surveillance_Logo.svg.png", width=180)
    st.markdown("### QUẢN LÝ TÀU CÁ")
    
    app_domain = st.text_input("🌐 Tên miền Web (Dùng tạo mã QR):", value="https://quanlytaucanhvn-29032026.streamlit.app")
    
    st.markdown("---")
    menu = st.radio("MENU CHÍNH", ["🔍 Tra cứu thông tin", "⚙️ Quản lý Hệ thống & QR", "🔄 Đối chiếu dữ liệu", "📊 Lọc & Xuất báo cáo"])
    st.markdown("---")
    st.caption("© 2026 - Chi cục Thủy sản và Biển đảo tỉnh Khánh Hoà")

df_db, mmap = load_master_db()

# ---------------------------------------------------------
# TAB 1: TÌM KIẾM VÀ XEM HỒ SƠ TÀU
# ---------------------------------------------------------
if menu == "🔍 Tra cứu thông tin":
    st.header("🔍 TRA CỨU THÔNG TIN TÀU CÁ")
    
    if df_db is None:
        st.warning("⚠️ Cơ sở dữ liệu đang trống. Vui lòng sang tab **⚙️ Quản lý Hệ thống & QR** để nạp dữ liệu trước khi tra cứu.")
    else:
        col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
        with col_s1: keyword = st.text_input("Nhập từ khóa:", placeholder="Số đăng ký hoặc tên chủ tàu...")
        with col_s2: search_type = st.selectbox("Tìm theo", ["Tất cả", "Số đăng ký", "Tên chủ tàu"])
        with col_s3: 
            st.write("##"); btn_search = st.button("🔍 TÌM KIẾM")

        if btn_search or keyword:
            col_dk = mmap.get('SO_DANG_KY')
            col_ten = mmap.get('CHU_TAU')
            
            if search_type == "Số đăng ký" and col_dk: res = df_db[df_db[col_dk].astype(str).str.lower().str.contains(keyword.lower(), na=False)]
            elif search_type == "Tên chủ tàu" and col_ten: res = df_db[df_db[col_ten].astype(str).str.lower().str.contains(keyword.lower(), na=False)]
            else:
                mask = df_db.apply(lambda row: row.astype(str).str.lower().str.contains(keyword.lower(), na=False).any(), axis=1)
                res = df_db[mask]

            if res.empty: 
                st.info(f"Không tìm thấy kết quả cho: '{keyword}'")
            else:
                left_col, right_col = st.columns([1.2, 1])
                
                with left_col:
                    st.markdown("**DANH SÁCH KẾT QUẢ**")
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
                                    val = parsed.strftime('%d/%m/%Y') if pd.notna(parsed) else str(val).split(' ')[0].strip()
                                except: pass
                            item[title] = str(val) if pd.notna(val) else "-"
                        dc_col = mmap.get('DIA_CHI')
                        item['Địa phương'] = get_new_address(row[dc_col]) if dc_col and dc_col in res.columns else "-"
                        disp_data.append(item)
                    
                    df_display = pd.DataFrame(disp_data)
                    selected_vessel = st.selectbox("Chọn tàu để xem chi tiết:", df_display['Số đăng ký'].tolist())
                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                with right_col:
                    st.markdown("**THẺ CHI TIẾT & MÃ QR**")
                    if selected_vessel:
                        s_item = df_display[df_display['Số đăng ký'] == selected_vessel].iloc[0]
                        loc_str = s_item['Địa phương'] if s_item['Địa phương'] != "-" else "CHƯA XÁC ĐỊNH"
                        
                        html_card = f"""<div class="vessel-card">
<div class="card-header"><h4>CHI TIẾT TÀU CÁ</h4><h2>{s_item['Số đăng ký']}</h2><span class="badge-loc">{loc_str}</span></div>
<div class="card-body">
<div class="info-row"><div><p class="info-label">👤 CHỦ PHƯƠNG TIỆN</p><p class="info-val">{s_item['Tên chủ tàu']}</p></div>
<div><p class="info-label">💳 SỐ CCCD</p><p class="info-val">{s_item['CCCD']}</p></div></div>
<div class="info-row"><div><p class="info-label">📞 SỐ ĐIỆN THOẠI</p><p class="info-val">{s_item['SĐT']}</p></div>
<div><p class="info-label">📏 LMAX</p><p class="info-val">{s_item['Lmax']} m</p></div></div>
<div class="info-row" style="border-bottom:none;"><div><p class="info-label">⚡ CÔNG SUẤT</p><p class="info-val">{s_item['Công suất']} KW</p></div>
<div><p class="info-label">📍 ĐỊA CHỈ</p><p class="info-val">{s_item['Địa chỉ']}</p></div></div>
<div style="margin-top:20px;">
<div class="date-box"><p class="date-label">🗓 HẠN GIẤY PHÉP KTTS</p><p class="date-val {'val-expired' if check_expired(s_item['Hạn GPKTTS']) else 'val-valid'}">{s_item['Hạn GPKTTS']}</p></div>
<div class="date-box"><p class="date-label">🗓 HẠN ĐĂNG KIỂM</p><p class="date-val {'val-expired' if check_expired(s_item['Hạn Đăng kiểm']) else 'val-valid'}">{s_item['Hạn Đăng kiểm']}</p></div>
</div></div></div>"""
                        st.markdown(html_card, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        app_domain_clean = app_domain.strip().rstrip("/")
                        qr_bytes = generate_qr_code(s_item['Số đăng ký'], app_domain_clean)
                        
                        col_qr1, col_qr2 = st.columns([1, 2])
                        with col_qr1: st.image(qr_bytes, use_container_width=True)
                        with col_qr2:
                            st.info(f"Mã QR cấp riêng cho tàu **{s_item['Số đăng ký']}**.")
                            st.download_button("🖨️ TẢI ẢNH MÃ QR ĐỂ IN", data=qr_bytes, file_name=f"QR_CODE_{s_item['Số đăng ký']}.png", mime="image/png")

# ---------------------------------------------------------
# TAB 2: QUẢN LÝ DỮ LIỆU & TẠO MÃ QR HÀNG LOẠT
# ---------------------------------------------------------
elif menu == "⚙️ Quản lý Hệ thống & QR":
    st.header("⚙️ QUẢN LÝ CƠ SỞ DỮ LIỆU & XUẤT QR HÀNG LOẠT")
    
    with st.expander("📁 1. NẠP & CẬP NHẬT CƠ SỞ DỮ LIỆU GỐC", expanded=(df_db is None)):
        st.markdown("Tải lên file Excel danh sách tàu cá mới nhất. Hệ thống sẽ tự động lưu lại để cán bộ quét mã QR có thể truy xuất.")
        uploaded_db = st.file_uploader("Chọn file Excel CSDL", type=["xlsx", "xls"])
        if uploaded_db:
            with open(DB_FILE, "wb") as f: f.write(uploaded_db.getbuffer())
            st.success("✅ Đã cập nhật CSDL lên máy chủ thành công!")
            st.rerun()

    if df_db is not None:
        mtime = os.path.getmtime(DB_FILE)
        st.info(f"📊 **Trạng thái CSDL:** Đang lưu trữ **{len(df_db)}** tàu. *(Cập nhật lần cuối: {datetime.fromtimestamp(mtime).strftime('%H:%M %d/%m/%Y')})*")
        
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.markdown("### 🖨️ 2. HỆ THỐNG XUẤT MÃ QR THÔNG MINH")
        st.markdown("Hệ thống AI tự động so sánh CSDL hiện tại với Lịch sử xuất QR trước đó để **chỉ tạo mã cho những tàu mới**.")
        
        generated_vessels = set()
        if os.path.exists(QR_LOG_FILE):
            with open(QR_LOG_FILE, "r") as f:
                generated_vessels = set(line.strip().upper() for line in f if line.strip())

        col_dk = mmap.get('SO_DANG_KY')
        if not col_dk:
            st.error("Không tìm thấy cột Số đăng ký trong CSDL!")
        else:
            all_vessels_in_db = set(df_db[col_dk].astype(str).str.strip().str.upper().dropna())
            all_vessels_in_db.discard('NAN')
            all_vessels_in_db.discard('NONE')
            
            new_vessels = all_vessels_in_db - generated_vessels
            
            c1, c2 = st.columns(2)
            c1.success(f"🗂️ Đã cấp phát: **{len(generated_vessels)}** mã QR.")
            
            if len(new_vessels) == 0:
                c2.success("✅ Toàn bộ tàu trong CSDL hiện tại đều đã được tạo mã QR!")
                st.button("Không có tàu mới cần tạo QR", disabled=True, use_container_width=True)
            else:
                c2.warning(f"⚠️ Phát hiện **{len(new_vessels)}** tàu MỚI chưa có mã QR!")
                
                if st.button(f"🚀 TẠO MÃ QR CHO {len(new_vessels)} TÀU MỚI", type="primary"):
                    my_bar = st.progress(0, text="Đang tạo mã QR cho tàu mới... Vui lòng chờ.")
                    zip_buffer = io.BytesIO()
                    app_domain_clean = app_domain.strip().rstrip("/")
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        new_vessels_list = list(new_vessels)
                        total_new = len(new_vessels_list)
                        
                        for i, vessel_id in enumerate(new_vessels_list):
                            qr_bytes = generate_qr_code(vessel_id, app_domain_clean)
                            zip_file.writestr(f"QR_CODE_{vessel_id}.png", qr_bytes)
                            
                            if i % 10 == 0 or i == total_new - 1:
                                percent_complete = int((i + 1) / total_new * 100)
                                my_bar.progress(percent_complete, text=f"Đã tạo {i+1}/{total_new} mã mới ({percent_complete}%)")
                    
                    with open(QR_LOG_FILE, "a") as f:
                        for vid in new_vessels_list:
                            f.write(f"{vid}\n")
                    
                    my_bar.empty()
                    st.success(f"✅ Đã tạo xong {len(new_vessels)} Mã QR mới!")
                    
                    st.download_button(
                        label="📥 TẢI FILE ZIP CHỨA MÃ QR MỚI",
                        data=zip_buffer.getvalue(),
                        file_name=f"Bo_Ma_QR_TauCa_Moi_{datetime.now().strftime('%d%m%Y')}.zip",
                        mime="application/zip"
                    )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.expander("⚙️ Tùy chọn Nâng cao (Xóa lịch sử in ấn)"):
            st.markdown("Nếu bạn bị mất file ZIP lưu trữ cũ và muốn hệ thống 'quên' lịch sử để **in lại toàn bộ các mã QR từ đầu**, hãy bấm nút bên dưới.")
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if st.button("🗑️ XÓA LỊCH SỬ & IN LẠI TOÀN BỘ"):
                if os.path.exists(QR_LOG_FILE):
                    os.remove(QR_LOG_FILE)
                    st.rerun()
                else:
                    st.info("Lịch sử đang trống.")
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 3: ĐỐI CHIẾU DỮ LIỆU
# ---------------------------------------------------------
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
        df_src = read_excel_auto_header(src_file)
        cols_src = list(df_src.columns)
        
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
            if not vals_to_get: st.warning("Vui lòng chọn ít nhất 1 cột cần lấy!")
            else:
                with st.spinner("Đang tiến hành đối chiếu thông minh..."):
                    df_src['_key_match'] = df_src[key_src].astype(str).str.strip().str.upper()
                    for t_file in tgt_files:
                        df_t = read_excel_auto_header(t_file)
                        local_key = map_columns(df_t.columns).get('SO_DANG_KY') if key_tgt == "<Tự động nhận diện bằng AI>" else (key_tgt if key_tgt in df_t.columns else None)
                        if not local_key: continue
                        
                        local_vals = [c for c in vals_to_get if c in df_t.columns]
                        if not local_vals: continue

                        df_t['_key_match'] = df_t[local_key].astype(str).str.strip().str.upper()
                        df_t_unique = df_t.drop_duplicates(subset=['_key_match'])
                        short_fname = t_file.name.split('.')[0][:15]
                        df_t_sub = df_t_unique[['_key_match'] + local_vals].rename(columns={c: f"{c} ({short_fname}...)" for c in local_vals})
                        df_src = pd.merge(df_src, df_t_sub, on='_key_match', how='left')

                    df_src.drop(columns=['_key_match'], inplace=True)
                    st.success("✅ Đã đối chiếu và đắp dữ liệu thành công!")
                    
                    output = io.BytesIO()
                    df_src.to_excel(output, index=False, engine='openpyxl')
                    st.download_button("📥 TẢI FILE KẾT QUẢ", data=output.getvalue(), file_name=f"Ket_qua_Doi_chieu_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 4: LỌC DỮ LIỆU & XUẤT BÁO CÁO (LẤY TỪ MASTER DB)
# ---------------------------------------------------------
elif menu == "📊 Lọc & Xuất báo cáo":
    st.header("📊 LỌC DỮ LIỆU & XUẤT BÁO CÁO")
    
    if df_db is None:
        st.warning("⚠️ Cơ sở dữ liệu đang trống. Vui lòng sang tab **⚙️ Quản lý Hệ thống & QR** để nạp dữ liệu trước khi lọc báo cáo.")
    else:
        df_raw = df_db.copy()
        all_cols = list(df_raw.columns)
        
        st.markdown("### 1. Thiết lập xuất báo cáo")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            selected_cols = st.multiselect("Cột sẽ xuất ra báo cáo:", all_cols, default=[c for c in all_cols if c in mmap.values()])
            selected_commune = st.selectbox("Lọc theo Địa phương:", ["Tất cả", "Xã Đại Lãnh", "Xã Tu Bông", "Xã Vạn Hưng", "Xã Vạn Ninh", "Xã Vạn Thắng", "Phường Đông Ninh Hoà", "Phường Hoà Thắng", "Xã Bắc Ninh Hoà", "Xã Nam Ninh Hoà", "Bắc Nha Trang"])
        with col_c2:
            idx = all_cols.index(mmap['HAN_DK']) if 'HAN_DK' in mmap else (all_cols.index(mmap['HAN_GP']) if 'HAN_GP' in mmap else 0)
            selected_date_col = st.selectbox("Cột Mốc Tính Hạn:", all_cols, index=idx)
            selected_date = st.text_input("Lọc đến ngày (Bỏ trống lấy tất cả):", placeholder="VD: 30/06/2026")
            split_expired = st.checkbox("Tách mỗi Xã/Phường thành 1 Sheet (Đối với Tàu Hết hạn)")
            
        st.markdown('<div class="btn-success">', unsafe_allow_html=True)
        if st.button("▶ XEM TRƯỚC DASHBOARD & XUẤT BÁO CÁO"):
            with st.spinner("Hệ thống AI đang xử lý dữ liệu..."):
                col_diachi_goc = mmap.get('DIA_CHI', '')
                if not col_diachi_goc: st.error("Không tìm thấy Cột Địa chỉ trong file!")
                else:
                    df_raw['Xã/Phường mới'] = df_raw[col_diachi_goc].apply(get_new_address)
                    df_filtered = df_raw[df_raw['Xã/Phường mới'].notna()].copy()
                    if selected_commune != "Tất cả": df_filtered = df_filtered[df_filtered['Xã/Phường mới'] == selected_commune]

                    col_cccd = mmap.get('CCCD', '')
                    if col_cccd and col_cccd in df_filtered.columns:
                        df_filtered[col_cccd] = df_filtered[col_cccd].apply(lambda x: str(x).strip().split('.')[0].zfill(12) if pd.notna(x) and str(x).strip().split('.')[0].isdigit() else x)

                    parsed_dates = pd.to_datetime(df_filtered[selected_date_col], dayfirst=True, errors='coerce')
                    mask_old = (parsed_dates.dt.year < 1950) & parsed_dates.notna()
                    if mask_old.any(): parsed_dates.loc[mask_old] = parsed_dates.loc[mask_old].apply(lambda x: x.replace(year=x.year + 100))
                    df_filtered['Ngày_dt_temp'] = parsed_dates
                    
                    if selected_date != "": df_filtered = df_filtered[df_filtered['Ngày_dt_temp'] <= pd.to_datetime(selected_date, dayfirst=True)]

                    if len(df_filtered) == 0: st.warning("Không có tàu nào thỏa mãn điều kiện lọc!")
                    else:
                        df_final = pd.DataFrame({col: df_filtered[col] for col in selected_cols if col in df_filtered.columns})
                        df_final.insert(0, 'TT', range(1, len(df_final) + 1))
                        df_filtered['_da_het_han'] = df_filtered['Ngày_dt_temp'] < pd.Timestamp.now().normalize()
                        df_filtered['Lmax_num'] = pd.to_numeric(df_filtered[mmap.get('LMAX', '')], errors='coerce') if 'LMAX' in mmap else None

                        def pl(lmax):
                            if pd.isna(lmax): return 'Không rõ'
                            if lmax < 6: return '<6'
                            if 6 <= lmax < 12: return '6 đến <12'
                            if 12 <= lmax < 15: return '12 đến <15'
                            if 15 <= lmax < 24: return '15 đến <24'
                            return '>=24'

                        df_filtered['Nhom_Lmax'] = df_filtered['Lmax_num'].apply(pl)
                        col_id = mmap.get('SO_DANG_KY', df_filtered.columns[0])
                        df_thong_ke_main = df_filtered.groupby('Xã/Phường mới').agg(Tong_tau=(col_id, 'count'), Tau_het_han=('_da_het_han', 'sum')).reset_index()
                        lmax_pivot = pd.crosstab(df_filtered['Xã/Phường mới'], df_filtered['Nhom_Lmax']).reset_index()
                        df_thong_ke = pd.merge(df_thong_ke_main, lmax_pivot, on='Xã/Phường mới', how='left')

                        for col in ['<6', '6 đến <12', '12 đến <15', '15 đến <24', '>=24', 'Không rõ']:
                            if col not in df_thong_ke.columns: df_thong_ke[col] = 0

                        df_thong_ke.rename(columns={'Tong_tau': 'Tổng số tàu', 'Tau_het_han': 'Tàu hết hạn'}, inplace=True)
                        final_cols_tk = ['Xã/Phường mới', 'Tổng số tàu', 'Tàu hết hạn'] + [c for c in ['<6', '6 đến <12', '12 đến <15', '15 đến <24', '>=24', 'Không rõ'] if df_thong_ke[c].sum() > 0]
                        df_thong_ke = df_thong_ke[final_cols_tk]

                        tong_cong_row = {'Xã/Phường mới': 'TỔNG CỘNG'}
                        for col in df_thong_ke.columns:
                            if col != 'Xã/Phường mới': tong_cong_row[col] = df_thong_ke[col].sum()
                        df_thong_ke = pd.concat([df_thong_ke, pd.DataFrame([tong_cong_row])], ignore_index=True)

                        df_hh_full = df_filtered[df_filtered['_da_het_han'] == True].copy()
                        cols_hh = [c for c in selected_cols if c in df_hh_full.columns]
                        if selected_date_col not in cols_hh and selected_date_col in df_hh_full.columns: cols_hh.append(selected_date_col)
                        df_hh_exp = df_hh_full[cols_hh].copy()
                        if not df_hh_exp.empty: df_hh_exp.insert(0, 'TT', range(1, len(df_hh_exp) + 1))

                        st.markdown("---")
                        st.markdown("### 📊 DASHBOARD TỔNG HỢP")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("TỔNG SỐ TÀU LỌC ĐƯỢC", tong_cong_row['Tổng số tàu'])
                        m2.metric("SỐ TÀU ĐÃ HẾT HẠN", tong_cong_row['Tàu hết hạn'])
                        m3.metric("TỶ LỆ HẾT HẠN", f"{round((tong_cong_row['Tàu hết hạn'] / tong_cong_row['Tổng số tàu'] * 100), 1) if tong_cong_row['Tổng số tàu'] > 0 else 0}%")
                        st.dataframe(df_thong_ke, use_container_width=True, hide_index=True)

                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_final.to_excel(writer, sheet_name='Danh sách chi tiết', index=False)
                            df_thong_ke.to_excel(writer, sheet_name='Bảng thống kê', index=False)
                            if not df_hh_exp.empty: 
                                df_hh_exp.to_excel(writer, sheet_name='Tàu Hết Hạn (Tổng)', index=False)
                                if split_expired:
                                    for loc in df_hh_full['Xã/Phường mới'].dropna().unique():
                                        dl = df_hh_full[df_hh_full['Xã/Phường mới'] == loc][cols_hh].copy()
                                        dl.insert(0, 'TT', range(1, len(dl) + 1))
                                        dl.to_excel(writer, sheet_name=f"HH_{str(loc).replace('/', '_').replace(chr(92), '_')}"[:31], index=False)
                        st.download_button("📥 XÁC NHẬN TẢI BÁO CÁO EXCEL", data=output.getvalue(), file_name=f"Bao_Cao_Loc_TauCa_{datetime.now().strftime('%d%m%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.markdown('</div>', unsafe_allow_html=True)
