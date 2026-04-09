"""
Tax Engine — Bộ máy tính Thuế TNCN Việt Nam (7 bậc lũy tiến từng phần)
"""
import json
import os
import pandas as pd
from datetime import datetime, date

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════
PERSONAL_DEDUCTION = 11_000_000      # Giảm trừ bản thân: 11 triệu/tháng
DEPENDENT_DEDUCTION = 4_400_000      # Giảm trừ NPT: 4.4 triệu/người/tháng

# Biểu thuế lũy tiến từng phần (7 bậc)
TAX_BRACKETS = [
    (5_000_000,    0.05),   # Bậc 1: Đến 5 triệu       → 5%
    (10_000_000,   0.10),   # Bậc 2: 5 – 10 triệu      → 10%
    (18_000_000,   0.15),   # Bậc 3: 10 – 18 triệu     → 15%
    (32_000_000,   0.20),   # Bậc 4: 18 – 32 triệu     → 20%
    (52_000_000,   0.25),   # Bậc 5: 32 – 52 triệu     → 25%
    (80_000_000,   0.30),   # Bậc 6: 52 – 80 triệu     → 30%
    (float('inf'), 0.35),   # Bậc 7: Trên 80 triệu     → 35%
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ═══════════════════════════════════════════════════════════════
# CORE: Tính thuế TNCN theo biểu lũy tiến
# ═══════════════════════════════════════════════════════════════
def calculate_pit(taxable_income):
    """
    Tính thuế TNCN từ Thu nhập tính thuế (đã trừ giảm trừ).
    Trả về (tổng thuế, chi tiết từng bậc).
    """
    if taxable_income <= 0:
        return 0, []

    tax = 0
    prev_limit = 0
    breakdown = []

    for limit, rate in TAX_BRACKETS:
        bracket_amount = min(taxable_income, limit) - prev_limit
        if bracket_amount <= 0:
            break
        bracket_tax = bracket_amount * rate
        tax += bracket_tax
        breakdown.append({
            "bac": len(breakdown) + 1,
            "tu": prev_limit,
            "den": min(taxable_income, limit),
            "thu_nhap_trong_bac": bracket_amount,
            "thue_suat": rate,
            "thue": bracket_tax,
        })
        prev_limit = limit

    return round(tax), breakdown


def count_valid_dependents(dependents, ref_date=None):
    """
    Đếm số người phụ thuộc còn hiệu lực tại thời điểm ref_date.
    NPT hết hạn (ngày kết thúc < ref_date) sẽ không được tính.
    """
    if not dependents:
        return 0
    if ref_date is None:
        ref_date = date.today()
    elif isinstance(ref_date, str):
        ref_date = datetime.strptime(ref_date, "%Y-%m-%d").date()

    count = 0
    for dep in dependents:
        end_str = dep.get("ket_thuc", "")
        if not end_str:
            count += 1  # Không có ngày kết thúc → còn hiệu lực vô thời hạn
            continue
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            if end_date >= ref_date:
                count += 1
        except ValueError:
            count += 1  # Nếu format lỗi, mặc định tính
    return count


def calculate_employee_tax(tong_thu_nhap, khong_chiu_thue, bao_hiem, num_dependents):
    """
    Tính đầy đủ thuế TNCN cho 1 nhân viên.
    Returns dict với tất cả thông số phân rã.
    """
    thu_nhap_chiu_thue = tong_thu_nhap - khong_chiu_thue - bao_hiem
    giam_tru_ban_than = PERSONAL_DEDUCTION
    giam_tru_npt = num_dependents * DEPENDENT_DEDUCTION
    tong_giam_tru = giam_tru_ban_than + giam_tru_npt

    thu_nhap_tinh_thue = max(0, thu_nhap_chiu_thue - tong_giam_tru)

    thue_tncn, breakdown = calculate_pit(thu_nhap_tinh_thue)
    luong_thuc_nhan = tong_thu_nhap - bao_hiem - thue_tncn

    return {
        "tong_thu_nhap": tong_thu_nhap,
        "khong_chiu_thue": khong_chiu_thue,
        "bao_hiem": bao_hiem,
        "thu_nhap_chiu_thue": thu_nhap_chiu_thue,
        "giam_tru_ban_than": giam_tru_ban_than,
        "so_npt": num_dependents,
        "giam_tru_npt": giam_tru_npt,
        "thu_nhap_tinh_thue": thu_nhap_tinh_thue,
        "thue_tncn": thue_tncn,
        "luong_thuc_nhan": luong_thuc_nhan,
        "breakdown": breakdown,
    }


# ═══════════════════════════════════════════════════════════════
# BATCH: Xử lý hàng loạt từ DataFrame
# ═══════════════════════════════════════════════════════════════
def load_employees_db():
    """Load cơ sở dữ liệu nhân viên & NPT từ JSON."""
    path = os.path.join(DATA_DIR, "employees.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_employees_db(db):
    """Lưu cơ sở dữ liệu nhân viên & NPT."""
    path = os.path.join(DATA_DIR, "employees.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def load_tax_history():
    """Load lịch sử thuế."""
    path = os.path.join(DATA_DIR, "tax_history.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_tax_history(history):
    """Lưu lịch sử thuế."""
    path = os.path.join(DATA_DIR, "tax_history.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def process_payroll(df, period_key, ref_date=None):
    """
    Xử lý bảng lương hàng loạt.
    df: DataFrame từ Excel (MaNV, HoTen, MaSoThue, TongThuNhap, KhongChiuThue, BaoHiem)
    period_key: Chuỗi "YYYY-MM" đại diện cho tháng tính thuế
    ref_date: Ngày tham chiếu kiểm tra NPT hết hạn
    Returns: list of result dicts
    """
    employees_db = load_employees_db()
    results = []

    for _, row in df.iterrows():
        mst = str(row.get("MaSoThue", "")).strip()
        ho_ten = str(row.get("HoTen", "")).strip()
        ma_nv = str(row.get("MaNV", "")).strip() if pd.notna(row.get("MaNV")) else ""
        tong_thu_nhap = float(row.get("TongThuNhap", 0) or 0)
        khong_chiu_thue = float(row.get("KhongChiuThue", 0) or 0)
        bao_hiem = float(row.get("BaoHiem", 0) or 0)

        # Tra cứu NPT từ database
        emp_data = employees_db.get(mst, {})
        dependents = emp_data.get("dependents", [])
        num_deps = count_valid_dependents(dependents, ref_date)

        # Tính thuế
        result = calculate_employee_tax(tong_thu_nhap, khong_chiu_thue, bao_hiem, num_deps)
        result["ma_nv"] = ma_nv
        result["ho_ten"] = ho_ten
        result["mst"] = mst

        # Cập nhật HoTen & MaNV vào database nhân viên (nếu chưa có)
        if mst and mst not in employees_db:
            employees_db[mst] = {"ho_ten": ho_ten, "ma_nv": ma_nv, "dependents": []}
        elif mst and mst in employees_db:
            employees_db[mst]["ho_ten"] = ho_ten
            if ma_nv:
                employees_db[mst]["ma_nv"] = ma_nv

        results.append(result)

    save_employees_db(employees_db)
    return results


def save_results_to_history(results, period_key):
    """Lưu kết quả tính thuế vào lịch sử theo tháng."""
    history = load_tax_history()
    # Lưu chỉ các field cần thiết (loại bỏ breakdown)
    records = []
    for r in results:
        records.append({
            "ma_nv": r["ma_nv"],
            "ho_ten": r["ho_ten"],
            "mst": r["mst"],
            "tong_thu_nhap": r["tong_thu_nhap"],
            "khong_chiu_thue": r["khong_chiu_thue"],
            "bao_hiem": r["bao_hiem"],
            "giam_tru_ban_than": r["giam_tru_ban_than"],
            "so_npt": r["so_npt"],
            "giam_tru_npt": r["giam_tru_npt"],
            "thu_nhap_tinh_thue": r["thu_nhap_tinh_thue"],
            "thue_tncn": r["thue_tncn"],
            "luong_thuc_nhan": r["luong_thuc_nhan"],
        })
    history[period_key] = records
    save_tax_history(history)
