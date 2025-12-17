from extensions import db

class SanPham(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50))
    gia = db.Column(db.BigInteger, default=0)
    ton_kho = db.Column(db.Integer, default=0)
    hinh_anh = db.Column(db.String(500))

class KhachHang(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    sdt = db.Column(db.String(20))
    ngay_dk = db.Column(db.String(20))
    tong_chi_tieu = db.Column(db.BigInteger, default=0)

class DonHang(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ma_don = db.Column(db.String(20), unique=True)
    ten_khach = db.Column(db.String(100))
    ngay_dat = db.Column(db.String(20))
    tong_tien = db.Column(db.BigInteger, default=0)
    trang_thai = db.Column(db.String(50))
    chi_tiet = db.Column(db.String(500))

class MaGiamGia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    loai = db.Column(db.String(50))
    gia_tri = db.Column(db.Integer, default=0)
    trang_thai = db.Column(db.String(20), default="Hoạt động")
    sudung = db.Column(db.String(20))
    ngay_bat_dau = db.Column(db.String(20))
    ngay_ket_thuc = db.Column(db.String(20))

class BaiViet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tieu_de = db.Column(db.String(200), nullable=False)
    chuyen_muc = db.Column(db.String(50))
    ngay_dang = db.Column(db.String(20))
    hinh_anh = db.Column(db.String(500))
    noi_dung = db.Column(db.String(1000))
    trang_thai = db.Column(db.String(20), default="Hiển thị")

class NhanVien(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    vai_tro = db.Column(db.String(50))
    trang_thai = db.Column(db.String(50), default="Đang hoạt động")