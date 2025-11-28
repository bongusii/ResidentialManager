import flet as ft
import json
import os
from datetime import datetime
from database.db_manager import db
from utils.security import verify_password, hash_password

class SettingsView:
    def __init__(self, page: ft.Page):
        self.page = page

        self.current_user = self.page.session.get("username")
        self.current_role = self.page.session.get("role")
        # FilePicker
        self.save_file_dialog = ft.FilePicker(on_result=self.save_backup_result)
        self.pick_file_dialog = ft.FilePicker(on_result=self.restore_backup_result)
        
        self.page.overlay.extend([self.save_file_dialog, self.pick_file_dialog])
        self.page.update()
        
        self.user_list_view = ft.Column(spacing=10)
        self.render()

    def get_content(self):
        if self.current_role == "SuperAdmin":
            self.load_users()
        return self.content

    def render(self):
        sections = []
        
        header = ft.Column([
            ft.Text("Cài đặt & Hệ thống", size=28, weight="bold", color="black87"),
            ft.Text(f"Xin chào: {self.current_user} ({self.current_role})", size=14, color="blue", italic=True),
            ft.Divider(),
        ])
        sections.append(header)

        # --- KHỐI 1: AN TOÀN DỮ LIỆU (CHỈ SUPERADMIN THẤY) ---
        if self.current_role == "SuperAdmin":
            backup_section = ft.Container(
                content=ft.Column([
                    ft.Text("An toàn dữ liệu (Admin Only)", size=18, weight="bold", color="red900"),
                    ft.Row([
                        self.build_action_card("Sao lưu dữ liệu", "Backup JSON", "cloud_upload", "green", lambda e: self.save_file_dialog.save_file(allowed_extensions=["json"], file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.json")),
                        self.build_action_card("Phục hồi dữ liệu", "Restore JSON", "cloud_download", "orange", lambda e: self.pick_file_dialog.pick_files(allow_multiple=False, allowed_extensions=["json"])),
                    ], spacing=20),

                    ft.Container(height=10),
                    ft.OutlinedButton("Tối ưu hóa dữ liệu (Fix Lag)", icon="speed", on_click=lambda e: self.fix_data_performance())
                ]),
                padding=20, bgcolor="white", border_radius=10, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
            )
            sections.append(backup_section)

            # --- KHỐI 2: QUẢN LÝ TÀI KHOẢN (CHỈ SUPERADMIN THẤY) ---
            user_manager_section = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Quản lý Người dùng", size=18, weight="bold", color="blue900"),
                        ft.IconButton(icon="person_add", icon_color="blue", tooltip="Thêm tài khoản mới", on_click=lambda e: self.open_add_user_dialog())
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text("Danh sách tài khoản hệ thống:", size=12, color="grey"),
                    ft.Divider(),
                    self.user_list_view,
                ]),
                padding=20, bgcolor="white", border_radius=10, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
            )
            sections.append(user_manager_section)

        # --- KHỐI 3: TÀI KHOẢN CÁ NHÂN (AI CŨNG THẤY) ---
        personal_section = ft.Container(
            content=ft.Column([
                ft.Text("Cá nhân", size=18, weight="bold", color="blue900"),
                ft.Row([
                    self.build_action_card(
                        "Đổi mật khẩu", "Thay đổi mật khẩu của bạn", "lock_reset", "blue", 
                        lambda e: self.open_change_password_dialog(is_self=True) # is_self=True: Đổi cho chính mình
                    ),
                ], spacing=20)
            ]),
            padding=20, bgcolor="white", border_radius=10, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
        )
        sections.append(personal_section)

        self.content = ft.Container(
            content=ft.Column(sections, spacing=30, scroll=ft.ScrollMode.AUTO),
            padding=30, bgcolor="bluegrey50", expand=True
        )

    def build_action_card(self, title, subtitle, icon, color, on_click):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=35, color=f"{color}500"),
                ft.Column([ft.Text(title, weight="bold", size=15), ft.Text(subtitle, size=12, color="grey")], expand=True),
                ft.Icon("arrow_forward_ios", size=14, color="grey")
            ]),
            padding=15, bgcolor="white", border_radius=10, border=ft.border.all(1, "grey200"), width=350, ink=True, on_click=on_click
        )

    # --- QUẢN LÝ USER (CẬP NHẬT) ---
    def load_users(self):
        self.user_list_view.controls.clear()
        users = db.get_all_users()
        
        # Sắp xếp: Admin luôn ở đầu
        users.sort(key=lambda x: x.get('username') != 'admin')

        for u in users:
            username = u.get('username')
            role = u.get('role', 'Cán bộ')
            
            # Row chứa các nút hành động
            action_buttons = []
            
            # Nút Sửa (Edit) - Ai cũng sửa được (Admin sửa chính mình thì chỉ đổi pass)
            action_buttons.append(
                ft.IconButton(icon="edit", icon_color="blue", tooltip="Sửa thông tin", 
                              on_click=lambda e, u=username, r=role: self.open_edit_user_dialog(u, r))
            )

            # Nút Xóa (Delete) - Không hiện cho admin gốc
            if username != 'admin':
                action_buttons.append(
                    ft.IconButton(icon="delete", icon_color="red", tooltip="Xóa", 
                                  on_click=lambda e, u=username: self.delete_user_confirm(u))
                )

            item = ft.Container(
                content=ft.Row([
                    ft.Icon("account_circle", size=35, color="orange" if username=='admin' else "blue"),
                    ft.Column([
                        ft.Text(username, weight="bold", size=16),
                        ft.Container(
                            content=ft.Text(role, size=10, color="white", weight="bold"),
                            bgcolor="grey", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4
                        )
                    ], spacing=2, expand=True),
                    ft.Row(action_buttons, spacing=0)
                ]),
                padding=10, border=ft.border.all(1, "grey200"), border_radius=8, bgcolor="grey50"
            )
            self.user_list_view.controls.append(item)
        self.page.update()

    # --- DIALOG THÊM USER ---
    def open_add_user_dialog(self):
        txt_user = ft.TextField(label="Tên đăng nhập")
        txt_pass = ft.TextField(label="Mật khẩu", password=True, can_reveal_password=True)
        txt_role = ft.Dropdown(label="Vai trò", options=[ft.dropdown.Option("Cán bộ"), ft.dropdown.Option("Lãnh đạo"), ft.dropdown.Option("Thư ký")], value="Cán bộ")
        
        def save(e):
            if not txt_user.value or not txt_pass.value: return
            if db.create_user(txt_user.value, txt_pass.value, txt_role.value):
                self.show_snack(f"✅ Đã tạo user {txt_user.value}", "green")
                dlg.open = False
                self.load_users()
                self.page.update()
            else:
                self.show_snack("❌ Tên đăng nhập đã tồn tại!", "red")

        dlg = ft.AlertDialog(title=ft.Text("Thêm người dùng"), content=ft.Column([txt_user, txt_pass, txt_role], height=200), actions=[ft.ElevatedButton("Lưu", on_click=save)])
        self.page.open(dlg); self.page.update()

    # --- DIALOG SỬA USER (MỚI) ---
    def open_edit_user_dialog(self, username, current_role):
        # Username không cho sửa (Read-only)
        txt_user = ft.TextField(label="Tên đăng nhập", value=username, read_only=True, disabled=True, bgcolor="grey100")
        
        # Mật khẩu mới (Để trống nếu không đổi)
        txt_pass = ft.TextField(label="Mật khẩu mới (Để trống nếu không đổi)", password=True, can_reveal_password=True)
        
        # Role
        txt_role = ft.Dropdown(
            label="Vai trò", 
            options=[ft.dropdown.Option("Cán bộ"), ft.dropdown.Option("Lãnh đạo"), ft.dropdown.Option("Thư ký"), ft.dropdown.Option("SuperAdmin")], 
            value=current_role
        )
        
        # Admin gốc không được hạ quyền chính mình
        if username == 'admin':
            txt_role.disabled = True

        def save(e):
            new_pass = txt_pass.value
            new_role = txt_role.value
            
            # Gọi hàm update
            db.update_user(username, new_password=new_pass, new_role=new_role)
            
            self.show_snack(f"✅ Đã cập nhật {username}", "green")
            dlg.open = False
            self.load_users()
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Chỉnh sửa: {username}"),
            content=ft.Container(
                content=ft.Column([
                    txt_user,
                    txt_pass,
                    txt_role,
                    ft.Text("* Nếu quên mật khẩu, hãy nhập mật khẩu mới vào ô trên để reset.", size=12, italic=True, color="grey")
                ], height=220),
                width=400
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()),
                ft.ElevatedButton("Cập nhật", on_click=save)
            ]
        )
        self.page.open(dlg)
        self.page.update()

    def delete_user_confirm(self, username):
        def confirm(e):
            if db.delete_user(username):
                self.show_snack(f"✅ Đã xóa {username}", "green")
                dlg.open = False
                self.load_users()
                self.page.update()
            else:
                self.show_snack("❌ Không thể xóa user này!", "red")
        
        dlg = ft.AlertDialog(title=ft.Text("Xác nhận"), content=ft.Text(f"Xóa tài khoản {username}?"), actions=[ft.TextButton("Hủy", on_click=lambda e: setattr(dlg,'open',False) or self.page.update()), ft.ElevatedButton("Xóa", on_click=confirm, bgcolor="red", color="white")])
        self.page.open(dlg); self.page.update()

    # --- CÁC HÀM KHÁC (Backup, Change Pass...) ---
    def show_snack(self, msg, color):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

    def save_backup_result(self, e):
        if e.path:
            try:
                with open(e.path, "w", encoding="utf-8") as f: f.write(db.backup_to_json())
                self.show_snack("Sao lưu thành công!", "green")
            except Exception as ex: self.show_snack(str(ex), "red")

    def restore_backup_result(self, e):
        if e.files:
            try:
                with open(e.files[0].path, "r", encoding="utf-8") as f: db.restore_from_json(f.read())
                self.show_snack("Phục hồi thành công!", "green")
            except Exception as ex: self.show_snack(str(ex), "red")

    def open_change_password_dialog(self, is_self=False, target_user=None):
        if is_self: target_user = self.current_user
        
        txt_old = ft.TextField(label="Mật khẩu cũ", password=True, can_reveal_password=True)
        txt_new = ft.TextField(label="Mật khẩu mới", password=True, can_reveal_password=True)
        
        # Nếu là Admin reset pass người khác thì không cần nhập pass cũ
        if not is_self: 
            txt_old.visible = False
            title_text = f"Reset mật khẩu cho {target_user}"
        else:
            title_text = "Đổi mật khẩu cá nhân"

        def save(e):
            if not txt_new.value: return
            
            # Nếu tự đổi pass thì phải check pass cũ
            if is_self:
                # Gọi hàm verify_login để check pass cũ của chính user đó
                if not db.verify_login(target_user, txt_old.value):
                    self.show_snack("Mật khẩu cũ không đúng!", "red")
                    return

            try:
                # Gọi hàm đổi pass (db_manager cần có hàm này, nếu chưa có thì dùng update_user)
                # Tái sử dụng hàm update_user đã viết ở bước trước
                db.update_user(target_user, new_password=txt_new.value)
                
                dlg.open = False
                self.show_snack("Đổi mật khẩu thành công!", "green")
                self.page.update()
            except Exception as ex:
                self.show_snack(str(ex), "red")

        dlg = ft.AlertDialog(
            title=ft.Text(title_text),
            content=ft.Container(height=200 if is_self else 100, content=ft.Column([txt_old, txt_new])),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()),
                ft.ElevatedButton("Lưu", on_click=save)
            ]
        )
        self.page.open(dlg)
        self.page.update()

    def fix_data_performance(self):
        self.show_snack("Đang tối ưu hóa dữ liệu... Vui lòng đợi!", "blue")
        
        try:
            # Lấy tất cả mã hộ khẩu
            all_hks = db.db.collection('households').stream()
            count = 0
            for hk in all_hks:
                # Gọi hàm tính toán lại cho từng hộ
                db.recalculate_household_info(hk.id)
                count += 1
            
            self.show_snack(f"✅ Đã tối ưu xong {count} hộ khẩu! Tốc độ sẽ nhanh hơn.", "green")
        except Exception as ex:
            self.show_snack(f"❌ Lỗi: {ex}", "red")