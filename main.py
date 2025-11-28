import ctypes
import flet as ft
from ui.login_view import LoginView
from ui.dashboard_view import DashboardView

try:
    myappid = 'sentinels.residential.manager.v1' # ID tùy ý, miễn là duy nhất
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

def main(page: ft.Page):
    page.title = "Quản Lý Dân Cư"
    page.theme_mode = "light"
    
    # Kích thước cửa sổ
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 1000
    page.window.min_height = 700
    
    # --- CÀI ĐẶT ICON ỨNG DỤNG ---
    # Flet sẽ tự động tìm file này trong thư mục assets đã khai báo bên dưới
    page.window.icon = "icon.png" 
    
    # Căn giữa cửa sổ khi mở lên
    page.window.center()

    def go_dashboard():
        page.clean()
        DashboardView(page)
        page.update()

    # Khởi chạy màn hình đăng nhập đầu tiên
    LoginView(page, go_dashboard)

if __name__ == "__main__":
    # --- QUAN TRỌNG: Khai báo assets_dir="assets" ---
    ft.app(target=main, assets_dir="assets")