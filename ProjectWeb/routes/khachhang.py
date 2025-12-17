from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import db
from models import KhachHang

khachhang_bp = Blueprint('khachhang', __name__)

@khachhang_bp.route("/khachhang")
def index():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    # Lấy toàn bộ khách hàng, mới nhất hiện lên đầu
    customers = KhachHang.query.order_by(KhachHang.id.desc()).all()
    return render_template("khachhang.html", active_page="khachhang", customers=customers)

@khachhang_bp.route("/khachhang/them", methods=["POST"])
def them():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    
    moi = KhachHang(
        ten=request.form.get("ten"), 
        email=request.form.get("email"), 
        sdt=request.form.get("sdt"), 
        ngay_dk=request.form.get("ngay_dk"), 
        tong_chi_tieu=0 # Mặc định số nguyên là 0
    )
    db.session.add(moi)
    db.session.commit()
    return redirect(url_for('khachhang.index'))

@khachhang_bp.route("/khachhang/sua", methods=["POST"])
def sua():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    
    kh = KhachHang.query.get(request.form.get("id"))
    if kh: 
        kh.ten = request.form.get("ten")
        kh.email = request.form.get("email")
        kh.sdt = request.form.get("sdt")
        db.session.commit()
    return redirect(url_for('khachhang.index'))

@khachhang_bp.route("/khachhang/xoa/<int:id_kh>")
def xoa(id_kh):
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    
    kh = KhachHang.query.get(id_kh)
    if kh:
        db.session.delete(kh)
        db.session.commit()
    return redirect(url_for('khachhang.index'))