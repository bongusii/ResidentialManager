import flet as ft
from database.db_manager import db

class LoginView:
    def __init__(self, page: ft.Page, on_success):
        self.page = page
        self.on_success = on_success
        
        # Các controls
        self.username = ft.TextField(label="Tên đăng nhập", width=300, border_radius=10)
        self.password = ft.TextField(label="Mật khẩu", password=True, can_reveal_password=True, width=300, border_radius=10, on_submit=self.handle_login)
        self.error_text = ft.Text(color="red", size=14)
        
        self.render()

    def handle_login(self, e):
        # Reset thông báo lỗi
        self.error_text.value = ""
        self.error_text.update()

        # Kiểm tra nhập liệu
        if not self.username.value or not self.password.value:
            self.error_text.value = "Vui lòng nhập đầy đủ thông tin!"
            self.error_text.update()
            return

        # Kiểm tra auth qua Database Manager
        if db.verify_login(self.username.value, self.password.value):
            # --- CẬP NHẬT QUAN TRỌNG: LƯU SESSION ---
            role = db.get_user_role(self.username.value)
            
            # Lưu vào bộ nhớ phiên làm việc của Flet
            self.page.session.set("username", self.username.value)
            self.page.session.set("role", role)
            
            print(f"Đăng nhập thành công: {self.username.value} - Quyền: {role}") # Debug log
            
            self.on_success()

        else:
            self.error_text.value = "Sai tên đăng nhập hoặc mật khẩu!"
            self.error_text.update()

    def render(self):
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(name="LOCATION_CITY_OUTLINED", size=80, color="blue700"),
                        ft.Text("HỆ THỐNG QUẢN LÝ DÂN CƯ", size=24, weight="bold", color="blue900"),
                        
                        ft.Container(height=20), # Khoảng cách
                        
                        self.username,
                        self.password,
                        
                        ft.Container(height=10),
                        self.error_text,
                        ft.Container(height=10),
                        
                        ft.ElevatedButton(
                            "Đăng nhập", 
                            on_click=self.handle_login, 
                            width=300, 
                            height=50,
                            style=ft.ButtonStyle(
                                color="white",
                                bgcolor="blue700",
                                shape=ft.RoundedRectangleBorder(radius=10),
                            )
                        ),

                        ft.Container(height=180),

                        ft.Text("2025 © Phan Hoàng Anh", size=14, color="grey500"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
                # Thêm background gradient nhẹ cho đẹp
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#F0F4F8", "#D9E2EC"],
                )
            )
        )