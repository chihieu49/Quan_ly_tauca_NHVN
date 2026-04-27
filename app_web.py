import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
import qrcode
import zipfile
import urllib.parse
from PIL import Image
import json
import re
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import time
import requests
import base64
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except ImportError:
    pyzbar_decode = None

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
    
    /* Auth Form CSS */
    .auth-container { background-color: #ffffff; border-radius: 12px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    .auth-title { text-align: center; color: #1e293b; font-size: 26px; font-weight: bold; margin-bottom: 5px; }
    .auth-subtitle { text-align: center; color: #64748b; font-size: 14px; margin-bottom: 25px; }
    .auth-form-container [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    .auth-form-container [data-baseweb="input"] { border-radius: 6px; }
    .auth-form-container [data-testid="stFormSubmitButton"] button { background-color: #1d4ed8; color: white; border-radius: 6px; font-weight: bold; padding: 12px; border: none; transition: 0.2s; }
    .auth-form-container [data-testid="stFormSubmitButton"] button:hover { background-color: #1e40af; }
    .fake-recaptcha { border: 1px solid #d1d5db; background-color: #f9fafb; border-radius: 4px; padding: 12px 15px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; margin-top: 10px;}
    .auth-link { text-align: center; margin-top: 15px; }
    .auth-link button { background: none; border: none; color: #2563eb; padding: 0; font-weight: normal; box-shadow: none; }
    .auth-link button:hover { text-decoration: underline; color: #1d4ed8; background: none; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LÕI DỮ LIỆU & AI
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "CSDL_TauCa_Master.xlsx")
QR_LOG_FILE = os.path.join(BASE_DIR, "Da_Tao_QR_Log.txt")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

def hash_password(password):
    salt = os.urandom(16).hex()
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(password, hashed):
    if "$" not in hashed:
        return password == hashed
    salt, hash_val = hashed.split("$")
    return hashlib.sha256((salt + password).encode()).hexdigest() == hash_val

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {"password": hash_password("admin"), "role": "admin", "name": "Quản trị viên", "email": "admin@nhvn.gov.vn", "phone": "admin"},
            "user": {"password": hash_password("user"), "role": "user", "name": "Người dùng", "email": "user@nhvn.gov.vn", "phone": "user"}
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4, ensure_ascii=False)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users_data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=4, ensure_ascii=False)
    sync_to_github(USERS_FILE)

def sync_to_github(file_path):
    try:
        if "github" not in st.secrets:
            st.warning("⚠️ Hệ thống chưa được cấu hình GitHub Secrets. Dữ liệu sẽ không được lưu vĩnh viễn!")
            return
        token = st.secrets["github"]["token"]
        repo = st.secrets["github"]["repo"]
        if token == "YOUR_GITHUB_TOKEN_HERE":
            st.error("⚠️ Bạn chưa điền GitHub Token thật vào Secrets. Hãy tạo Token và dán vào Streamlit Cloud Secrets!")
            return
        repo_prefix = st.secrets["github"].get("folder", "")
    except Exception as e:
        st.error(f"⚠️ Lỗi cấu hình GitHub Secrets: {e}")
        return

    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        encoded_content = base64.b64encode(content).decode("utf-8")
        
        # Vì file_path giờ là đường dẫn tuyệt đối, ta chỉ lấy tên file để ghép với repo_prefix
        file_name = os.path.basename(file_path)
        github_path = f"{repo_prefix}{file_name}" if repo_prefix else file_name
        
        url = f"https://api.github.com/repos/{repo}/contents/{github_path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.get(url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json().get("sha")

        data = {
            "message": f"Auto-sync {file_name} from Streamlit app",
            "content": encoded_content
        }
        if sha:
            data["sha"] = sha

        put_response = requests.put(url, headers=headers, json=data)
        if put_response.status_code in [200, 201]:
            st.toast(f"✅ Đã đồng bộ `{file_name}` lên kho lưu trữ đám mây an toàn!")
        else:
            error_msg = put_response.json().get('message', 'Không rõ lỗi')
            st.error(f"❌ Lỗi đồng bộ lên GitHub ({put_response.status_code}): {error_msg}")
    except Exception as e:
        st.error(f"❌ Lỗi đồng bộ file {file_path}: {e}")

def send_otp_email(to_email, otp_code):
    try:
        sender_email = st.secrets["email"]["user"]
        sender_pass = st.secrets["email"]["password"]
        
        msg = MIMEMultipart()
        msg['From'] = f"Hệ thống Quản lý Tàu cá <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "Mã xác thực Đặt lại mật khẩu (OTP)"
        
        body = f"""
        Xin chào,
        
        Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản trên Hệ thống Quản lý Tàu cá NHVN.
        Dưới đây là mã xác thực OTP của bạn:
        
        {otp_code}
        
        Mã này có hiệu lực trong vòng 5 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.
        Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.
        
        Trân trọng,
        Ban Quản trị Hệ thống
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_pass)
        server.send_message(msg)
        server.quit()
        return True, ""
    except Exception as e:
        return False, str(e)

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

@st.cache_data
def load_master_db():
    pkl_file = DB_FILE.replace(".xlsx", ".pkl")
    if os.path.exists(pkl_file):
        try:
            df = pd.read_pickle(pkl_file)
            return df, map_columns(df.columns)
        except Exception:
            pass

    if os.path.exists(DB_FILE):
        df = read_excel_auto_header(DB_FILE)
        try:
            df.to_pickle(pkl_file)
        except Exception:
            pass
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
<div style="text-align:center; padding: 20px; color: #adb5bd; font-size: 12px; font-family:sans-serif;">Cấp bởi Chi cục Thủy sản và Biển Đảo tỉnh Khánh hoà - trạm Kiểm ngư NHVN</div>"""
    st.markdown(html_mobile, unsafe_allow_html=True)
    if st.button("🔙 Quét mã khác / Quay lại Trang chủ", use_container_width=True):
        st.session_state["search_mode"] = "📷 Quét QR Tự động (Camera)"
        st.query_params.clear()
        st.rerun()
    st.stop()


# =========================================================
# GIAO DIỆN QUẢN TRỊ TRÊN MÁY TÍNH (ADMIN DASHBOARD)
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "fp_step" not in st.session_state:
    st.session_state.fp_step = 1

if "otp_data" not in st.session_state:
    st.session_state.otp_data = {"code": None, "time": 0, "phone": None, "attempts": 0}

if not st.session_state.logged_in:
    users_db = load_users()
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        if st.session_state.auth_mode == "login":
            st.markdown('<div class="auth-title">Đăng nhập</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-subtitle">Vui lòng nhập thông tin để tiếp tục</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Tên đăng nhập (Số điện thoại) *", placeholder="👤 Nhập số điện thoại")
                password = st.text_input("Mật khẩu *", type="password", placeholder="🔒 Nhập mật khẩu")
                submit = st.form_submit_button("Đăng nhập")
                
                if submit:
                    user_info = users_db.get(username)
                    if user_info and verify_password(password, user_info.get("password", "")):
                        st.session_state.logged_in = True
                        st.session_state.role = user_info.get("role", "user")
                        st.session_state.name = user_info.get("name", "USER")
                        st.rerun()
                    else:
                        st.error("Tên đăng nhập hoặc mật khẩu không đúng!")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-link">', unsafe_allow_html=True)
            if st.button("Trợ giúp: Quên mật khẩu?", use_container_width=True):
                st.session_state.auth_mode = "forgot_password"
                st.session_state.fp_step = 1
                st.rerun()
            if st.button("Chưa có tài khoản? Đăng ký ngay", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
                
        elif st.session_state.auth_mode == "forgot_password":
            st.markdown('<div class="auth-title">Quên Mật Khẩu</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-subtitle">Quy trình khôi phục mật khẩu 3 bước</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
            
            if st.session_state.fp_step == 1:
                with st.form("fp_step1"):
                    fp_phone = st.text_input("Nhập Số điện thoại đã đăng ký *", placeholder="📞 VD: 0912345678")
                    not_robot_fp = st.checkbox("Tôi không phải là người máy *")
                    submit_fp1 = st.form_submit_button("Tiếp tục (Gửi OTP)")
                    
                    if submit_fp1:
                        if not fp_phone:
                            st.error("⚠️ Vui lòng nhập số điện thoại!")
                        elif not not_robot_fp:
                            st.error("⚠️ Vui lòng xác nhận không phải là người máy!")
                        else:
                            user_info = users_db.get(fp_phone)
                            if user_info and user_info.get("email"):
                                otp_code = str(random.randint(100000, 999999))
                                st.session_state.otp_data = {"code": otp_code, "time": time.time(), "phone": fp_phone, "attempts": 0}
                                
                                success, err = send_otp_email(user_info["email"], otp_code)
                                if success:
                                    st.success(f"✅ Đã gửi mã OTP đến Email liên kết với SĐT này!")
                                    time.sleep(1.5)
                                    st.session_state.fp_step = 2
                                    st.rerun()
                                else:
                                    st.error(f"⚠️ Không thể gửi Email. Có lỗi xảy ra, có thể Mật khẩu Ứng dụng sai!")
                            else:
                                st.error("⚠️ Số điện thoại không tồn tại trong hệ thống!")
            
            elif st.session_state.fp_step == 2:
                with st.form("fp_step2"):
                    st.info(f"Mã OTP đã được gửi đến Email của tài khoản **{st.session_state.otp_data['phone']}**. Vui lòng kiểm tra hộp thư đến (hoặc thư rác).")
                    entered_otp = st.text_input("Nhập mã OTP (6 số) *")
                    submit_fp2 = st.form_submit_button("Xác thực OTP")
                    
                    if submit_fp2:
                        if time.time() - st.session_state.otp_data["time"] > 300:
                            st.error("⚠️ Mã OTP đã hết hạn (quá 5 phút). Vui lòng yêu cầu lại!")
                            st.session_state.fp_step = 1
                        elif st.session_state.otp_data["attempts"] >= 3:
                            st.error("⚠️ Bạn đã nhập sai OTP quá 3 lần. Vui lòng yêu cầu lại!")
                            st.session_state.fp_step = 1
                        elif entered_otp == st.session_state.otp_data["code"]:
                            st.success("✅ Xác thực thành công!")
                            time.sleep(1)
                            st.session_state.fp_step = 3
                            st.rerun()
                        else:
                            st.session_state.otp_data["attempts"] += 1
                            st.error(f"⚠️ Mã OTP không chính xác! (Còn {3 - st.session_state.otp_data['attempts']} lần thử)")
            
            elif st.session_state.fp_step == 3:
                with st.form("fp_step3"):
                    st.info("Nhập mật khẩu mới cho tài khoản của bạn.")
                    new_fp_pass = st.text_input("Mật khẩu mới *", type="password")
                    confirm_fp_pass = st.text_input("Xác nhận mật khẩu *", type="password")
                    submit_fp3 = st.form_submit_button("Cập nhật Mật khẩu")
                    
                    if submit_fp3:
                        if not new_fp_pass or not confirm_fp_pass:
                            st.error("⚠️ Vui lòng điền đủ thông tin!")
                        elif new_fp_pass != confirm_fp_pass:
                            st.error("⚠️ Mật khẩu xác nhận không khớp!")
                        elif len(new_fp_pass) < 8 or not re.search(r"[a-z]", new_fp_pass) or not re.search(r"[A-Z]", new_fp_pass) or not re.search(r"[0-9]", new_fp_pass) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_fp_pass):
                            st.error("⚠️ Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ hoa, thường, số và ký tự đặc biệt!")
                        else:
                            phone = st.session_state.otp_data["phone"]
                            old_hash = users_db[phone]["password"]
                            if verify_password(new_fp_pass, old_hash):
                                st.error("⚠️ Mật khẩu mới không được trùng với mật khẩu cũ!")
                            else:
                                users_db[phone]["password"] = hash_password(new_fp_pass)
                                save_users(users_db)
                                st.success("✅ Đặt lại mật khẩu thành công! Chuyển về trang đăng nhập...")
                                time.sleep(2)
                                st.session_state.auth_mode = "login"
                                st.session_state.fp_step = 1
                                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-link">', unsafe_allow_html=True)
            if st.button("🔙 Quay lại Đăng nhập", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.session_state.fp_step = 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        elif st.session_state.auth_mode == "register": # Chế độ Đăng ký
            st.markdown('<div class="auth-title">Tạo tài khoản</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-subtitle">Điền thông tin để tạo tài khoản mới</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
            with st.form("register_form"):
                full_name = st.text_input("Họ và tên *", placeholder="👤 Nhập họ và tên")
                email = st.text_input("Email *", placeholder="✉️ Nhập email của bạn")
                phone = st.text_input("Số điện thoại *", placeholder="📞 Nhập số điện thoại (Dùng làm Tên đăng nhập)")
                reg_password = st.text_input("Mật khẩu *", type="password", placeholder="🔒 Nhập mật khẩu")
                reg_confirm_password = st.text_input("Xác nhận mật khẩu *", type="password", placeholder="🔒 Nhập lại mật khẩu")
                
                with st.expander("📄 Đọc Điều khoản sử dụng & Chính sách bảo mật", expanded=False):
                    st.markdown("""
                    <div style='font-size: 13px; color: #4b5563;'>
                    <strong>ĐIỀU KHOẢN SỬ DỤNG</strong><br>
                    1. <strong>Chấp nhận điều khoản:</strong> Bằng việc tạo tài khoản, bạn đồng ý tuân thủ các Điều khoản sử dụng này.<br>
                    2. <strong>Tài khoản người dùng:</strong> Bạn phải cung cấp thông tin chính xác và chịu trách nhiệm bảo mật tài khoản.<br>
                    3. <strong>Sử dụng ứng dụng:</strong> Sử dụng ứng dụng đúng mục đích, tuân thủ pháp luật.<br><br>
                    
                    <strong>CHÍNH SÁCH BẢO MẬT</strong><br>
                    1. <strong>Thu thập thông tin:</strong> Chúng tôi thu thập thông tin bạn cung cấp (họ tên, email, sđt) để cải thiện dịch vụ.<br>
                    2. <strong>Bảo mật dữ liệu:</strong> Chúng tôi áp dụng các biện pháp kỹ thuật phù hợp để bảo vệ thông tin cá nhân của bạn.<br>
                    3. <strong>Chia sẻ thông tin:</strong> Chúng tôi không bán, cho thuê thông tin cá nhân của bạn cho bên thứ ba.<br>
                    4. <strong>Liên hệ:</strong> Nếu có câu hỏi hoặc yêu cầu liên quan đến bảo mật thông tin, vui lòng liên hệ:<br>
                       - 📧 Email: <strong>chihieu49@gmail.com</strong><br>
                       - 📞 Hotline: <strong>0916.804.167</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                agree_terms = st.checkbox("Tôi đồng ý với Điều khoản sử dụng và Chính sách bảo mật")
                
                st.markdown('''
                    <div class="fake-recaptcha">
                        <div style="font-size: 14px; color: #374151;">☑️ Vui lòng tick ô bên dưới để xác nhận</div>
                        <div style="display: flex; flex-direction: column; align-items: center;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/RecaptchaLogo.svg/120px-RecaptchaLogo.svg.png" width="30">
                            <span style="font-size: 8px; color: #9ca3af;">reCAPTCHA</span>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                not_robot = st.checkbox("Tôi không phải là người máy *")
                
                submit_reg = st.form_submit_button("Đăng ký")
                
                if submit_reg:
                    email_exists = any(u.get("email") == email for u in users_db.values())
                    phone_regex = r"^(0|\+84)[3|5|7|8|9][0-9]{8}$"
                    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                    
                    if not full_name or not email or not phone or not reg_password or not reg_confirm_password:
                        st.error("⚠️ Vui lòng điền đầy đủ các trường bắt buộc (*)")
                    elif not re.match(email_regex, email):
                        st.error("⚠️ Định dạng Email không hợp lệ!")
                    elif not re.match(phone_regex, phone):
                        st.error("⚠️ Định dạng Số điện thoại không hợp lệ (VD: 0912345678)!")
                    elif reg_password != reg_confirm_password:
                        st.error("⚠️ Mật khẩu xác nhận không khớp!")
                    elif len(reg_password) < 8 or not re.search(r"[a-z]", reg_password) or not re.search(r"[A-Z]", reg_password) or not re.search(r"[0-9]", reg_password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", reg_password):
                        st.error("⚠️ Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt!")
                    elif not agree_terms:
                        st.error("⚠️ Bạn cần đồng ý với Điều khoản sử dụng và Chính sách bảo mật!")
                    elif not not_robot:
                        st.error("⚠️ Vui lòng xác nhận bạn không phải là người máy!")
                    elif phone in users_db:
                        st.error("⚠️ Số điện thoại này đã được đăng ký. Vui lòng đăng nhập!")
                    elif email_exists:
                        st.error("⚠️ Email này đã được đăng ký bởi tài khoản khác!")
                    else:
                        users_db[phone] = {
                            "password": hash_password(reg_password),
                            "role": "user",
                            "name": full_name,
                            "email": email,
                            "phone": phone
                        }
                        save_users(users_db)
                        st.success("✅ Đăng ký thành công! Hệ thống sẽ tự động chuyển sang trang Đăng nhập...")
                        import time
                        time.sleep(1.5)
                        st.session_state.auth_mode = "login"
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-link">', unsafe_allow_html=True)
            if st.button("Đã có tài khoản? Đăng nhập", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

with st.sidebar:
    try: st.image("logo_kiem_ngu.png", width=180)
    except: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Vietnam_Fisheries_Surveillance_Logo.svg/1200px-Vietnam_Fisheries_Surveillance_Logo.svg.png", width=90)
    st.markdown("### QUẢN LÝ TÀU CÁ")
    
    app_domain = st.text_input("🌐 Tên miền Web (Dùng tạo mã QR):", value="https://quanlytaucanhvn-29032026.streamlit.app")
    
    st.markdown("---")
    
    if st.session_state.role == "admin":
        menu_options = ["🔍 Tra cứu thông tin", "⚙️ Quản lý Hệ thống & QR", "🔄 Đối chiếu dữ liệu", "📊 Lọc & Xuất báo cáo", "👥 Quản lý Người dùng"]
    else:
        menu_options = ["🔍 Tra cứu thông tin", "📊 Lọc & Xuất báo cáo"]
        
    menu = st.radio("MENU CHÍNH", menu_options)
    
    st.markdown("---")
    st.markdown(f"**Tài khoản:** `{st.session_state.get('name', 'USER').upper()}`")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.name = None
        st.rerun()
        
    st.markdown("---")
    st.caption("© 2026 - Chi cục Thủy sản và Biển Đảo tỉnh Khánh hoà - trạm Kiểm ngư NHVN")

df_db, mmap = load_master_db()

# ---------------------------------------------------------
# TAB 1: TÌM KIẾM VÀ XEM HỒ SƠ TÀU
# ---------------------------------------------------------
if menu == "🔍 Tra cứu thông tin":
    st.header("🔍 TRA CỨU & QUÉT MÃ QR")
    
    if df_db is None:
        st.warning("⚠️ Cơ sở dữ liệu đang trống. Vui lòng sang tab **⚙️ Quản lý Hệ thống & QR** để nạp dữ liệu trước khi tra cứu.")
    else:
        search_mode = st.radio("Chọn phương thức tra cứu:", ["⌨️ Nhập tay", "📷 Quét QR Tự động (Camera)"], 
                               horizontal=True, 
                               index=1 if st.session_state.get("search_mode") == "📷 Quét QR Tự động (Camera)" else 0)
        
        if search_mode == "⌨️ Nhập tay":
            st.session_state["search_mode"] = "⌨️ Nhập tay"
            col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
            with col_s1: keyword = st.text_input("Nhập từ khóa:", placeholder="Số đăng ký hoặc tên chủ tàu...")
            with col_s2: search_type = st.selectbox("Tìm theo", ["Tất cả", "Số đăng ký", "Tên chủ tàu"])
            with col_s3: 
                st.write("##"); btn_search = st.button("🔍 TÌM KIẾM")
                
        else:
            st.session_state["search_mode"] = "📷 Quét QR Tự động (Camera)"
            st.info("💡 **Hướng dẫn:** Cho phép trình duyệt truy cập Camera. Đưa mã QR vào khung hình, ứng dụng sẽ tự động quét và tải hồ sơ.")
            import streamlit.components.v1 as components
            import os
            import urllib.parse
            
            component_path = os.path.join(os.path.dirname(__file__), "qr_scanner_component")
            if not os.path.exists(component_path):
                os.makedirs(component_path)
            
            index_path = os.path.join(component_path, "index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <script>
      function sendMessageToStreamlitClient(type, data) {
        var outData = Object.assign({isStreamlitMessage: true, type: type}, data);
        window.parent.postMessage(outData, "*");
      }
      function init() { sendMessageToStreamlitClient("streamlit:componentReady", {apiVersion: 1}); }
      function setFrameHeight(height) { sendMessageToStreamlitClient("streamlit:setFrameHeight", {height: height}); }
      function sendDataToPython(value) { sendMessageToStreamlitClient("streamlit:setComponentValue", {value: value}); }
      window.addEventListener("message", function(event) {
        if (event.data.type === "streamlit:render") { setFrameHeight(550); }
      });
    </script>
  </head>
  <body onload="init()" style="margin:0; padding:0;">
    <div id="qr-reader" style="width:100%; max-width:500px; margin:auto;"></div>
    <script>
      let isScanned = false;
      function onScanSuccess(decodedText, decodedResult) {
        if (!isScanned) {
            isScanned = true;
            sendDataToPython(decodedText + "|||" + Date.now());
        }
      }
      var html5QrcodeScanner = new Html5QrcodeScanner("qr-reader", { fps: 10, qrbox: {width: 250, height: 250} }, false);
      html5QrcodeScanner.render(onScanSuccess);
    </script>
  </body>
</html>""")

            qr_scanner = components.declare_component("qr_scanner", path=component_path)
            scan_key = st.session_state.get("scan_key", 0)
            qr_data = qr_scanner(key=f"qr_scanner_{scan_key}")
            
            if qr_data:
                qr_text = qr_data.split("|||")[0] if "|||" in qr_data else qr_data
                vessel_id = None
                try:
                    parsed_url = urllib.parse.urlparse(qr_text)
                    params_url = urllib.parse.parse_qs(parsed_url.query)
                    if "tau" in params_url:
                        vessel_id = params_url["tau"][0].strip().upper()
                    elif "?tau=" in qr_text:
                        vessel_id = qr_text.split("?tau=")[-1].split("&")[0].strip().upper()
                    elif len(qr_text) <= 15 and " " not in qr_text:
                        vessel_id = qr_text.strip().upper()
                except Exception:
                    pass
                
                if vessel_id:
                    st.session_state["scan_key"] = scan_key + 1
                    st.query_params["tau"] = vessel_id
                    st.rerun()

        st.markdown("---")
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
            with st.spinner("⏳ Đang xử lý và Tối ưu hóa dữ liệu (chỉ mất vài giây cho lần đầu tiên)..."):
                with open(DB_FILE, "wb") as f: f.write(uploaded_db.getbuffer())
                
                # Tạo bản sao Pickle siêu tốc
                df = read_excel_auto_header(DB_FILE)
                pkl_file = DB_FILE.replace(".xlsx", ".pkl")
                df.to_pickle(pkl_file)
                
                load_master_db.clear()
                sync_to_github(DB_FILE)
            st.success("✅ Đã cập nhật và Tối ưu hóa CSDL lên máy chủ thành công!")
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
                            
                    sync_to_github(QR_LOG_FILE)
                    
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
                    with open(QR_LOG_FILE, "w") as f:
                        f.write("")
                    sync_to_github(QR_LOG_FILE)
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
        
        st.markdown("### 1. Thiết lập Lọc và Xuất báo cáo")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            selected_cols = st.multiselect("Chọn các cột sẽ hiển thị trong báo cáo:", all_cols, default=[c for c in all_cols if c in mmap.values()])
            selected_commune = st.selectbox("Lọc theo Địa phương:", ["Tất cả", "Xã Đại Lãnh", "Xã Tu Bông", "Xã Vạn Hưng", "Xã Vạn Ninh", "Xã Vạn Thắng", "Phường Đông Ninh Hoà", "Phường Hoà Thắng", "Xã Bắc Ninh Hoà", "Xã Nam Ninh Hoà", "Bắc Nha Trang"])
            
        with col_c2:
            st.info("💡 **Tùy chọn lọc hết hạn:** Bạn có thể tự chọn tiêu chí quét tàu hết hạn tùy theo nghiệp vụ kiểm tra.")
            
            # TÍNH NĂNG MỚI: CHỌN ĐIỀU KIỆN LỌC
            filter_mode = st.selectbox("🎯 Lọc tàu hết hạn dựa trên:", [
                "1. Kết hợp (Hết GPKTTS với mọi tàu + Hết Đăng kiểm với tàu ≥ 12m)",
                "2. Chỉ lọc tàu hết hạn Giấy phép KTTS",
                "3. Chỉ lọc tàu hết hạn Đăng kiểm"
            ])
            
            selected_date = st.text_input("Mốc thời gian quy chiếu (Bỏ trống = Tính đến hôm nay):", placeholder="VD: 30/06/2026")
            split_expired = st.checkbox("Tách mỗi Xã/Phường thành 1 Sheet riêng (Đối với Tàu Hết hạn)")
            
        st.markdown('<div class="btn-success">', unsafe_allow_html=True)
        if st.button("▶ PHÂN TÍCH & XUẤT BÁO CÁO TỔNG HỢP"):
            with st.spinner("Trí tuệ nhân tạo đang phân tích dữ liệu..."):
                col_diachi_goc = mmap.get('DIA_CHI', '')
                if not col_diachi_goc: 
                    st.error("Không tìm thấy Cột Địa chỉ trong file CSDL gốc!")
                else:
                    df_raw['Xã/Phường mới'] = df_raw[col_diachi_goc].apply(get_new_address)
                    df_filtered = df_raw[df_raw['Xã/Phường mới'].notna()].copy()
                    if selected_commune != "Tất cả": 
                        df_filtered = df_filtered[df_filtered['Xã/Phường mới'] == selected_commune]

                    col_cccd = mmap.get('CCCD', '')
                    if col_cccd and col_cccd in df_filtered.columns:
                        df_filtered[col_cccd] = df_filtered[col_cccd].apply(lambda x: str(x).strip().split('.')[0].zfill(12) if pd.notna(x) and str(x).strip().split('.')[0].isdigit() else x)

                    target_date = pd.to_datetime(selected_date, dayfirst=True) if selected_date else pd.Timestamp.now().normalize()
                    
                    df_filtered['Lmax_num'] = pd.to_numeric(df_filtered[mmap.get('LMAX', '')], errors='coerce') if 'LMAX' in mmap else 0
                    
                    col_gp = mmap.get('HAN_GP')
                    col_dk = mmap.get('HAN_DK')
                    
                    def parse_dates_safe(series):
                        d = pd.to_datetime(series, dayfirst=True, errors='coerce')
                        mask = (d.dt.year < 1950) & d.notna()
                        if mask.any(): d.loc[mask] = d.loc[mask].apply(lambda x: x.replace(year=x.year + 100))
                        return d
                        
                    dt_gp = parse_dates_safe(df_filtered[col_gp]) if col_gp in df_filtered.columns else pd.Series(pd.NaT, index=df_filtered.index)
                    dt_dk = parse_dates_safe(df_filtered[col_dk]) if col_dk in df_filtered.columns else pd.Series(pd.NaT, index=df_filtered.index)
                    
                    is_exp_gp = dt_gp < target_date
                    is_exp_dk = dt_dk < target_date
                    is_ge_12 = df_filtered['Lmax_num'] >= 12
                    
                    # LOGIC LỌC TÙY BIẾN
                    if filter_mode.startswith("1"):
                        df_filtered['_da_het_han'] = is_exp_gp | (is_ge_12 & is_exp_dk)
                    elif filter_mode.startswith("2"):
                        df_filtered['_da_het_han'] = is_exp_gp
                    elif filter_mode.startswith("3"):
                        df_filtered['_da_het_han'] = is_exp_dk

                    if len(df_filtered) == 0: 
                        st.warning("Không có tàu nào thỏa mãn điều kiện lọc!")
                    else:
                        df_final = pd.DataFrame({col: df_filtered[col] for col in selected_cols if col in df_filtered.columns})
                        df_final.insert(0, 'TT', range(1, len(df_final) + 1))

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

                        df_thong_ke.rename(columns={'Tong_tau': 'Tổng số tàu', 'Tau_het_han': 'Tàu Hết hạn'}, inplace=True)
                        final_cols_tk = ['Xã/Phường mới', 'Tổng số tàu', 'Tàu Hết hạn'] + [c for c in ['<6', '6 đến <12', '12 đến <15', '15 đến <24', '>=24', 'Không rõ'] if df_thong_ke[c].sum() > 0]
                        df_thong_ke = df_thong_ke[final_cols_tk]

                        tong_cong_row = {'Xã/Phường mới': 'TỔNG CỘNG'}
                        for col in df_thong_ke.columns:
                            if col != 'Xã/Phường mới': tong_cong_row[col] = df_thong_ke[col].sum()
                        df_thong_ke = pd.concat([df_thong_ke, pd.DataFrame([tong_cong_row])], ignore_index=True)

                        df_hh_full = df_filtered[df_filtered['_da_het_han'] == True].copy()
                        cols_hh = [c for c in selected_cols if c in df_hh_full.columns]
                        if col_gp and col_gp not in cols_hh and col_gp in df_hh_full.columns: cols_hh.append(col_gp)
                        if col_dk and col_dk not in cols_hh and col_dk in df_hh_full.columns: cols_hh.append(col_dk)
                        
                        df_hh_exp = df_hh_full[cols_hh].copy()
                        if not df_hh_exp.empty: df_hh_exp.insert(0, 'TT', range(1, len(df_hh_exp) + 1))

                        st.markdown("---")
                        st.markdown("### 📊 DASHBOARD TỔNG HỢP")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("TỔNG SỐ TÀU LỌC ĐƯỢC", tong_cong_row['Tổng số tàu'])
                        m2.metric("SỐ TÀU Hết hạn", tong_cong_row['Tàu Hết hạn'])
                        m3.metric("TỶ LỆ HẾT HẠN", f"{round((tong_cong_row['Tàu Hết hạn'] / tong_cong_row['Tổng số tàu'] * 100), 1) if tong_cong_row['Tổng số tàu'] > 0 else 0}%")
                        st.dataframe(df_thong_ke, use_container_width=True, hide_index=True)

                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_final.to_excel(writer, sheet_name='Danh sách chi tiết', index=False)
                            df_thong_ke.to_excel(writer, sheet_name='Bảng thống kê', index=False)
                            if not df_hh_exp.empty: 
                                df_hh_exp.to_excel(writer, sheet_name='Tàu hết hạn (Tổng)', index=False)
                                if split_expired:
                                    for loc in df_hh_full['Xã/Phường mới'].dropna().unique():
                                        dl = df_hh_full[df_hh_full['Xã/Phường mới'] == loc][cols_hh].copy()
                                        dl.insert(0, 'TT', range(1, len(dl) + 1))
                                        dl.to_excel(writer, sheet_name=f"VP_{str(loc).replace('/', '_').replace(chr(92), '_')}"[:31], index=False)
                        st.download_button("📥 XÁC NHẬN TẢI BÁO CÁO EXCEL", data=output.getvalue(), file_name=f"Bao_Cao_Vi_Pham_NHVN_{datetime.now().strftime('%d%m%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 5: QUẢN LÝ NGƯỜI DÙNG
# ---------------------------------------------------------
elif menu == "👥 Quản lý Người dùng":
    st.header("👥 QUẢN LÝ NGƯỜI DÙNG")
    
    users_db = load_users()
    
    st.subheader("📋 Danh sách Tài khoản")
    df_users = pd.DataFrame.from_dict(users_db, orient='index').reset_index()
    df_users.rename(columns={'index': 'Số điện thoại (ID)', 'name': 'Họ và tên', 'email': 'Email', 'role': 'Quyền'}, inplace=True)
    df_users = df_users[['Số điện thoại (ID)', 'Họ và tên', 'Email', 'Quyền']]
    st.dataframe(df_users, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("⚙️ Tùy chỉnh Tài khoản")
    
    user_list = [f"{v.get('name', '')} - {k}" for k, v in users_db.items()]
    selected_user_str = st.selectbox("Chọn người dùng để thao tác:", [""] + user_list)
    
    if selected_user_str:
        selected_phone = selected_user_str.split(" - ")[-1]
        user_info = users_db.get(selected_phone)
        
        if user_info:
            with st.form("edit_user_form"):
                st.info(f"Đang chỉnh sửa: **{selected_phone}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Họ và tên", value=user_info.get("name", ""))
                    new_email = st.text_input("Email", value=user_info.get("email", ""))
                with col2:
                    new_role = st.selectbox("Quyền", ["user", "admin"], index=0 if user_info.get("role") == "user" else 1)
                    new_password = st.text_input("Reset Mật khẩu (Bỏ trống nếu không đổi)", type="password", help="Nhập mật khẩu mới nếu muốn reset. (Chưa mã hóa, hệ thống sẽ tự băm)")
                
                delete_user = st.checkbox("⚠️ Xác nhận XÓA TÀI KHOẢN này vĩnh viễn")
                
                submit_edit = st.form_submit_button("Lưu thay đổi", type="primary")
                
                if submit_edit:
                    if delete_user:
                        if selected_phone == "admin" and len([u for u in users_db.values() if u.get("role") == "admin"]) <= 1:
                            st.error("⚠️ Không thể xóa Admin cuối cùng của hệ thống!")
                        else:
                            del users_db[selected_phone]
                            save_users(users_db)
                            st.success("✅ Đã xóa tài khoản thành công!")
                            import time
                            time.sleep(1.5)
                            st.rerun()
                    else:
                        users_db[selected_phone]["name"] = new_name
                        users_db[selected_phone]["email"] = new_email
                        users_db[selected_phone]["role"] = new_role
                        
                        if new_password.strip():
                            users_db[selected_phone]["password"] = hash_password(new_password)
                            st.warning("🔑 Đã đặt lại mật khẩu mới!")
                            
                        save_users(users_db)
                        st.success("✅ Cập nhật thông tin thành công!")
                        import time
                        time.sleep(1.5)
                        st.rerun()
