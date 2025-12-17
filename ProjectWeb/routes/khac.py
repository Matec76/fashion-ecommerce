from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import db
from models import MaGiamGia, BaiViet, NhanVien, DonHang, KhachHang
from utils import clean_input_money

khac_bp = Blueprint('khac', __name__)

# ==========================================
# 1. BÁO CÁO (CHART.JS)
# ==========================================
@khac_bp.route("/baocao")
def baocao():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    
    don_hangs = DonHang.query.all()
    sl_moi = 0; sl_giao = 0; sl_huy = 0; tong_tien_thuc = 0
    
    for don in don_hangs:
        if don.trang_thai == 'Đang xử lý': sl_moi += 1
        elif don.trang_thai == 'Đã giao': 
            sl_giao += 1
            tong_tien_thuc += (don.tong_tien or 0)
        elif don.trang_thai == 'Đã hủy': sl_huy += 1
            
    tong_don = len(don_hangs)
    ti_le = round((sl_giao / tong_don) * 100, 1) if tong_don > 0 else 0
    
    top_khach = KhachHang.query.order_by(KhachHang.tong_chi_tieu.desc()).limit(5).all()
    label_kh = [k.ten for k in top_khach]
    data_kh = [k.tong_chi_tieu for k in top_khach]
    
    return render_template("baocao.html", 
                           active_page="baocao", 
                           tong_don=tong_don, 
                           doanh_thu=tong_tien_thuc, 
                           ti_le_thanh_cong=ti_le, 
                           data_trang_thai=[sl_moi, sl_giao, sl_huy], 
                           label_khach_hang=label_kh, 
                           data_khach_hang=data_kh)

# ==========================================
# 2. MARKETING
# ==========================================
@khac_bp.route("/marketing")
def marketing():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    return render_template("marketing.html", active_page="marketing", coupons=MaGiamGia.query.all())

@khac_bp.route("/marketing/them", methods=["POST"])
def them_coupon():
    gt = clean_input_money(request.form.get("gia_tri"))
    db.session.add(MaGiamGia(
        code=request.form.get("code").upper(), 
        loai=request.form.get("loai"), 
        gia_tri=gt, 
        sudung=f"0 / {request.form.get('so_luong')}", 
        ngay_bat_dau=request.form.get("ngay_bat_dau"), 
        ngay_ket_thuc=request.form.get("ngay_ket_thuc")
    ))
    db.session.commit()
    return redirect(url_for('khac.marketing'))

@khac_bp.route("/marketing/xoa/<int:id_cp>")
def xoa_coupon(id_cp):
    cp = MaGiamGia.query.get(id_cp)
    if cp:
        db.session.delete(cp)
        db.session.commit()
    return redirect(url_for('khac.marketing'))

# ==========================================
# 3. NỘI DUNG
# ==========================================
@khac_bp.route("/noidung")
def noidung():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    posts = BaiViet.query.order_by(BaiViet.id.desc()).all()
    return render_template("noidung.html", active_page="noidung", posts=posts)

@khac_bp.route("/noidung/them", methods=["POST"])
def them_baiviet():
    db.session.add(BaiViet(
        tieu_de=request.form.get("tieu_de"), 
        chuyen_muc=request.form.get("chuyen_muc"), 
        ngay_dang=request.form.get("ngay_dang"), 
        hinh_anh=request.form.get("hinh_anh"), 
        noi_dung=request.form.get("noi_dung")
    ))
    db.session.commit()
    return redirect(url_for('khac.noidung'))

@khac_bp.route("/noidung/xoa/<int:id_bv>")
def xoa_baiviet(id_bv):
    bv = BaiViet.query.get(id_bv)
    if bv:
        db.session.delete(bv)
        db.session.commit()
    return redirect(url_for('khac.noidung'))

# ==========================================
# 4. CẤU HÌNH HỆ THỐNG
# ==========================================
@khac_bp.route("/cauhinh")
def cauhinh():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    return render_template("cauhinh.html", active_page="cauhinh")

@khac_bp.route("/cauhinh/thongtin")
def thongtin(): # Tên hàm phải là 'thongtin' để khớp với url_for('khac.thongtin')
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    return render_template("cauhinh/thongtin.html", active_page="cauhinh")

@khac_bp.route("/cauhinh/thanhtoan")
def thanhtoan():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    return render_template("cauhinh/thanhtoan.html", active_page="cauhinh")

@khac_bp.route("/cauhinh/vanchuyen")
def vanchuyen():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    return render_template("cauhinh/vanchuyen.html", active_page="cauhinh")

# ==========================================
# 5. NHÂN VIÊN
# ==========================================
@khac_bp.route("/cauhinh/phanquyen")
def phanquyen():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    return render_template("cauhinh/phanquyen.html", active_page="cauhinh", users=NhanVien.query.all())

@khac_bp.route("/cauhinh/phanquyen/them", methods=["POST"])
def them_nhanvien():
    db.session.add(NhanVien(
        ten=request.form.get("ten"), 
        email=request.form.get("email"), 
        vai_tro=request.form.get("vai_tro"),
        trang_thai="Đang hoạt động"
    ))
    db.session.commit()
    return redirect(url_for('khac.phanquyen'))

@khac_bp.route("/cauhinh/phanquyen/sua", methods=["POST"])
def sua_nhanvien():
    nv = NhanVien.query.get(request.form.get("id"))
    if nv:
        nv.ten = request.form.get("ten")
        nv.email = request.form.get("email")
        nv.vai_tro = request.form.get("vai_tro")
        db.session.commit()
    return redirect(url_for('khac.phanquyen'))

@khac_bp.route("/cauhinh/phanquyen/xoa/<int:id_nv>")
def xoa_nhanvien(id_nv):
    nv = NhanVien.query.get(id_nv)
    if nv:
        db.session.delete(nv)
        db.session.commit()
    return redirect(url_for('khac.phanquyen'))