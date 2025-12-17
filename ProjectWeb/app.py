from flask import Flask
from extensions import db
from utils import format_money
import os

def create_app():
    app = Flask(__name__)
    
    # --- CẤU HÌNH HỆ THỐNG ---
    app.secret_key = 'mat_khau_bi_mat_cua_stylex'

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'stylex.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- 1. KẾT NỐI EXTENSIONS ---
    db.init_app(app)

    # --- 2. ĐĂNG KÝ JINJA FILTER ---
    app.jinja_env.filters['format_money'] = format_money

    # --- 3. ĐĂNG KÝ BLUEPRINTS (Kết nối các file trong folder routes) ---
    with app.app_context():
        from routes.auth import auth_bp
        from routes.donhang import donhang_bp
        from routes.khachhang import khachhang_bp  
        from routes.sanpham import sanpham_bp
        from routes.khac import khac_bp

        # Đăng ký với Flask
        app.register_blueprint(auth_bp)
        app.register_blueprint(donhang_bp)
        app.register_blueprint(khachhang_bp)
        app.register_blueprint(sanpham_bp)
        app.register_blueprint(khac_bp)

        # Tạo bảng dữ liệu nếu chưa có
        db.create_all()

    return app

# Chạy ứng dụng
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)