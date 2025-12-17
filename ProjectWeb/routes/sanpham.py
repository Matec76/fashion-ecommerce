from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import db
from models import SanPham
from utils import clean_input_money

sanpham_bp = Blueprint('sanpham', __name__)

@sanpham_bp.route("/sanpham")
def index():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    products = SanPham.query.order_by(SanPham.id.desc()).all()
    return render_template("sanpham.html", active_page="sanpham", products=products)

@sanpham_bp.route("/sanpham/them", methods=["POST"])
def them():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    
    # Làm sạch giá tiền trước khi lưu (ví dụ: "150.000" -> 150000)
    gia_so = clean_input_money(request.form.get("gia"))
    
    moi_sp = SanPham(
        ten=request.form.get("ten"), 
        sku=request.form.get("sku"), 
        gia=gia_so, 
        ton_kho=int(request.form.get("ton_kho") or 0), 
        hinh_anh=request.form.get("hinh_anh")
    )
    db.session.add(moi_sp)
    db.session.commit()
    return redirect(url_for('sanpham.index'))

@sanpham_bp.route("/sanpham/sua", methods=["POST"])
def sua():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    
    sp = SanPham.query.get(request.form.get("id"))
    if sp:
        sp.ten = request.form.get("ten")
        sp.sku = request.form.get("sku")
        sp.gia = clean_input_money(request.form.get("gia"))
        sp.ton_kho = int(request.form.get("ton_kho") or 0)
        sp.hinh_anh = request.form.get("hinh_anh")
        db.session.commit()
    return redirect(url_for('sanpham.index'))

@sanpham_bp.route("/sanpham/xoa/<int:id_sp>")
def xoa(id_sp):
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    
    sp = SanPham.query.get(id_sp)
    if sp:
        db.session.delete(sp)
        db.session.commit()
    return redirect(url_for('sanpham.index'))