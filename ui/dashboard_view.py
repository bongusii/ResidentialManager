import flet as ft
import sys
import time
from ui.residents_view import ResidentsView
from ui.households_view import HouseholdsView
from ui.import_view import ImportView
from ui.export_view import ExportView
from ui.stats_view import StatsView
from ui.settings_view import SettingsView
from ui.login_view import LoginView

class DashboardView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.content_area = ft.Container(expand=True, padding=20)
        self.render()

    def show_loading(self, with_update=True):
        """
        Hiển thị màn hình chờ.
        - with_update=False: Dùng cho lần load đầu tiên (khi chưa add vào page).
        - with_update=True: Dùng khi chuyển tab.
        """
        self.content_area.content = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=60, height=60, stroke_width=5, color="blue"),
                ft.Text("Đang lấy dữ liệu từ kho lưu trữ...", size=16, color="blue500", italic=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        
        if with_update:
            self.content_area.update()
            # Delay nhẹ 50ms để UI kịp vẽ vòng xoay trước khi tải nặng
            time.sleep(0.05)

    def change_tab(self, e):
        idx = e.control.selected_index
        
        # Khi chuyển tab thì CẦN update ngay để hiện loading
        self.show_loading(with_update=True)

        # Logic tải view mới
        if idx == 0: # Tab Cá Nhân
            self.content_area.content = ResidentsView(self.page).get_content()
        elif idx == 1: # Tab Hộ Khẩu
            self.content_area.content = HouseholdsView(self.page).get_content()
        elif idx == 2: # Tab Nhập Liệu
            self.content_area.content = ImportView(self.page).get_content()
        elif idx == 3: # Tab Báo Cáo
            self.content_area.content = ExportView(self.page).get_content()
        elif idx == 4: # Tab Thống Kê
            self.content_area.content = StatsView(self.page).get_content()
        elif idx == 5: # Tab Hệ Thống
            self.content_area.content = SettingsView(self.page).get_content() 
        elif idx == 6: # Đăng Xuất
            self.confirm_logout()
            return

        # Tắt loading, hiện nội dung thật
        self.content_area.update()

    def render(self):
        # --- QUAN TRỌNG: Lần đầu render KHÔNG gọi update() ---
        # Chỉ gán nội dung, Flet sẽ tự vẽ khi chạy lệnh page.add bên dưới
        self.content_area.content = ResidentsView(self.page).get_content()

        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon="person", 
                    label="Cá Nhân"
                ),
                ft.NavigationRailDestination(
                    icon="home", 
                    label="Hộ Khẩu"
                ),
                ft.NavigationRailDestination(
                    icon="upload_file", 
                    label="Nhập Liệu"
                ),
                ft.NavigationRailDestination(
                    icon="file_download", 
                    label="Báo Cáo"
                ),
                ft.NavigationRailDestination(
                    icon="pie_chart", 
                    label="Thống Kê"
                ),
                ft.NavigationRailDestination(
                    icon="settings", 
                    label="Hệ Thống"
                ),
                ft.NavigationRailDestination(
                    icon="logout", 
                    label="Đăng Xuất", 
                ),
            ],
            on_change=self.change_tab,
        )

        self.page.add(
            ft.Row(
                [
                    self.rail,
                    ft.VerticalDivider(width=1, thickness=1, color="grey300"),
                    self.content_area,
                ],
                expand=True,
            )
        )

    def confirm_logout(self):
        def on_confirm(e):
            dlg.open = False
            self.page.update()
            
            # Xóa session (nếu có)
            self.page.session.clear()

            # Đóng cửa sổ an toàn
            try:
                self.page.window.close() 
            except Exception:
                sys.exit()

        def on_cancel(e):
            dlg.open = False
            
            # Reset thanh menu về tab đầu tiên
            self.rail.selected_index = 0
            
            # Load lại tab đầu có hiệu ứng loading
            self.show_loading(with_update=True)
            self.content_area.content = ResidentsView(self.page).get_content()
            self.content_area.update()
            
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Xác nhận"),
            content=ft.Text("Bạn có chắc chắn muốn thoát phần mềm?"),
            actions=[
                ft.TextButton("Hủy", on_click=on_cancel),
                ft.ElevatedButton(
                    "Thoát", 
                    on_click=on_confirm, 
                    style=ft.ButtonStyle(color="white", bgcolor="red")
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
        self.page.open(dlg)
        self.page.update()