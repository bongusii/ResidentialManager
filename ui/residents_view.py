
import time
import json
import flet as ft
from database.db_manager import db
from datetime import datetime
from utils.vn_locations import LOCATION_DATA

# Dữ liệu Khóm cụ thể cho Phường Long Xuyên
PHUONG_LONG_XUYEN_DATA = [
    "Khóm 1", "Khóm 2", "Khóm 3", "Khóm 4", "Khóm 5", "Khóm 6", "Khóm 7",
    "Khóm Bình Long 1", "Khóm Bình Long 2", "Khóm Bình Long 3", "Khóm Bình Long 4",
    "Khóm Đông An", "Khóm Đông An 1", "Khóm Đông An 2", "Khóm Đông An 4", "Khóm Đông An 5", "Khóm Đông An 6",
    "Khóm Đông Thịnh 1", "Khóm Đông Thịnh 2", "Khóm Đông Thịnh 3", "Khóm Đông Thịnh 4", 
    "Khóm Đông Thịnh 5", "Khóm Đông Thịnh 6", "Khóm Đông Thịnh 7", "Khóm Đông Thịnh 8", "Khóm Đông Thịnh 9",
    "Khóm Tây Khánh 1", "Khóm Tây Khánh 2", "Khóm Tây Khánh 3", "Khóm Tây Khánh 4", 
    "Khóm Tây Khánh 5", "Khóm Tây Khánh 6", "Khóm Tây Khánh 7",
    "Khóm Tây Huề 1", "Khóm Tây Huề 2", "Khóm Tây Huề 3",
    "Khóm Đông Hưng", "Khóm Đông Phú", "Khóm Đông Thành", 
    "Khóm Mỹ Lộc", "Khóm Mỹ Phú", "Khóm Mỹ Quới", "Khóm Mỹ Thọ", 
    "Khóm Nguyễn Du", "Khóm Phó Quế", "Khóm Tân Phú", "Khóm Tân Quới"
]

class ResidentsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.primary_color = "blue700"
        self.bg_color = "bluegrey50"
        self.card_bg = "white"
        
        self.total_residents_text = ft.Text("0", size=30, weight="bold", color=self.primary_color)
        
        # Biến lưu trữ toàn bộ dữ liệu gốc để tìm kiếm
        self.all_data = []

        # Controls lọc & tìm kiếm
        self.tf_search = ft.TextField(
            hint_text="Tìm tên / CCCD...", prefix_icon="search", 
            border_radius=8, height=40, content_padding=10, 
            expand=True, bgcolor=self.card_bg, border_color="transparent", 
            text_size=13, on_change=self.apply_filters
        )

        # Tuổi: Giảm width
        self.tf_age_min = ft.TextField(
            hint_text="Tuổi từ", prefix_icon="cake", 
            width=100, height=40, text_size=12, content_padding=10, 
            keyboard_type=ft.KeyboardType.NUMBER, border_radius=8, 
            bgcolor="white", on_change=self.apply_filters
        )
        self.tf_age_max = ft.TextField(
            hint_text="Đến tuổi", 
            width=90, height=40, text_size=12, content_padding=10, 
            keyboard_type=ft.KeyboardType.NUMBER, border_radius=8, 
            bgcolor="white", on_change=self.apply_filters
        )
        
        # 2. Dropdowns (Thay Label bằng Icon + Hint)
        # Cấu trúc: build_filter_dropdown(Hint, Icon, Options)
        self.dd_filter_gender = self.build_filter_dropdown("Giới tính", "wc", ["Tất cả", "Nam", "Nữ"])
        self.dd_filter_edu = self.build_filter_dropdown("Trình độ", "school", ["Tất cả", "Chưa đi học","Tiểu học","THCS","THPT","Trung cấp","Cao đẳng","Đại học","Thạc sĩ","Tiến sĩ"])
        self.dd_filter_eth = self.build_filter_dropdown("Dân tộc", "people_outline", ["Tất cả", "Kinh", "Hoa", "Khmer", "Chăm", "Khác"])
        self.dd_filter_rel = self.build_filter_dropdown("Tôn giáo", "temple_buddhist", ["Tất cả", "Không", "Phật giáo", "Công giáo", "Tin lành", "Hòa hảo", "Cao đài", "Hồi giáo"])
        
        self.dd_filter_poli = self.build_filter_dropdown("Chính trị", "groups", ["Tất cả", "Đảng CS Việt Nam", "Đoàn TNCS HCM", "Hội Phụ nữ", "Hội Nông dân", "Hội Cựu chiến binh"])
        self.dd_filter_policy = self.build_filter_dropdown("Chính sách", "loyalty", ["Tất cả", "Hộ nghèo", "Hộ cận nghèo", "Con thương binh", "Con liệt sĩ", "Gia đình chính sách"])

        # 3. Địa chỉ
        self.dd_filter_tinh = self.build_filter_dropdown("Tỉnh/TP", "map", ["Tất cả"] + list(LOCATION_DATA.keys()))
        self.dd_filter_phuong = self.build_filter_dropdown("Phường/Xã", "location_city", ["Tất cả"])
        self.dd_filter_khom = self.build_filter_dropdown("Khóm/Ấp", "store", ["Tất cả"])
        
        self.tf_filter_to = ft.TextField(
            hint_text="Tổ/Chi tiết", prefix_icon="signpost",
            width=140, height=40, text_size=12, content_padding=10, 
            border_radius=8, bgcolor="white", on_change=self.apply_filters
        )

        # Sự kiện Cascade
        self.dd_filter_tinh.on_change = self.on_filter_province_change
        self.dd_filter_phuong.on_change = self.on_filter_ward_change

        # Bảng dữ liệu
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("CCCD", weight="bold")),
                ft.DataColumn(ft.Text("Họ Tên", weight="bold")),
                ft.DataColumn(ft.Text("Giới Tính", weight="bold")),
                ft.DataColumn(ft.Text("Ngày Sinh", weight="bold")),
                ft.DataColumn(ft.Text("Hành động", weight="bold")),
            ],
            rows=[],
            heading_row_color="blue50",
            heading_row_height=50, # Giảm chiều cao header chút
            data_row_min_height=50,
            column_spacing=40,
            border=ft.border.all(1, "grey200"),
            border_radius=10,
            width=1250, 
        )
        
        self.load_data()

    def build_filter_dropdown(self, hint, icon_name, options):
        return ft.Dropdown(
            hint_text=hint,        # Chữ mờ hướng dẫn
            prefix_icon=icon_name, # Icon ở đầu
            options=[ft.dropdown.Option(x) for x in options],
            text_size=10,
            content_padding=10,
            on_change=self.apply_filters,
            width=160,             # Độ rộng vừa phải
            border_radius=8,
            filled=True,
            bgcolor="white"
        )
    
    # --- CÁC HÀM XỬ LÝ EVENT BỘ LỌC ---
    def on_filter_province_change(self, e):
        sel = self.dd_filter_tinh.value
        self.dd_filter_phuong.options = [ft.dropdown.Option(x) for x in (["Tất cả"] + LOCATION_DATA.get(sel, []))] if sel != "Tất cả" else [ft.dropdown.Option("Tất cả")]
        self.dd_filter_phuong.value = "Tất cả"; self.dd_filter_khom.value = "Tất cả"; self.page.update(); self.apply_filters(None)

    def on_filter_ward_change(self, e):
        sel = self.dd_filter_phuong.value
        self.dd_filter_khom.options = [ft.dropdown.Option(x) for x in (["Tất cả"] + PHUONG_LONG_XUYEN_DATA)] if sel and "Long Xuyên" in sel else [ft.dropdown.Option("Tất cả")]
        self.dd_filter_khom.value = "Tất cả"; self.page.update(); self.apply_filters(None)
    
    # --- HÀM BẢO MẬT ---
    def show_auth_dialog(self, on_success_callback):
        txt_password = ft.TextField(label="Mật khẩu Admin", password=True, can_reveal_password=True, autofocus=True)
        lbl_error = ft.Text("", color="red", size=12)

        def check_pass(e):
            if db.verify_admin_action(txt_password.value):
                auth_dlg.open = False
                self.page.update()
                on_success_callback()
            else:
                lbl_error.value = "Mật khẩu không đúng!"
                lbl_error.update()

        auth_dlg = ft.AlertDialog(
            title=ft.Text("Xác thực bảo mật"),
            content=ft.Column([
                ft.Text("Vui lòng nhập mật khẩu để tiếp tục:", size=14),
                txt_password,
                lbl_error
            ], tight=True, width=300),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: setattr(auth_dlg, 'open', False) or self.page.update()),
                ft.ElevatedButton("Xác nhận", on_click=check_pass)
            ]
        )
        self.page.open(auth_dlg)
        self.page.update()

    # --- GIAO DIỆN CHÍNH ---
    def get_content(self):
        # header = ft.Container(
        #     content=ft.Row([
        #         ft.Column([ft.Text("Quản Lý Cư Dân", size=24, weight="bold", color="black87")]),
        #         ft.Container(content=ft.Row([ft.Icon("people", color="blue"), ft.Text(f"Tổng: {self.total_residents_text.value}", weight="bold")]), padding=10, border=ft.border.all(1,"grey200"), border_radius=8, bgcolor="white")
        #     ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        #     margin=ft.margin.only(bottom=10)
        # )

        header = ft.Container(content=ft.Row([ft.Column([ft.Text("Quản Lý Cư Dân", size=28, weight="bold", color="black87"), ft.Text("Danh sách và thông tin chi tiết", size=14, color="grey500")]), ft.Container(content=ft.Row([ft.Icon("people", size=40, color="blue200"), ft.Column([ft.Text("Tổng số", size=12, color="grey600"), self.total_residents_text], spacing=0)]), padding=15, border=ft.border.all(1, "grey200"), border_radius=12, bgcolor=self.card_bg)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), margin=ft.margin.only(bottom=20))

        toolbar = ft.Row([
            ft.TextField(
                hint_text="Tìm kiếm theo Tên hoặc CCCD...", prefix_icon="search", 
                border_radius=10, height=45, content_padding=10, 
                expand=True, bgcolor=self.card_bg, border_color="transparent", 
                text_size=14, 
                on_change=self.filter_data # <--- ĐÃ KÍCH HOẠT
            ),
            ft.ElevatedButton(
                "Thêm cư dân mới", icon="add", 
                style=ft.ButtonStyle(color="white", bgcolor=self.primary_color, padding=15, shape=ft.RoundedRectangleBorder(radius=10), elevation=2), 
                on_click=lambda e: self.open_form_dialog()
            )
        ])

        filter_controls = ft.Row(
            controls=[
                # Nhóm Tuổi
                self.tf_age_min, 
                ft.Text("-"), 
                self.tf_age_max,
                
                # Nhóm Dropdown (Đã có icon bên trong)
                self.dd_filter_gender,
                self.dd_filter_edu,
                self.dd_filter_eth,
                self.dd_filter_rel,
                self.dd_filter_poli,
                self.dd_filter_policy,
                
                # Nhóm Địa chỉ
                self.dd_filter_tinh,
                self.dd_filter_phuong,
                self.dd_filter_khom,
                self.tf_filter_to,

                # Nút Xóa
                ft.IconButton(icon="clear_all", icon_color="red", tooltip="Xóa bộ lọc", on_click=self.clear_filters)
            ],
            wrap=True, # Tự động xuống dòng nếu hết chỗ
            run_spacing=10, 
            spacing=10
        )

        filter_panel = ft.ExpansionTile(
            title=ft.Text("Bộ lọc", weight="bold", color="blue700", size=14),
            leading=ft.Icon("filter_list", color="blue", size=20),
            controls=[
                ft.Container(content=filter_controls, padding=10, bgcolor="#F7F9FC", border_radius=8)
            ],
            initially_expanded=False,
            tile_padding=ft.padding.symmetric(horizontal=10, vertical=0),
            min_tile_height=40 # Thu nhỏ chiều cao thanh tiêu đề
        )

        table_card = ft.Container(
            content=ft.Column([
                toolbar,
                filter_panel, # Đặt filter ngay dưới toolbar
                ft.Divider(height=5, color="transparent"),
                ft.Column([ft.Row([self.data_table], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.AUTO, expand=True)
            ], expand=True),
            padding=20, bgcolor=self.card_bg, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000"), expand=True
        )

        return ft.Container(content=ft.Column([header, table_card], spacing=0, expand=True), padding=20, bgcolor=self.bg_color, expand=True)

    # --- LOAD DỮ LIỆU & TÌM KIẾM ---
    def load_data(self):
        # Lấy dữ liệu gốc từ DB và lưu vào biến self.all_data
        self.all_data = db.get_all_residents()
        self.render_table(self.all_data) # Hiển thị toàn bộ
        self.apply_filters(None) # Gọi hàm lọc để hiển thị
    
    def clear_filters(self, e):
        """Reset tất cả ô nhập liệu về mặc định"""
        self.tf_search.value = ""
        self.tf_age_min.value = ""
        self.tf_age_max.value = ""
        self.dd_filter_gender.value = None
        self.dd_filter_edu.value = None
        self.dd_filter_eth.value = None
        self.dd_filter_rel.value = None
        self.dd_filter_poli.value = None
        self.dd_filter_policy.value = None

        self.dd_filter_tinh.value = None
        self.dd_filter_phuong.value = None
        self.dd_filter_khom.value = None
        self.tf_filter_to.value = ""

        self.page.update()
        self.apply_filters(None)

    # --- LOGIC LỌC DỮ LIỆU ---
    def apply_filters(self, e):
        filtered_data = self.all_data
        current_year = datetime.now().year

        # 1. Tìm kiếm Text (Tên hoặc CCCD)
        search_term = self.tf_search.value.lower() if self.tf_search.value else ""
        if search_term:
            filtered_data = [r for r in filtered_data if search_term in str(r[0]).lower() or search_term in str(r[1]).lower()]

        # 2. Lọc Giới tính (Index 2)
        if self.dd_filter_gender.value and self.dd_filter_gender.value != "Tất cả":
            filtered_data = [r for r in filtered_data if r[2] == self.dd_filter_gender.value]

        # 3. Lọc Trình độ (Index 14)
        if self.dd_filter_edu.value and self.dd_filter_edu.value != "Tất cả":
            filtered_data = [r for r in filtered_data if r[14] == self.dd_filter_edu.value]
        
        # 4. Lọc Dân tộc (Index 17) - Check length vì data cũ có thể thiếu cột này
        if self.dd_filter_eth.value and self.dd_filter_eth.value != "Tất cả":
            filtered_data = [r for r in filtered_data if len(r) > 17 and r[17] == self.dd_filter_eth.value]

        # 5. Lọc Tôn giáo (Index 18)
        if self.dd_filter_rel.value and self.dd_filter_rel.value != "Tất cả":
            filtered_data = [r for r in filtered_data if len(r) > 18 and r[18] == self.dd_filter_rel.value]

        # 6. Lọc Chính trị - XH (Index 7) - Kiểm tra chuỗi chứa
        if self.dd_filter_poli.value and self.dd_filter_poli.value != "Tất cả":
            target = self.dd_filter_poli.value
            filtered_data = [r for r in filtered_data if target in (r[7] or "")]

        # 7. Lọc Chính sách (Index 8) - Kiểm tra chuỗi chứa
        if self.dd_filter_policy.value and self.dd_filter_policy.value != "Tất cả":
            target = self.dd_filter_policy.value
            filtered_data = [r for r in filtered_data if target in (r[8] or "")]

        # 8. Lọc Tuổi (Tính từ Index 3: Ngày sinh)
        min_age = int(self.tf_age_min.value) if self.tf_age_min.value and self.tf_age_min.value.isdigit() else 0
        max_age = int(self.tf_age_max.value) if self.tf_age_max.value and self.tf_age_max.value.isdigit() else 999
        
        if min_age > 0 or max_age < 999:
            temp_res = []
            for r in filtered_data:
                age = 0
                try:
                    if "/" in str(r[3]):
                        born_year = int(str(r[3]).split("/")[-1])
                        age = current_year - born_year
                except: age = 0
                
                if min_age <= age <= max_age:
                    temp_res.append(r)
            filtered_data = temp_res

        # 9. Tỉnh/TP (Index 9)
        if self.dd_filter_tinh.value and self.dd_filter_tinh.value != "Tất cả":
            filtered_data = [r for r in filtered_data if r[9] == self.dd_filter_tinh.value]

        # 10. Phường/Xã (Index 10)
        if self.dd_filter_phuong.value and self.dd_filter_phuong.value != "Tất cả":
            filtered_data = [r for r in filtered_data if r[10] == self.dd_filter_phuong.value]

        # 11. Khóm/Ấp (Index 11)
        if self.dd_filter_khom.value and self.dd_filter_khom.value != "Tất cả":
            filtered_data = [r for r in filtered_data if r[11] == self.dd_filter_khom.value]

        # 12. Tổ / Chi tiết (Index 12) - Tìm kiếm tương đối
        # Lọc những người có "Địa chỉ chi tiết" chứa từ khóa nhập vào (VD: "Tổ 5")
        search_to = self.tf_filter_to.value.lower() if self.tf_filter_to.value else ""
        if search_to:
            filtered_data = [r for r in filtered_data if search_to in str(r[12]).lower()]

        # Render kết quả
        self.render_table(filtered_data)

    def filter_data(self, e):
        search_term = e.control.value.lower()
        if not search_term:
            # Nếu ô tìm kiếm trống -> Hiện tất cả
            self.render_table(self.all_data)
        else:
            # Lọc dữ liệu: Kiểm tra CCCD (index 0) hoặc Tên (index 1)
            filtered_data = [
                row for row in self.all_data 
                if search_term in str(row[0]).lower() or search_term in str(row[1]).lower()
            ]
            self.render_table(filtered_data)

    def render_table(self, data_list):
        """Hàm vẽ lại bảng dựa trên danh sách data truyền vào"""
        self.data_table.rows.clear()
        self.total_residents_text.value = str(len(data_list))
        
        for r in data_list:
            gender_color = "blue100" if r[2] == "Nam" else "pink100"
            gender_text_color = "blue900" if r[2] == "Nam" else "pink900"
            
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(r[0], font_family="Consolas")),
                        ft.DataCell(ft.Text(r[1], weight="w500")),
                        ft.DataCell(ft.Container(content=ft.Text(r[2], size=12, color=gender_text_color, weight="bold"), bgcolor=gender_color, padding=ft.padding.symmetric(horizontal=10, vertical=5), border_radius=20)),
                        ft.DataCell(ft.Text(r[3])),
                        ft.DataCell(ft.Row([
                            ft.IconButton(icon="visibility", icon_color="green", tooltip="Xem chi tiết", on_click=lambda e, cccd=r[0]: self.open_detail_dialog(cccd)),
                            ft.IconButton(icon="edit", icon_color="blue", tooltip="Sửa", on_click=lambda e, cccd=r[0]: self.open_form_dialog(cccd)),
                            ft.IconButton(icon="delete", icon_color="red", tooltip="Xóa", on_click=lambda e, cccd=r[0]: self.delete_resident(cccd)),
                        ], spacing=0))
                    ]
                )
            )
        try: self.page.update()
        except: pass

    # --- POPUP CHI TIẾT (READ-ONLY) ---
    def open_detail_dialog(self, cccd):
        data = db.get_resident_by_cccd(cccd)
        if not data: return
        r = data[0]

        addr_parts = [r[12], r[11], r[10], r[9]]
        full_addr = ", ".join([str(x) for x in addr_parts if x]) or "Chưa cập nhật"
        
        quan_he = r[13] if r[13] else "Chưa xác định"
        if r[16] == 1: quan_he = "CHỦ HỘ"
        ma_ho_khau = r[15] if r[15] else "Chưa có"
        
        dan_toc = r[17] if len(r) > 17 and r[17] else "Kinh"
        ton_giao = r[18] if len(r) > 18 and r[18] else "Không"

        def info_box(icon, label, value, color_icon="blue400", full_width=False):
            return ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(icon, size=16, color=color_icon), ft.Text(label, size=12, color="grey")]),
                    ft.Text(value if value else "---", size=14, weight="w500", color="black87", no_wrap=False, selectable=True)
                ], spacing=5),
                padding=12, bgcolor="grey50", border_radius=8,
                expand=1 if not full_width else None, width=None if not full_width else 700
            )

        content = ft.Container(
            width=800, padding=10,
            content=ft.Column([
                ft.Row([
                    ft.CircleAvatar(content=ft.Icon("person", size=50), radius=45, bgcolor="blue100"),
                    ft.Column([
                        ft.Text(r[1], size=26, weight="bold", color="blue900"),
                        ft.Container(content=ft.Text(f"CCCD: {r[0]}", color="white", size=13, weight="bold"), bgcolor="bluegrey", padding=ft.padding.symmetric(horizontal=10, vertical=4), border_radius=4)
                    ], spacing=5)
                ], alignment=ft.MainAxisAlignment.START),
                
                ft.Divider(height=20, color="transparent"),
                
                ft.Row([
                    info_box("wc", "Giới tính", r[2]),
                    info_box("cake", "Ngày sinh", r[3]),
                    info_box("school", "Trình độ", r[14]),
                ]),
                
                ft.Container(height=5),
                
                ft.Row([
                    info_box("people_outline", "Dân tộc", dan_toc),
                    info_box("temple_buddhist", "Tôn giáo", ton_giao),
                    info_box("medical_services", "BHYT", r[4])
                ]),

                ft.Container(height=5),
                
                ft.Row([
                    info_box("phone", "Số điện thoại", r[6]),
                    info_box("work", "Nghề nghiệp", r[5]),
                    info_box("home", "Hộ khẩu", ma_ho_khau, "orange"), 
                ]),

                ft.Container(height=5),
                
                ft.Text("Thông tin Chính trị & Xã hội", size=12, weight="bold", color="blue"),
                
                info_box("groups", "Chính trị - XH", r[7], "blue", full_width=True),
                ft.Container(height=5),
                info_box("policy", "Chế độ Chính sách", r[8], "red", full_width=True),

                ft.Divider(height=30),

                ft.Container(
                    content=ft.Row([
                        ft.Icon("location_on", size=24, color="red400"),
                        ft.Column([
                            ft.Text("Địa chỉ thường trú", size=11, color="red800"),
                            ft.Text(full_addr, size=15, weight="bold", color="black87", no_wrap=False)
                        ], spacing=2, expand=True)
                    ]),
                    padding=15, bgcolor="red50", border_radius=8
                )

            ], scroll=ft.ScrollMode.AUTO, spacing=5)
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Hồ Sơ Cư Dân", weight="bold"),
            content=content,
            actions=[
                ft.TextButton("Đóng", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()),
                ft.ElevatedButton("Chỉnh sửa", icon="edit", on_click=lambda e: self.open_form_dialog(r[0]))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)
        self.page.update()

    # --- XÓA CƯ DÂN ---
    def delete_resident(self, cccd):
        check = db.get_resident_by_cccd(cccd)
        if check and check[0][16] == 1: 
            self.page.open(ft.AlertDialog(title=ft.Text("Lỗi"), content=ft.Text("Không thể xóa Chủ hộ!"), open=True))
            self.page.update()
            return
        
        def confirm_delete_action():
            db.delete_resident(cccd)
            confirm_dlg.open = False
            self.load_data()
            self.page.update()

        def on_click_delete_confirm(e):
            self.show_auth_dialog(confirm_delete_action)

        confirm_dlg = ft.AlertDialog(
            title=ft.Text("Xác nhận xóa"), 
            content=ft.Text(f"Bạn có chắc muốn xóa cư dân {cccd}?"), 
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: setattr(confirm_dlg, 'open', False) or self.page.update()), 
                ft.ElevatedButton("Xóa", on_click=on_click_delete_confirm, style=ft.ButtonStyle(color="red"))
            ], 
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(confirm_dlg)
        self.page.update()

    # --- MULTI-SELECT HELPER ---
    def create_multi_select_group(self, label, options, initial_value=""):
        checkboxes = []
        selected_items = [x.strip() for x in initial_value.split(",")] if initial_value else []
        result_text = ft.Text(value=initial_value if initial_value else "Chưa chọn...", color=self.primary_color)

        def on_change(e):
            current = [cb.label for cb in checkboxes if cb.value]
            if other_cb.value and other_input.value: current.append(f"Khác: {other_input.value}")
            result_text.value = ", ".join(current) if current else "Chưa chọn..."
            result_text.update()

        for opt in options: checkboxes.append(ft.Checkbox(label=opt, value=opt in selected_items, on_change=on_change))
        
        other_input = ft.TextField(label="Nhập cụ thể...", height=30, text_size=12, visible=False, on_change=on_change)
        has_other = any(item.startswith("Khác:") for item in selected_items)
        if has_other: 
            other_input.value = [i for i in selected_items if i.startswith("Khác:")][0].replace("Khác: ", "")
            other_input.visible = True

        def toggle_other(e):
            other_input.visible = other_cb.value
            other_input.update()
            on_change(e)

        other_cb = ft.Checkbox(label="Khác", value=has_other, on_change=toggle_other)
        tile = ft.ExpansionTile(title=ft.Column([ft.Text(label, size=12, weight="bold", color="grey"), result_text], spacing=2), controls=[ft.Column([*checkboxes, other_cb, other_input], spacing=0)], collapsed_text_color="black", text_color="black")
        tile.data = result_text 
        return tile

    # --- FORM NHẬP LIỆU ---
    def open_form_dialog(self, cccd_edit=None):
        txt_cccd = ft.TextField(label="CCCD", read_only=False, border_radius=8)
        txt_hoten = ft.TextField(label="Họ và tên", border_radius=8)
        dd_gioitinh = ft.Dropdown(label="Giới tính", options=[ft.dropdown.Option("Nam"), ft.dropdown.Option("Nữ")], border_radius=8)
        txt_ngaysinh = ft.TextField(label="Ngày sinh (DD/MM/YYYY)", border_radius=8)
        txt_bhyt = ft.TextField(label="BHYT", border_radius=8)
        txt_nghe = ft.TextField(label="Nghề nghiệp", border_radius=8)
        txt_sdt = ft.TextField(label="Số điện thoại", border_radius=8)
        
        dd_trinhdo = ft.Dropdown(label="Trình độ học vấn", options=[ft.dropdown.Option(x) for x in ["Chưa đi học","Tiểu học","THCS","THPT","Trung cấp","Cao đẳng","Đại học","Thạc sĩ","Tiến sĩ","Khác"]], border_radius=8)
        dd_dantoc = ft.Dropdown(label="Dân tộc", options=[ft.dropdown.Option(x) for x in ["Kinh", "Hoa", "Khmer", "Chăm", "Tày", "Mường", "Nùng", "H'Mông", "Thái", "Dao", "Khác"]], border_radius=8)
        dd_tongiao = ft.Dropdown(label="Tôn giáo", options=[ft.dropdown.Option(x) for x in ["Không", "Phật giáo", "Công giáo", "Tin lành", "Cao đài", "Hòa hảo", "Hồi giáo", "Khác"]], border_radius=8)

        dd_tinh = ft.Dropdown(label="Tỉnh / Thành phố", border_radius=8, expand=1)
        dd_phuong = ft.Dropdown(label="Phường / Xã", border_radius=8, expand=1)
        dd_khom = ft.Dropdown(label="Khóm / Ấp", border_radius=8, expand=1, hint_text="Chọn Phường trước", disabled=True)
        txt_chitiet = ft.TextField(label="Số nhà, đường...", border_radius=8, expand=1)

        dd_tinh.options = [ft.dropdown.Option(k) for k in LOCATION_DATA.keys()]

        def on_phuong_change(e):
            if dd_phuong.value == "P. Long Xuyên" or dd_phuong.value == "TP. Long Xuyên - P. Long Xuyên": 
                dd_khom.options = [ft.dropdown.Option(k) for k in PHUONG_LONG_XUYEN_DATA]
                dd_khom.disabled = False
                dd_khom.hint_text = "Chọn Khóm"
            else:
                dd_khom.options = []
                dd_khom.disabled = True
                dd_khom.hint_text = "Chưa có dữ liệu"
                dd_khom.value = None
            dd_khom.update()

        def on_province_change(e):
            dd_phuong.options = [ft.dropdown.Option(x) for x in LOCATION_DATA.get(dd_tinh.value, [])]
            dd_phuong.value = None; dd_khom.value = None; dd_khom.options = []; dd_khom.disabled = True
            dd_phuong.update(); dd_khom.update()

        dd_tinh.on_change = on_province_change
        dd_phuong.on_change = on_phuong_change
        val_chinhtri, val_chinhsach = "", ""
        
        if cccd_edit:
            data = db.get_resident_by_cccd(cccd_edit)
            if data:
                r = data[0]
                txt_cccd.value, txt_hoten.value = r[0], r[1]
                dd_gioitinh.value, txt_ngaysinh.value = r[2], r[3]
                txt_bhyt.value, txt_nghe.value, txt_sdt.value = r[4], r[5], r[6]
                val_chinhtri, val_chinhsach = r[7], r[8]
                dd_tinh.value = r[9]
                if r[9]: dd_phuong.options = [ft.dropdown.Option(x) for x in LOCATION_DATA.get(r[9], [])]
                dd_phuong.value = r[10]
                if r[10] and "Long Xuyên" in r[10]: 
                    dd_khom.options = [ft.dropdown.Option(k) for k in PHUONG_LONG_XUYEN_DATA]
                    dd_khom.disabled = False
                dd_khom.value, txt_chitiet.value = r[11], r[12]
                dd_trinhdo.value = r[14]
                if len(r) > 17: dd_dantoc.value = r[17]
                if len(r) > 18: dd_tongiao.value = r[18]

        group_chinhtri = self.create_multi_select_group("Chính trị - Xã hội", ["Đảng CS Việt Nam", "Đoàn TNCS HCM", "Hội Phụ nữ", "Hội Nông dân", "Hội Cựu chiến binh"], val_chinhtri)
        group_chinhsach = self.create_multi_select_group("Chế độ Chính sách", ["Hộ nghèo", "Hộ cận nghèo", "Con thương binh", "Con liệt sĩ", "Gia đình chính sách"], val_chinhsach)

        def save_data(e):
            if not txt_cccd.value or not txt_hoten.value:
                txt_cccd.error_text = "Bắt buộc"
                txt_cccd.update()
                return
            
            def execute_save():
                data_dict = {
                    'ho_ten': txt_hoten.value, 'gioi_tinh': dd_gioitinh.value, 'ngay_sinh': txt_ngaysinh.value,
                    'bhyt': txt_bhyt.value, 'nghe_nghiep': txt_nghe.value, 'sdt': txt_sdt.value,
                    'chinh_tri_xh': group_chinhtri.data.value if "Chưa chọn" not in group_chinhtri.data.value else "",
                    'che_do_chinh_sach': group_chinhsach.data.value if "Chưa chọn" not in group_chinhsach.data.value else "",
                    'tinh_thanh': dd_tinh.value, 'phuong_xa': dd_phuong.value, 'khom_ap': dd_khom.value, 'dia_chi_chi_tiet': txt_chitiet.value,
                    'trinh_do': dd_trinhdo.value, 'dan_toc': dd_dantoc.value, 'ton_giao': dd_tongiao.value
                }
                try:
                    db.upsert_resident(txt_cccd.value, data_dict)
                    dlg.open = False
                    self.load_data()
                    self.page.update()
                    # Reload detail nếu đang mở
                    if cccd_edit: pass
                except Exception as ex:
                    self.page.open(ft.AlertDialog(title=ft.Text("Lỗi"), content=ft.Text(f"Lỗi hệ thống: {ex}"), open=True))
                    self.page.update()

            self.show_auth_dialog(execute_save)

        dlg = ft.AlertDialog(
            title=ft.Text("Thông tin Cư Dân", weight="bold"),
            content=ft.Container(
                width=800, height=600,
                content=ft.Column([
                    ft.Text("Thông tin cơ bản", weight="bold", color="blue"),
                    ft.Row([txt_cccd, txt_hoten]),
                    ft.Row([dd_gioitinh, txt_ngaysinh]),
                    ft.Row([dd_dantoc, dd_tongiao]),
                    ft.Row([txt_bhyt, txt_sdt]),
                    ft.Row([txt_nghe, dd_trinhdo]), 
                    ft.Divider(),
                    ft.Text("Địa chỉ cư trú", weight="bold", color="blue"),
                    ft.Row([dd_tinh, dd_phuong]),
                    ft.Row([dd_khom, txt_chitiet]), 
                    ft.Divider(),
                    ft.Text("Thông tin khác", weight="bold", color="blue"),
                    ft.Row([ft.Container(group_chinhtri, expand=1), ft.Container(group_chinhsach, expand=1)])
                ], scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()),
                ft.ElevatedButton("Lưu Dữ Liệu", bgcolor=self.primary_color, color="white", on_click=save_data)
            ]
        )
        self.page.open(dlg)
        self.page.update()