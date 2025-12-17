from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import db
from models import DonHang, KhachHang
from utils import clean_input_money
import time

donhang_bp = Blueprint('donhang', __name__)

@donhang_bp.route("/donhang")
def index(): 
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    return render_template("donhang.html", active_page="donhang", orders=DonHang.query.order_by(DonHang.id.desc()).all(), customers=KhachHang.query.all())

@donhang_bp.route("/donhang/them", methods=["POST"])
def them():
    tien = clean_input_money(request.form.get("tong_tien"))
    db.session.add(DonHang(
        ma_don=f"#DH{str(int(time.time()))[-6:]}", 
        ten_khach=request.form.get("ten_khach"), 
        ngay_dat=request.form.get("ngay_dat"), 
        tong_tien=tien,
        trang_thai="Đang xử lý", 
        chi_tiet=request.form.get("chi_tiet")
    ))
    db.session.commit()
    return redirect(url_for('donhang.index'))

@donhang_bp.route("/donhang/capnhat/<int:id_don>/<trang_thai_moi>")
def capnhat(id_don, trang_thai_moi):
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    don = DonHang.query.get(id_don)
    if don:
        if don.trang_thai != 'Đã giao' and trang_thai_moi == 'Đã giao':
            kh = KhachHang.query.filter_by(ten=don.ten_khach).first()
            if kh: kh.tong_chi_tieu += don.tong_tien 
        don.trang_thai = trang_thai_moi
        db.session.commit()
    return redirect(url_for('donhang.index'))

@donhang_bp.route("/donhang/xoa/<int:id_don>")
def xoa(id_don):
    d = DonHang.query.get(id_don); db.session.delete(d) if d else None; db.session.commit(); return redirect(url_for('donhang.index'))