import flet as ft
import pandas as pd
import os
from datetime import datetime
from database.db_manager import db

class ExportView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.primary_color = "blue700"
        self.bg_color = "bluegrey50"
        
        # FilePicker
        self.save_picker = ft.FilePicker(on_result=self.on_save_result)
        self.page.overlay.append(self.save_picker)
        self.page.update()

        self.current_export_type = None 
        self.log_view = ft.Column(scroll=ft.ScrollMode.AUTO, height=150, spacing=2)
        
        self.render()

    def get_content(self):
        return self.content

    def render(self):
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Xuất Báo Cáo & Danh Sách", size=28, weight="bold", color="black87"),
                    ft.Text("Trích xuất dữ liệu ra file Excel (.xlsx) để in ấn", size=14, color="grey500"),
                ]),
                ft.Icon("file_download", size=50, color="green200"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            margin=ft.margin.only(bottom=20)
        )

        # Các nút chức năng
        actions_card = ft.Container(
            content=ft.Column([
                ft.Text("Chọn loại báo cáo:", size=16, weight="bold", color="blue900"),
                ft.Divider(),
                ft.ResponsiveRow([
                    ft.Column([self.build_export_btn("Danh sách Cử tri (18+)", "how_to_vote", "green", "voters")], col={"md": 4}),
                    ft.Column([self.build_export_btn("Người cao tuổi (>60)", "elderly", "orange", "elderly")], col={"md": 4}),
                    ft.Column([self.build_export_btn("Trẻ em (<16)", "child_care", "pink", "children")], col={"md": 4}),
                    ft.Column([self.build_export_btn("Thanh niên (16-30)", "face", "blue", "youth")], col={"md": 4}),
                    ft.Column([self.build_export_btn("Đảng viên", "star", "red", "party")], col={"md": 4}),
                    ft.Column([self.build_export_btn("Toàn bộ Dân cư", "groups", "grey", "all")], col={"md": 4}),
                    ft.Column([self.build_export_btn("Danh sách Hộ khẩu", "home", "teal", "households")], col={"md": 4}),
                ], run_spacing=20)
            ]),
            padding=20, bgcolor="white", border_radius=10,
            shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
        )

        # Log
        logs_card = ft.Container(
            content=ft.Column([
                ft.Text("Trạng thái xuất file", size=14, weight="bold"),
                ft.Container(
                    content=self.log_view,
                    bgcolor="black", border_radius=5, padding=10, height=150
                )
            ]),
            padding=20, bgcolor="white", border_radius=10, margin=ft.margin.only(top=20),
            shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
        )

        self.content = ft.Container(
            content=ft.Column([header, actions_card, logs_card], scroll=ft.ScrollMode.AUTO),
            padding=30, bgcolor=self.bg_color, expand=True
        )

    def build_export_btn(self, text, icon, color, export_type):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="white", size=24),
                ft.Text(text, weight="bold", color="white", size=14)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=f"{color}500",
            padding=20, border_radius=10,
            ink=True,
            on_click=lambda e: self.prepare_export(export_type),
            shadow=ft.BoxShadow(blur_radius=5, color=f"{color}200")
        )

    def log(self, msg, color="white"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.controls.append(ft.Text(f"[{timestamp}] {msg}", color=color, font_family="Consolas", size=12))
        self.log_view.update()

    def prepare_export(self, export_type):
        self.current_export_type = export_type
        filename = f"BaoCao_{export_type}_{datetime.now().strftime('%d%m%Y')}.xlsx"
        self.save_picker.save_file(dialog_title="Lưu báo cáo Excel", file_name=filename, allowed_extensions=["xlsx"])

    def on_save_result(self, e: ft.FilePickerResultEvent):
        if not e.path: return
        
        save_path = e.path
        ex_type = self.current_export_type
        self.log(f"Đang tạo báo cáo '{ex_type}'...", "yellow")

        try:
            # Xử lý xuất Hộ Khẩu
            if ex_type == "households":
                data = db.get_all_households()
                # data là list tuple: (ma_hk, ten_chu_ho, dia_chi, ngay_lap, count_mem, cccd_chu_ho)
                cols = ["Mã HK", "Chủ Hộ", "Địa Chỉ", "Ngày Lập", "Số Thành Viên", "CCCD Chủ Hộ"]
                df = pd.DataFrame(data, columns=cols)
            
            # Xử lý xuất Cư Dân
            else:
                data = db.get_all_residents()
                # Tuple: 0:cccd, 1:ten, 2:gt, 3:ns, 4:bhyt, 5:nghe, 6:sdt, 7:chinhtri, 8:chinhsach, 
                # 9:tinh, 10:phuong, 11:khom, 12:chitiet, 13:quanhe, 14:trinhdo, 15:ma_hk, 16:is_chu_ho, 17:dantoc, 18:tongiao
                cols = ["CCCD", "Họ Tên", "Giới Tính", "Ngày Sinh", "BHYT", "Nghề Nghiệp", "SĐT", 
                        "Chính Trị - XH", "Chính Sách", "Tỉnh", "Phường", "Khóm", "ĐC Chi Tiết", 
                        "Quan Hệ", "Trình Độ", "Mã HK", "Là Chủ Hộ", "Dân Tộc", "Tôn Giáo"]
                
                # Kiểm tra độ dài tuple để tránh lỗi nếu data cũ thiếu trường
                safe_data = []
                for r in data:
                    row_list = list(r)
                    # Nếu thiếu cột (do data cũ), bù thêm chuỗi rỗng
                    while len(row_list) < len(cols):
                        row_list.append("")
                    safe_data.append(row_list)

                df = pd.DataFrame(safe_data, columns=cols)

                # --- Logic Lọc ---
                curr_year = datetime.now().year
                def get_age(dob):
                    try: return curr_year - int(str(dob).split("/")[-1])
                    except: return 0
                
                df['Tuổi'] = df['Ngày Sinh'].apply(get_age)

                if ex_type == "voters": # 18+
                    df = df[df['Tuổi'] >= 18]
                elif ex_type == "elderly": # >60
                    df = df[df['Tuổi'] >= 60]
                elif ex_type == "children": # <16
                    df = df[df['Tuổi'] <= 16]
                elif ex_type == "youth": # 16-30
                    df = df[(df['Tuổi'] >= 16) & (df['Tuổi'] <= 30)]
                elif ex_type == "party": # Đảng viên
                    df = df[df['Chính Trị - XH'].str.contains("Đảng", na=False, case=False)]

            if df.empty:
                self.log("⚠️ Không có dữ liệu phù hợp!", "orange")
                return

            # Xuất file
            df.to_excel(save_path, index=False)
            self.log(f"✅ Xuất thành công {len(df)} dòng!", "green")
            self.log(f"Đã lưu: {save_path}", "green")
            
            try: os.startfile(save_path)
            except: pass

        except Exception as ex:
            self.log(f"❌ Lỗi xuất file: {ex}", "red")