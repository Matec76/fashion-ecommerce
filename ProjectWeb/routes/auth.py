from flask import Blueprint, render_template, request, redirect, url_for, session
from models import DonHang, KhachHang
# Tạo Blueprint tên là 'auth'
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/")
def home(): return redirect(url_for('auth.tongquan')) if 'da_dang_nhap' in session else render_template("login.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Lưu ý: Nên đổi thành check Database sau này
        if request.form.get("email") == "admin@stylex.com" and request.form.get("password") == "123456":
            session['da_dang_nhap'] = True; return redirect(url_for('auth.tongquan'))
    return render_template("login.html")

@auth_bp.route("/logout")
def logout(): session.pop('da_dang_nhap', None); return redirect(url_for('auth.login'))

@auth_bp.route("/tongquan")
def tongquan():
    if 'da_dang_nhap' not in session: return redirect(url_for('auth.login'))
    sl_don = DonHang.query.count()
    sl_khach = KhachHang.query.count()
    ds_don = DonHang.query.filter_by(trang_thai='Đã giao').all()
    tong_tien = sum(don.tong_tien for don in ds_don)
    return render_template("tongquan.html", active_page="tongquan", total_revenue=tong_tien, new_orders=sl_don, new_customers=sl_khach)