import streamlit as st
import pandas as pd
from datetime import datetime
import io
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

# =========================================================
# CẤU HÌNH TRANG WEB
# =========================================================
st.set_page_config(page_title="Quản lý Tàu cá - Khánh Hòa", page_icon="🚢", layout="wide")

# Bộ từ điển và Luật lệ (Giữ nguyên lõi AI của bạn)
COLUMN_ALIASES = {
    'SO_DANG_KY': ['số đăng ký', 'biển số', 'số đk'],
    'CHU_TAU': ['chủ tàu', 'chủ phương tiện', 'họ tên chủ', 'tên chủ'],
    'DIA_CHI': ['địa chỉ', 'nơi thường trú', 'địa chỉ thường trú', 'chỗ ở', 'địa chỉ chủ'],
    'LMAX': ['chiều dài lmax', 'lmax', 'chiều dài lớn nhất', 'l max', 'chiều dài'],
    'NGAY_HET_HAN': ['ngày hết hạn', 'hạn đăng kiểm', 'hết hạn đk', 'ngày hết hạn đk']
}

GLOBAL_EXCLUDES = [
    "phú yên", "ninh thuận", "bình thuận", "đắk lắk", "lâm đồng", 
    "tp.hcm", "hồ chí minh", "hà nội", "đà nẵng", "quảng nam", "quảng ngãi", "bình định"
]

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

# =========================================================
# HÀM BỔ TRỢ CHUNG
# =========================================================
def find_true_header_and_cols(uploaded_file):
    try:
        df_temp = pd.read_excel(uploaded_file, header=None, nrows=50)
        best_idx = 0
        max_valid_cells = 0
        std_to_original = {}
        
        for i, row in df_temp.iterrows():
            valid_cells = sum(1 for x in row.values if pd.notna(x) and str(x).strip() != '')
            if valid_cells > max_valid_cells:
                max_valid_cells = valid_cells
                best_idx = i
                
                # Nhận diện cột nếu là Tab 1
                temp_map = {}
                for cell_val in row.values:
                    cell_str = str(cell_val).lower().strip()
                    orig_name = str(cell_val).strip()
                    if cell_str == 'nan' or not orig_name: continue
                    for std_name, alias_list in COLUMN_ALIASES.items():
                        if std_name not in temp_map:
                            if any(alias in cell_str for alias in alias_list):
                                temp_map[std_name] = orig_name; break
                std_to_original = temp_map

        # Đưa con trỏ file về đầu trước khi đọc lại
        uploaded_file.seek(0)
        df_real = pd.read_excel(uploaded_file, header=best_idx, nrows=5)
        cols = df_real.columns.astype(str).str.strip().tolist()
        cols = [c for c in cols if not c.lower().startswith('unnamed') and c.lower() != 'nan' and c != 'None' and c != '']
        
        uploaded_file.seek(0) # Reset lại con trỏ cho các lần đọc sau
        return cols, best_idx, std_to_original
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return [], 0, {}

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

def style_excel(writer, df_final, df_thong_ke):
    df_final.to_excel(writer, sheet_name='Danh sách chi tiết', index=False)
    df_thong_ke.to_excel(writer, sheet_name='Bảng thống kê', index=False)
    
    workbook = writer.book
    ws_thong_ke = writer.sheets['Bảng thống kê']
    ws_chi_tiet = writer.sheets['Danh sách chi tiết']

    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    total_fill = PatternFill(start_color="FDE9D9", end_color="FDE9D9", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    total_font = Font(bold=True, color="C0504D")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    for col_num, cell in enumerate(ws_thong_ke[1], 1):
        cell.fill = header_fill; cell.font = header_font; cell.alignment = center_align; cell.border = thin_border
        ws_thong_ke.column_dimensions[cell.column_letter].width = 30 if col_num == 1 else 15

    max_row = ws_thong_ke.max_row
    for row in range(2, max_row + 1):
        for col in range(1, ws_thong_ke.max_column + 1):
            cell = ws_thong_ke.cell(row=row, column=col)
            cell.border = thin_border
            cell.alignment = left_align if col == 1 else center_align
            if row == max_row: cell.fill = total_fill; cell.font = total_font
                
    for col_num, cell in enumerate(ws_chi_tiet[1], 1):
        cell.fill = header_fill; cell.font = header_font; cell.alignment = center_align; cell.border = thin_border
        ws_chi_tiet.column_dimensions[cell.column_letter].width = 20
    ws_chi_tiet.column_dimensions['A'].width = 8 

# =========================================================
# GIAO DIỆN WEB
# =========================================================
# --- CHÈN LOGO VÀ TIÊU ĐỀ ---
col_logo, col_title = st.columns([1, 11]) # Chia tỷ lệ màn hình để logo nằm bên trái, chữ bên phải
with col_logo:
    try:
        from PIL import Image
        logo = Image.open("logo_kiem_ngu.png")
        st.image(logo, width=160)
    except Exception:
        st.write("🚢") # Nếu mất file ảnh thì hiện tạm hình con tàu

with col_title:
    st.title("HỆ THỐNG PHÂN TÍCH DỮ LIỆU TÀU CÁ")

st.markdown("---") # Đường kẻ ngang

tab1, tab2 = st.tabs(["📊 LỌC & THỐNG KÊ DANH SÁCH", "🔄 ĐỐI CHIẾU DỮ LIỆU"])

# ---------------------------------------------------------
# TAB 1: LỌC & THỐNG KÊ
# ---------------------------------------------------------
with tab1:
    st.header("1. Dữ liệu đầu vào")
    uploaded_file_t1 = st.file_uploader("Tải lên File Excel gốc", type=['xlsx', 'xls'], key="file_t1")
    
    if uploaded_file_t1 is not None:
        cols_t1, hdr_idx_t1, std_to_original_t1 = find_true_header_and_cols(uploaded_file_t1)
        
        if cols_t1:
            st.success("✅ Đã nhận diện cấu trúc file thành công!")
            
            st.header("2. Điều kiện Lọc & Tùy chọn Cột")
            col1, col2 = st.columns(2)
            with col1:
                danh_sach_xa = ["Tất cả", "Xã Đại Lãnh", "Xã Tu Bông", "Xã Vạn Hưng", "Xã Vạn Ninh", "Xã Vạn Thắng", "Phường Đông Ninh Hoà", "Phường Hoà Thắng", "Xã Bắc Ninh Hoà", "Xã Nam Ninh Hoà", "Bắc Nha Trang"]
                selected_commune = st.selectbox("Chọn Địa phương:", danh_sach_xa)
            with col2:
                selected_date = st.text_input("Hạn GPKTTS/Đăng kiểm (Ví dụ: 30/06/2026. Để trống lấy tất cả):")
            
            default_cols = list(std_to_original_t1.values())
            all_cols_options = ["Địa chỉ mới (Tạo tự động)"] + cols_t1
            default_cols_options = ["Địa chỉ mới (Tạo tự động)"] + default_cols
            
            selected_cols = st.multiselect(
                "Chọn các Cột Báo cáo:",
                options=all_cols_options,
                default=default_cols_options
            )
            
            if st.button("🚀 BẮT ĐẦU XỬ LÝ & TẠO BÁO CÁO", use_container_width=True, type="primary"):
                with st.spinner('Đang xử lý dữ liệu bằng AI...'):
                    try:
                        df_raw = pd.read_excel(uploaded_file_t1, header=hdr_idx_t1)
                        df_raw.columns = df_raw.columns.astype(str).str.strip()
                        
                        col_diachi_goc = std_to_original_t1.get('DIA_CHI', '')
                        if col_diachi_goc:
                            df_raw['Địa chỉ mới (Tạo tự động)'] = df_raw[col_diachi_goc].apply(get_new_address)
                        else:
                            st.error("Không tìm thấy Cột Địa chỉ trong file gốc!")
                            st.stop()
                            
                        df_filtered = df_raw[df_raw['Địa chỉ mới (Tạo tự động)'].notna()].copy()

                        if selected_commune != "Tất cả":
                            df_filtered = df_filtered[df_filtered['Địa chỉ mới (Tạo tự động)'] == selected_commune]

                        if 'NGAY_HET_HAN' in std_to_original_t1:
                            col_ngay_het_han = std_to_original_t1['NGAY_HET_HAN']
                            df_filtered['Ngày_dt_temp'] = pd.to_datetime(df_filtered[col_ngay_het_han], dayfirst=True, format='mixed', errors='coerce')
                            if selected_date != "":
                                target_date = pd.to_datetime(selected_date, dayfirst=True)
                                df_filtered = df_filtered[df_filtered['Ngày_dt_temp'] <= target_date]

                        if len(df_filtered) == 0:
                            st.warning("⚠️ Không có tàu cá nào thỏa mãn các điều kiện lọc của bạn!")
                        else:
                            final_dict = {}
                            for col in selected_cols:
                                if col in df_filtered.columns: final_dict[col] = df_filtered[col]
                            df_final = pd.DataFrame(final_dict)
                            df_final.insert(0, 'TT', range(1, len(df_final) + 1))

                            # Tính toán thống kê
                            current_date = pd.Timestamp.now()
                            if 'NGAY_HET_HAN' in std_to_original_t1: df_filtered['_da_het_han'] = df_filtered['Ngày_dt_temp'] < current_date
                            else: df_filtered['_da_het_han'] = False

                            if 'LMAX' in std_to_original_t1: df_filtered['Lmax_num'] = pd.to_numeric(df_filtered[std_to_original_t1['LMAX']], errors='coerce')
                            else: df_filtered['Lmax_num'] = None

                            def phan_loai_lmax(lmax):
                                if pd.isna(lmax): return 'Không rõ'
                                if lmax < 6: return '<6'
                                elif 6 <= lmax < 12: return '6 đến <12'
                                elif 12 <= lmax < 15: return '12 đến <15'
                                elif 15 <= lmax < 24: return '15 đến <24'
                                else: return '>=24'

                            df_filtered['Nhom_Lmax'] = df_filtered['Lmax_num'].apply(phan_loai_lmax)

                            col_id = std_to_original_t1.get('SO_DANG_KY', df_filtered.columns[0])
                            df_thong_ke_main = df_filtered.groupby('Địa chỉ mới (Tạo tự động)').agg(Tong_tau=(col_id, 'count'), Tau_het_han=('_da_het_han', 'sum')).reset_index()
                            lmax_pivot = pd.crosstab(df_filtered['Địa chỉ mới (Tạo tự động)'], df_filtered['Nhom_Lmax']).reset_index()
                            df_thong_ke = pd.merge(df_thong_ke_main, lmax_pivot, on='Địa chỉ mới (Tạo tự động)', how='left')

                            for col in ['<6', '6 đến <12', '12 đến <15', '15 đến <24', '>=24', 'Không rõ']:
                                if col not in df_thong_ke.columns: df_thong_ke[col] = 0

                            df_thong_ke.rename(columns={'Địa chỉ mới (Tạo tự động)': 'Xã/Phường (Địa chỉ mới)', 'Tong_tau': 'Tổng số tàu', 'Tau_het_han': 'Tàu hết hạn'}, inplace=True)
                            final_cols_tk = ['Xã/Phường (Địa chỉ mới)', 'Tổng số tàu', 'Tàu hết hạn']
                            if df_thong_ke['<6'].sum() > 0: final_cols_tk.append('<6')
                            final_cols_tk.extend(['6 đến <12', '12 đến <15', '15 đến <24', '>=24'])
                            if df_thong_ke['Không rõ'].sum() > 0: final_cols_tk.append('Không rõ')
                            df_thong_ke = df_thong_ke[final_cols_tk]

                            tong_cong_row = {'Xã/Phường (Địa chỉ mới)': 'TỔNG CỘNG'}
                            for col in df_thong_ke.columns:
                                if col != 'Xã/Phường (Địa chỉ mới)': tong_cong_row[col] = df_thong_ke[col].sum()
                            df_thong_ke = pd.concat([df_thong_ke, pd.DataFrame([tong_cong_row])], ignore_index=True)

                            # --- TẠO FILE EXCEL ẢO ĐỂ TẢI XUỐNG (WEB-STYLE) ---
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                style_excel(writer, df_final, df_thong_ke)
                            
                            processed_data = output.getvalue()
                            
                            now_str = datetime.now().strftime("%d%m%Y_%Hh%Mm")
                            base_name = "DS_tau_ca" if selected_commune == "Tất cả" else f"DS_tau_ca_{selected_commune.replace(' ', '_')}"
                            if selected_date != "": base_name += f"_Han_{selected_date.replace('/', '')}"
                            final_file_name = f"{base_name}_NHVN_{now_str}.xlsx"

                            st.success(f"🎉 Hoàn thành! Xử lý thành công {tong_cong_row['Tổng số tàu']} tàu cá.")
                            
                            st.download_button(
                                label="📥 TẢI XUỐNG FILE BÁO CÁO EXCEL",
                                data=processed_data,
                                file_name=final_file_name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                    except Exception as e:
                        st.error(f"Lỗi hệ thống: {e}")

# ---------------------------------------------------------
# TAB 2: ĐỐI CHIẾU DỮ LIỆU
# ---------------------------------------------------------
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.header("1. File Gốc (Cần đắp thêm)")
        file_src = st.file_uploader("Tải lên File Gốc", type=['xlsx', 'xls'], key="src_t2")
    with col2:
        st.header("2. File Đích (Lấy dữ liệu từ đây)")
        file_tgt = st.file_uploader("Tải lên File Đích", type=['xlsx', 'xls'], key="tgt_t2")
        
    if file_src and file_tgt:
        cols_src, hdr_idx_src, _ = find_true_header_and_cols(file_src)
        cols_tgt, hdr_idx_tgt, _ = find_true_header_and_cols(file_tgt)
        
        st.header("3. Thiết lập Đối chiếu")
        
        def guess_key(columns):
            for i, c in enumerate(columns):
                if any(alias in str(c).lower().strip() for alias in COLUMN_ALIASES['SO_DANG_KY']):
                    return i
            return 0
            
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            key_src = st.selectbox("Cột Nối của File Gốc:", cols_src, index=guess_key(cols_src))
        with col_k2:
            key_tgt = st.selectbox("Cột Nối của File Đích:", cols_tgt, index=guess_key(cols_tgt))
            
        vals_to_get = st.multiselect("Chọn (các) Cột ở File Đích muốn lấy sang:", cols_tgt)
        
        if st.button("🚀 BẮT ĐẦU ĐỐI CHIẾU & LẤY DỮ LIỆU", use_container_width=True, type="primary"):
            if not vals_to_get:
                st.warning("Vui lòng chọn ít nhất 1 cột cần lấy dữ liệu!")
            else:
                with st.spinner('Đang quét và nối dữ liệu...'):
                    try:
                        df_src = pd.read_excel(file_src, header=hdr_idx_src)
                        df_tgt = pd.read_excel(file_tgt, header=hdr_idx_tgt)

                        df_src.columns = df_src.columns.astype(str).str.strip()
                        df_tgt.columns = df_tgt.columns.astype(str).str.strip()

                        df_src['_key_match'] = df_src[key_src].astype(str).str.strip().str.upper()
                        df_tgt['_key_match'] = df_tgt[key_tgt].astype(str).str.strip().str.upper()

                        df_tgt_unique = df_tgt.drop_duplicates(subset=['_key_match'])
                        df_tgt_sub = df_tgt_unique[['_key_match'] + vals_to_get]
                        rename_dict = {col: f"{col} (Đối chiếu)" for col in vals_to_get}
                        df_tgt_sub = df_tgt_sub.rename(columns=rename_dict)

                        df_merged = pd.merge(df_src, df_tgt_sub, on='_key_match', how='left')
                        df_merged.drop(columns=['_key_match'], inplace=True)
                        
                        output = io.BytesIO()
                        # Xuất thẳng ra Excel ảo, không cần format cầu kì
                        df_merged.to_excel(output, index=False)
                        processed_data = output.getvalue()
                        
                        now_str = datetime.now().strftime("%d%m%Y_%Hh%Mm")
                        out_name = f'Ket_qua_Doi_chieu_{now_str}.xlsx'
                        
                        st.success("🎉 Đã đối chiếu xong!")
                        st.download_button(
                            label="📥 TẢI XUỐNG FILE KẾT QUẢ",
                            data=processed_data,
                            file_name=out_name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"Lỗi hệ thống: {e}")
