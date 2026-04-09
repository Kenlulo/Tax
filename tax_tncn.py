"""
Web Tính Thuế TNCN — Streamlit App
Phong cách: Giống dự án Chứng khoán (Light theme, teal sidebar)
Hỗ trợ đa ngôn ngữ VN/EN
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from io import BytesIO
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tax_engine import (
    calculate_employee_tax, calculate_pit,
    count_valid_dependents,
    load_employees_db, save_employees_db,
    load_tax_history, save_tax_history,
    process_payroll, save_results_to_history,
    PERSONAL_DEDUCTION, DEPENDENT_DEDUCTION,
)

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG & THEME (Giống dự án chứng khoán)
# ═══════════════════════════════════════════════════════════════
st.set_page_config(page_title="Tính Thuế TNCN — Tax Calculator", page_icon="🧾", layout="wide")

st.markdown("""
<style>
    /* ── Light Professional Theme (matching Stock Evaluator) ── */
    [data-testid="stAppViewContainer"] { background-color: #E9ECEF; color: #1E1E1E; }
    [data-testid="stSidebar"] { background-color: #0B5C57 !important; border-right: none; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
        color: #F8F9F9 !important;
    }
    [data-testid="stHeader"] { background-color: transparent; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 98% !important; }

    /* ── Title ── */
    .main-title {
        font-size: 32px; font-weight: 800; color: #1A5276;
        margin-bottom: 0px; text-transform: uppercase; letter-spacing: -0.5px;
    }
    .sub-title { font-size: 16px; color: #7FB3D5; margin-bottom: 20px; font-weight: 500; }

    /* ── Cards ── */
    .info-card {
        background: #FFFFFF; border: 1px solid #D5DBDB;
        border-radius: 10px; padding: 18px 22px; margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .info-card h4 {
        color: #0B5C57; font-size: 13px; text-transform: uppercase;
        letter-spacing: 1.2px; margin-bottom: 8px; font-weight: 700;
    }
    .info-card p { color: #566573; font-size: 14px; margin: 0; }

    /* ── Metric Override ── */
    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #D5DBDB;
        border-radius: 10px; padding: 14px 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    [data-testid="stMetric"] label { color: #566573 !important; font-size: 12px !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #1A5276 !important; font-size: 22px !important; }

    /* ── Tables ── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background: #F4F6F7; border-radius: 8px 8px 0 0;
        color: #566573; font-weight: 500; padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #0B5C57 !important; color: #FFFFFF !important; font-weight: 700;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #0B5C57, #148F77) !important;
        color: #FFFFFF !important; font-weight: 700 !important;
        border: none !important; border-radius: 8px !important;
        padding: 8px 24px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #148F77, #1ABC9C) !important;
        box-shadow: 0 4px 12px rgba(11,92,87,0.3);
    }

    /* ── Download Button ── */
    .stDownloadButton > button {
        background: #1A5276 !important; color: #FFFFFF !important;
        border: none !important; border-radius: 8px !important;
    }

    /* ── Input Fields ── */
    .stNumberInput input, .stTextInput input, .stDateInput input {
        background: #FFFFFF !important; color: #1E1E1E !important;
        border-color: #D5DBDB !important; border-radius: 8px !important;
    }

    /* ── Status badges ── */
    .badge-active {
        background: #D5F5E3; color: #1E8449;
        padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;
        display: inline-block;
    }
    .badge-expired {
        background: #FADBD8; color: #C0392B;
        padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;
        display: inline-block;
    }

    /* ── General text readability ── */
    h1, h2, h3 { color: #1A5276 !important; }
    p, li, span, div { color: #2C3E50; }
    .stMarkdown { color: #2C3E50; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# LANGUAGE SYSTEM (VN / EN)
# ═══════════════════════════════════════════════════════════════
_LANG = {
    # Header
    '🧾 Hệ Thống Tính Thuế TNCN': '🧾 Personal Income Tax System',
    'Tính thuế Thu Nhập Cá Nhân theo Biểu thuế Lũy tiến từng phần — Nghị quyết 954/2020/UBTVQH14':
        'Personal Income Tax calculated using Progressive Tax Brackets — Resolution 954/2020/UBTVQH14',
    '⚖️ DỰ ÁN CÁ NHÂN (PORTFOLIO PROJECT): Trang web này là một dự án cá nhân mang tính chất thực hành và ứng dụng (Software Engineering Portfolio). Tuyên bố miễn trừ trách nhiệm: Các công cụ tính toán và kết quả thuế trên hệ thống này chỉ mang tính chất tham khảo và ước tính. Đây không phải pháp nhân đại diện cho cơ quan thuế hay cung cấp lời khuyên luật định chính thức.':
        '⚖️ PERSONAL PROJECT (PORTFOLIO PROJECT): This website is a personal project for practical application purposes (Software Engineering Portfolio). Disclaimer: The calculation tools and tax results on this system are for reference and estimation purposes only. This is not an official representative of any tax authority nor does it provide official legal advice.',
    'Nếu bạn muốn xem thêm dự án khác hãy': 'If you want to view other projects, please',

    # Sidebar
    'Điều hướng': 'Navigation',
    '📥 Import Thu Nhập': '📥 Import Income',
    '👥 Quản Lý NPT': '👥 Manage Dependents',
    '📊 Lịch Sử Thuế': '📊 Tax History',
    '🧮 Tính Nhanh': '🧮 Quick Calculator',
    'Ngày hiện tại': 'Current date',

    # Module 1: Import
    '📥 Import Dữ Liệu Thu Nhập Tháng': '📥 Import Monthly Income Data',
    '📋 File Mẫu': '📋 Template',
    'Tải file Excel mẫu để điền dữ liệu thu nhập tháng.': 'Download the Excel template to fill in monthly income data.',
    '⬇️ Tải File Mẫu (.xlsx)': '⬇️ Download Template (.xlsx)',
    '📁 Upload Dữ Liệu': '📁 Upload Data',
    'Chọn file Excel chứa dữ liệu thu nhập nhân viên.': 'Select the Excel file containing employee income data.',
    'Tháng': 'Month',
    'Năm': 'Year',
    '⚡ Tính Thuế TNCN': '⚡ Calculate PIT',
    '👀 Xem trước dữ liệu': '👀 Data Preview',
    '📊 Kết Quả Tính Thuế': '📊 Tax Calculation Results',
    '👥 Số nhân viên': '👥 Employees',
    '💰 Tổng Thu Nhập': '💰 Total Income',
    '🏛️ Tổng Thuế TNCN': '🏛️ Total PIT',
    '💵 Tổng Thực Nhận': '💵 Total Net Pay',
    'Cơ Cấu Quỹ Lương Tháng': 'Monthly Payroll Structure',
    'Lương Thực Nhận': 'Net Pay',
    'Bảo Hiểm': 'Insurance',
    'Thuế TNCN': 'PIT',
    '💾 Lưu vào Lịch Sử': '💾 Save to History',
    '📥 Xuất Báo Cáo Excel': '📥 Export Excel Report',
    'Đã lưu kết quả tính thuế': 'Tax results saved',
    'vào lịch sử': 'to history',

    # Module 2: NPT
    '👥 Quản Lý Người Phụ Thuộc (NPT)': '👥 Manage Dependents',
    'Thêm, sửa, xóa người phụ thuộc cho từng nhân viên. NPT hết hạn sẽ không được tính giảm trừ.':
        'Add, edit, or remove dependents for each employee. Expired dependents will not be counted for deductions.',
    '➕ Thêm Nhân Viên Mới vào Hệ Thống': '➕ Add New Employee to System',
    'Mã Số Thuế': 'Tax ID',
    'Họ Tên': 'Full Name',
    'Mã NV (tùy chọn)': 'Employee ID (optional)',
    '✅ Thêm Nhân Viên': '✅ Add Employee',
    'đã tồn tại trong hệ thống': 'already exists in the system',
    'Đã thêm nhân viên': 'Employee added',
    'Vui lòng nhập Mã Số Thuế và Họ Tên': 'Please enter Tax ID and Full Name',
    'Chưa có nhân viên nào trong hệ thống.': 'No employees in the system yet.',
    'Hãy Import Thu Nhập hoặc Thêm Nhân Viên Mới ở trên.':
        'Please Import Income or Add New Employee above.',
    '🔍 Chọn Nhân Viên': '🔍 Select Employee',
    'Thông tin Nhân viên': 'Employee Information',
    'Họ tên': 'Full name',
    'Mã NV': 'Employee ID',
    '📋 Danh Sách Người Phụ Thuộc': '📋 Dependents List',
    'Nhân viên này chưa có người phụ thuộc nào.': 'This employee has no dependents.',
    '✅ Hiệu lực': '✅ Active',
    '❌ Hết hạn': '❌ Expired',
    'Không giới hạn': 'Unlimited',
    '➕ Thêm Người Phụ Thuộc Mới': '➕ Add New Dependent',
    'Tên Người Phụ Thuộc': 'Dependent Name',
    'Quan Hệ': 'Relationship',
    'Con': 'Child',
    'Vợ/Chồng': 'Spouse',
    'Cha/Mẹ': 'Parent',
    'Khác': 'Other',
    'Ngày Bắt Đầu Giảm Trừ': 'Deduction Start Date',
    'Ngày Kết Thúc Giảm Trừ': 'Deduction End Date',
    '✅ Thêm Người Phụ Thuộc': '✅ Add Dependent',
    'Đã thêm NPT': 'Dependent added',
    'Vui lòng nhập tên người phụ thuộc': 'Please enter dependent name',

    # Module 3: History
    '📊 Lịch Sử Đóng Thuế TNCN': '📊 PIT Payment History',
    'Chưa có dữ liệu lịch sử.': 'No history data available.',
    'Hãy Import Thu Nhập và bấm Lưu vào Lịch Sử trước.':
        'Please Import Income and click Save to History first.',
    '📅 Chọn Tháng': '📅 Select Month',
    '📋 Bảng Thuế': '📋 Tax Table',
    '📊 TB Thuế/Người': '📊 Avg Tax/Person',
    '🔍 Tìm kiếm (Tên, MST)': '🔍 Search (Name, Tax ID)',
    'Phân Bổ Thuế & Lương': 'Tax & Salary Distribution',
    '📈 Xu Hướng Thuế TNCN Qua Các Tháng': '📈 PIT Trends Over Months',
    '🗑️ Xóa lịch sử tháng này': '🗑️ Delete this month\'s history',
    'Đã xóa lịch sử': 'History deleted',

    # Module 4: Quick Calculator
    '🧮 Tính Nhanh Thuế TNCN (Cá Nhân)': '🧮 Quick PIT Calculator (Individual)',
    'Nhập thông tin thu nhập để tính thuế TNCN nhanh cho 1 cá nhân.':
        'Enter income information to quickly calculate PIT for an individual.',
    '📝 Thông Tin Thu Nhập': '📝 Income Information',
    '💰 Tổng Thu Nhập (VNĐ/tháng)': '💰 Total Income (VND/month)',
    '🔓 Thu Nhập Không Chịu Thuế': '🔓 Non-Taxable Income',
    '🏥 Bảo Hiểm (BHXH, BHYT, BHTN)': '🏥 Insurance (Social, Health, Unemployment)',
    '👶 Số Người Phụ Thuộc': '👶 Number of Dependents',
    '📊 Kết Quả': '📊 Results',
    'Thu Nhập Chịu Thuế': 'Taxable Income',
    'Giảm Trừ Bản Thân': 'Personal Deduction',
    'Giảm Trừ NPT': 'Dependent Deduction',
    'TN Tính Thuế': 'Assessable Income',
    '🏛️ Thuế TNCN': '🏛️ PIT Amount',
    '💵 Lương Thực Nhận': '💵 Net Pay',
    '📋 Chi Tiết Thuế Theo Từng Bậc': '📋 Tax Breakdown by Bracket',
    'Bậc': 'Bracket',
    'Từ': 'From',
    'Đến': 'To',
    'TN Trong Bậc': 'Income in Bracket',
    'Thuế Suất': 'Rate',
    'Thuế': 'Tax',
    '🍩 Cơ Cấu Thu Nhập': '🍩 Income Structure',
    'Thực nhận': 'Net pay',

    # Table headers
    'Tổng Thu Nhập': 'Total Income',
    'Không Chịu Thuế': 'Non-Taxable',
    'Giảm Trừ BT': 'Personal Ded.',
    'Số NPT': 'Dependents',
    'Thực Nhận': 'Net Pay',
    'MST': 'Tax ID',

    # Excel column headers (cho bảng preview)
    'MaNV': 'EmpID',
    'HoTen': 'Full Name',
    'MaSoThue': 'Tax ID',
    'TongThuNhap': 'Total Income',
    'KhongChiuThue': 'Non-Taxable',
    'BaoHiem': 'Insurance',
}

def t(text):
    """Translation function."""
    if st.session_state.get('lang', '🇻🇳 Tiếng Việt') == '🇬🇧 English':
        return _LANG.get(text, text)
    return text


# ═══════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════
def fmt(value):
    if value is None: return "0"
    return f"{int(value):,}".replace(",", ".")


def create_template_excel():
    df = pd.DataFrame({
        "MaNV": ["NV001", "NV002", ""],
        "HoTen": ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"],
        "MaSoThue": ["8601234567", "8607654321", "8609876543"],
        "TongThuNhap": [25000000, 40000000, 15000000],
        "KhongChiuThue": [0, 0, 0],
        "BaoHiem": [2625000, 4200000, 1575000],
    })
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name="ThuNhapThang")
    output.seek(0)
    return output


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    lang_choice = st.radio("🌍 Ngôn ngữ / Language:", ['🇻🇳 Tiếng Việt', '🇬🇧 English'], horizontal=True)
    st.session_state.lang = lang_choice

    st.markdown("### 🧾 Thuế TNCN")
    st.caption("Personal Income Tax Calculator")
    st.markdown("---")

    modules_vi = ["📥 Import Thu Nhập", "🧮 Tính Nhanh"]
    modules_en = ["📥 Import Income", "🧮 Quick Calculator"]
    modules = modules_en if lang_choice == '🇬🇧 English' else modules_vi
    selected_display = st.radio(t("Điều hướng"), modules, label_visibility="collapsed")

    # Map back to Vietnamese key for module logic
    module_map = dict(zip(modules_en, modules_vi))
    selected = module_map.get(selected_display, selected_display)

    st.markdown("---")
    st.caption(f"📅 {t('Ngày hiện tại')}: {date.today().strftime('%d/%m/%Y')}")
    st.caption("© 2026 Hồ Anh Khoa")



# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════
st.markdown(f'<div class="main-title">{t("🧾 Hệ Thống Tính Thuế TNCN")}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{t("Tính thuế Thu Nhập Cá Nhân theo Biểu thuế Lũy tiến từng phần — Nghị quyết 954/2020/UBTVQH14")}</div>', unsafe_allow_html=True)

st.warning(t('⚖️ DỰ ÁN CÁ NHÂN (PORTFOLIO PROJECT): Trang web này là một dự án cá nhân mang tính chất thực hành và ứng dụng (Software Engineering Portfolio). Tuyên bố miễn trừ trách nhiệm: Các công cụ tính toán và kết quả thuế trên hệ thống này chỉ mang tính chất tham khảo và ước tính. Đây không phải pháp nhân đại diện cho cơ quan thuế hay cung cấp lời khuyên luật định chính thức.'))
st.markdown(f"**👉 {t('Nếu bạn muốn xem thêm dự án khác hãy')} [nhấp vào đây](https://portfolio-gilt-sigma-43.vercel.app)**")



# ═══════════════════════════════════════════════════════════════
# MODULE 1: IMPORT THU NHẬP
# ═══════════════════════════════════════════════════════════════
if selected == "📥 Import Thu Nhập":
    st.markdown(f"### {t('📥 Import Dữ Liệu Thu Nhập Tháng')}")

    col_download, col_upload = st.columns([1, 2])
    with col_download:
        st.markdown(f'<div class="info-card"><h4>{t("📋 File Mẫu")}</h4><p>{t("Tải file Excel mẫu để điền dữ liệu thu nhập tháng.")}</p></div>', unsafe_allow_html=True)
        st.download_button(
            t("⬇️ Tải File Mẫu (.xlsx)"),
            data=create_template_excel(),
            file_name="template_thu_nhap.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col_upload:
        st.markdown(f'<div class="info-card"><h4>{t("📁 Upload Dữ Liệu")}</h4><p>{t("Chọn file Excel chứa dữ liệu thu nhập nhân viên.")}</p></div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload file Excel", type=["xlsx", "xls"], label_visibility="collapsed")

    st.markdown("---")

    col_month, col_year, _ = st.columns([1, 1, 3])
    with col_month:
        month = st.selectbox(t("Tháng"), list(range(1, 13)), index=datetime.now().month - 1)
    with col_year:
        year = st.selectbox(t("Năm"), list(range(2020, 2031)), index=6)
    period_key = f"{year}-{month:02d}"

    if uploaded:
        try:
            df = pd.read_excel(uploaded)
            required = ["HoTen", "MaSoThue", "TongThuNhap", "KhongChiuThue", "BaoHiem"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                st.error(f"❌ File thiếu cột / Missing columns: {', '.join(missing)}")
                st.stop()

            st.markdown(f"#### {t('👀 Xem trước dữ liệu')}")
            # Dịch tên cột Excel sang ngôn ngữ hiện tại
            col_rename = {c: t(c) for c in df.columns}
            st.dataframe(df.rename(columns=col_rename), use_container_width=True, height=200)

            if st.button(t("⚡ Tính Thuế TNCN"), use_container_width=True):
                ref_date = date(year, month, 1)
                results = process_payroll(df, period_key, ref_date)

                st.markdown(f"### {t('📊 Kết Quả Tính Thuế')} — {t('Tháng')} {month:02d}/{year}")

                total_tax = sum(r["thue_tncn"] for r in results)
                total_net = sum(r["luong_thuc_nhan"] for r in results)
                total_gross = sum(r["tong_thu_nhap"] for r in results)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric(t("👥 Số nhân viên"), len(results))
                m2.metric(t("💰 Tổng Thu Nhập"), f"{fmt(total_gross)} ₫")
                m3.metric(t("🏛️ Tổng Thuế TNCN"), f"{fmt(total_tax)} ₫")
                m4.metric(t("💵 Tổng Thực Nhận"), f"{fmt(total_net)} ₫")

                table_data = []
                for r in results:
                    table_data.append({
                        t("Mã NV"): r["ma_nv"], t("Họ Tên"): r["ho_ten"], t("MST"): r["mst"],
                        t("Tổng Thu Nhập"): r["tong_thu_nhap"], t("Không Chịu Thuế"): r["khong_chiu_thue"],
                        t("Bảo Hiểm"): r["bao_hiem"], t("Giảm Trừ BT"): r["giam_tru_ban_than"],
                        t("Số NPT"): r["so_npt"], t("Giảm Trừ NPT"): r["giam_tru_npt"],
                        t("TN Tính Thuế"): r["thu_nhap_tinh_thue"],
                        t("Thuế TNCN"): r["thue_tncn"], t("Thực Nhận"): r["luong_thuc_nhan"],
                    })
                result_df = pd.DataFrame(table_data)

                num_cols = [t("Tổng Thu Nhập"), t("Không Chịu Thuế"), t("Bảo Hiểm"), t("Giảm Trừ BT"),
                           t("Giảm Trừ NPT"), t("TN Tính Thuế"), t("Thuế TNCN"), t("Thực Nhận")]
                fmt_dict = {c: "{:,.0f}" for c in num_cols if c in result_df.columns}
                st.dataframe(result_df.style.format(fmt_dict), use_container_width=True, height=400)

                # Pie chart
                total_insurance = sum(r["bao_hiem"] for r in results)
                fig_pie = go.Figure(data=[go.Pie(
                    labels=[t("Lương Thực Nhận"), t("Bảo Hiểm"), t("Thuế TNCN")],
                    values=[total_net, total_insurance, total_tax],
                    hole=0.55,
                    marker=dict(colors=["#27AE60", "#2980B9", "#E74C3C"]),
                    textinfo="label+percent", textfont=dict(size=13),
                )])
                fig_pie.update_layout(
                    title=dict(text=t("Cơ Cấu Quỹ Lương Tháng"), font=dict(color="#1A5276", size=16)),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#2C3E50"), legend=dict(font=dict(color="#566573")), height=350,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

                col_save, col_export = st.columns(2)
                with col_save:
                    if st.button(f"{t('💾 Lưu vào Lịch Sử')} ({t('Tháng')} {month:02d}/{year})"):
                        save_results_to_history(results, period_key)
                        st.success(f"✅ {t('Đã lưu kết quả tính thuế')} {t('Tháng')} {month:02d}/{year} {t('vào lịch sử')}!")
                with col_export:
                    export_bytes = BytesIO()
                    result_df.to_excel(export_bytes, index=False, sheet_name=f"Thue_{period_key}")
                    export_bytes.seek(0)
                    st.download_button(t("📥 Xuất Báo Cáo Excel"), data=export_bytes,
                        file_name=f"bao_cao_thue_tncn_{period_key}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"❌ Lỗi / Error: {e}")


# ═══════════════════════════════════════════════════════════════
# MODULE 4: TÍNH NHANH CÁ NHÂN
# ═══════════════════════════════════════════════════════════════
elif selected == "🧮 Tính Nhanh":
    st.markdown(f"### {t('🧮 Tính Nhanh Thuế TNCN (Cá Nhân)')}")
    st.markdown(f'<p style="color:#566573;">{t("Nhập thông tin thu nhập để tính thuế TNCN nhanh cho 1 cá nhân.")}</p>', unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 1])

    with col_input:
        st.markdown(f'<div class="info-card"><h4>{t("📝 Thông Tin Thu Nhập")}</h4></div>', unsafe_allow_html=True)
        gross = st.number_input(t("💰 Tổng Thu Nhập (VNĐ/tháng)"), min_value=0, value=30_000_000, step=1_000_000, format="%d")
        non_tax = st.number_input(t("🔓 Thu Nhập Không Chịu Thuế"), min_value=0, value=0, step=500_000, format="%d")
        insurance = st.number_input(t("🏥 Bảo Hiểm (BHXH, BHYT, BHTN)"), min_value=0, value=3_150_000, step=100_000, format="%d")
        num_dep = st.number_input(t("👶 Số Người Phụ Thuộc"), min_value=0, max_value=20, value=0, step=1)

    result = calculate_employee_tax(gross, non_tax, insurance, num_dep)

    with col_result:
        st.markdown(f'<div class="info-card"><h4>{t("📊 Kết Quả")}</h4></div>', unsafe_allow_html=True)
        r1, r2 = st.columns(2)
        r1.metric(t("Thu Nhập Chịu Thuế"), f"{fmt(result['thu_nhap_chiu_thue'])} ₫")
        r2.metric(t("Giảm Trừ Bản Thân"), f"{fmt(result['giam_tru_ban_than'])} ₫")
        r3, r4 = st.columns(2)
        r3.metric(t("Giảm Trừ NPT"), f"{fmt(result['giam_tru_npt'])} ₫")
        r4.metric(t("TN Tính Thuế"), f"{fmt(result['thu_nhap_tinh_thue'])} ₫")
        st.markdown("---")
        r5, r6 = st.columns(2)
        r5.metric(t("🏛️ Thuế TNCN"), f"{fmt(result['thue_tncn'])} ₫")
        r6.metric(t("💵 Lương Thực Nhận"), f"{fmt(result['luong_thuc_nhan'])} ₫")

    # Breakdown
    if result["breakdown"]:
        st.markdown(f"#### {t('📋 Chi Tiết Thuế Theo Từng Bậc')}")
        bk_data = []
        for b in result["breakdown"]:
            bk_data.append({
                t("Bậc"): b["bac"], t("Từ"): fmt(b["tu"]), t("Đến"): fmt(b["den"]),
                t("TN Trong Bậc"): fmt(b["thu_nhap_trong_bac"]),
                t("Thuế Suất"): f"{int(b['thue_suat']*100)}%", t("Thuế"): fmt(b["thue"]),
            })
        st.dataframe(pd.DataFrame(bk_data), use_container_width=True, hide_index=True)

    # Pie chart
    st.markdown(f"#### {t('🍩 Cơ Cấu Thu Nhập')}")
    fig = go.Figure(data=[go.Pie(
        labels=[t("Lương Thực Nhận"), t("Bảo Hiểm"), t("Thuế TNCN")],
        values=[max(0, result["luong_thuc_nhan"]), result["bao_hiem"], result["thue_tncn"]],
        hole=0.55,
        marker=dict(colors=["#27AE60", "#2980B9", "#E74C3C"]),
        textinfo="label+percent", textfont=dict(size=13),
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2C3E50"), legend=dict(font=dict(color="#566573")), height=350,
        annotations=[dict(
            text=f"<b>{fmt(result['luong_thuc_nhan'])} ₫</b><br><span style='font-size:11px;color:#7F8C8D'>{t('Thực nhận')}</span>",
            x=0.5, y=0.5, font_size=16, font_color="#27AE60", showarrow=False,
        )]
    )
    st.plotly_chart(fig, use_container_width=True)
