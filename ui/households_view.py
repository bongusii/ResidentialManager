import flet as ft
from database.db_manager import db
from datetime import datetime

class HouseholdsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.primary_color = "blue700"
        self.bg_color = "bluegrey50"
        self.card_bg = "white"

        self.total_households_text = ft.Text("0", size=30, weight="bold", color=self.primary_color)
        
        self.all_data = []

        # Khởi tạo bảng dữ liệu
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Mã Hộ Khẩu", weight="bold")),
                ft.DataColumn(ft.Text("Chủ Hộ", weight="bold")),
                ft.DataColumn(ft.Text("Địa Chỉ", weight="bold")),
                ft.DataColumn(ft.Text("Ngày Lập", weight="bold")),
                ft.DataColumn(ft.Text("Thành Viên", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Hành động", weight="bold")),
            ],
            rows=[],
            heading_row_color="blue50",
            heading_row_height=60,
            data_row_min_height=60,
            column_spacing=40,
            border=ft.border.all(1, "grey200"),
            border_radius=10,
            width=1250,
        )
        self.load_data()

    # --- AUTHENTICATION (BẢO MẬT) ---
    def show_auth_dialog(self, on_success_callback):
        txt_pass = ft.TextField(label="Mật khẩu Admin", password=True, autofocus=True)
        lbl_error = ft.Text("", color="red", size=12)

        def check(e):
            if db.verify_admin(txt_pass.value): 
                dlg.open = False
                self.page.update()
                on_success_callback()
            else: 
                txt_pass.error_text = "Sai mật khẩu!"
                txt_pass.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("Xác thực bảo mật"), 
            content=ft.Column([
                ft.Text("Vui lòng nhập mật khẩu để tiếp tục:", size=14),
                txt_pass,
                lbl_error
            ], tight=True, width=300),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()), 
                ft.ElevatedButton("OK", on_click=check)
            ]
        )
        self.page.open(dlg)
        self.page.update()

    # --- GIAO DIỆN CHÍNH ---
    def get_content(self):
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Quản Lý Hộ Khẩu", size=28, weight="bold", color="black87"),
                    ft.Text("Danh sách hộ gia đình & Thành viên", size=14, color="grey500"),
                ]),
                ft.Container(
                    content=ft.Row([
                        ft.Icon("home", size=40, color="blue200"),
                        ft.Column([
                            ft.Text("Tổng số hộ", size=12, color="grey600"), 
                            self.total_households_text
                        ], spacing=0)
                    ]),
                    padding=15, border=ft.border.all(1, "grey200"), border_radius=12, bgcolor=self.card_bg
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            margin=ft.margin.only(bottom=20)
        )

        toolbar = ft.Row([
            ft.TextField(
                hint_text="Tìm theo Mã HK hoặc Tên chủ hộ...", prefix_icon="search", 
                border_radius=10, height=45, content_padding=10, 
                expand=True, bgcolor=self.card_bg, border_color="transparent",
                on_change=self.filter_data
            ),
            ft.ElevatedButton(
                "Tạo Hộ Khẩu Mới", icon="add_home", 
                style=ft.ButtonStyle(color="white", bgcolor=self.primary_color, padding=15, shape=ft.RoundedRectangleBorder(radius=10)), 
                on_click=lambda e: self.open_create_dialog()
            )
        ])

        table_card = ft.Container(
            content=ft.Column([
                toolbar,
                ft.Divider(height=20, color="transparent"),
                ft.Column([
                    ft.Row([self.data_table], scroll=ft.ScrollMode.ALWAYS)
                ], scroll=ft.ScrollMode.AUTO, expand=True)
            ], expand=True),
            padding=25, bgcolor=self.card_bg, border_radius=15, shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color="#1A000000"), expand=True
        )

        return ft.Container(content=ft.Column([header, table_card], spacing=0, expand=True), padding=30, bgcolor=self.bg_color, expand=True)

    # --- TÍNH NĂNG: ĐỒNG BỘ ĐỊA CHỈ ---
    def sync_address(self, ma_hk, cccd_chu_ho, current_hk_addr):
        if not cccd_chu_ho:
            self.page.snack_bar = ft.SnackBar(ft.Text("⚠️ Hộ này chưa có chủ hộ!"), bgcolor="orange")
            self.page.snack_bar.open = True; self.page.update(); return

        res = db.get_resident_by_cccd(cccd_chu_ho)
        if not res:
            self.page.snack_bar = ft.SnackBar(ft.Text("❌ Không tìm thấy dữ liệu chủ hộ!"), bgcolor="red")
            self.page.snack_bar.open = True; self.page.update(); return
        
        r = res[0]
        # 12:ChiTiet, 11:Khom, 10:Phuong, 9:Tinh
        addr_parts = [r[12], r[11], r[10], r[9]]
        new_addr = ", ".join([str(x) for x in addr_parts if x])

        if new_addr != current_hk_addr:
            def do_update():
                # Gọi hàm create_household với merge=True (đã sửa ở db_manager)
                # Chỉ gửi địa chỉ cần update
                db.create_household(ma_hk, {'dia_chi': new_addr}) 
                
                self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ Đã cập nhật địa chỉ mới cho hộ {ma_hk}"), bgcolor="green")
                self.page.snack_bar.open = True
                self.load_data()
                self.page.update()
            
            do_update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("✅ Địa chỉ đã khớp, không cần cập nhật."), bgcolor="blue")
            self.page.snack_bar.open = True; self.page.update()

    # --- POPUP XEM CHI TIẾT HỒ SƠ CÁ NHÂN (Tái sử dụng logic hiển thị) ---
    def open_resident_detail(self, cccd):
        data = db.get_resident_by_cccd(cccd)
        if not data: return
        r = data[0]

        addr_parts = [r[12], r[11], r[10], r[9]]
        full_addr = ", ".join([str(x) for x in addr_parts if x]) or "Chưa cập nhật"

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
                
                ft.Row([info_box("wc", "Giới tính", r[2]), info_box("cake", "Ngày sinh", r[3]), info_box("school", "Trình độ", r[14])]),
                ft.Container(height=5),
                ft.Row([info_box("phone", "SĐT", r[6]), info_box("work", "Nghề", r[5]), info_box("home", "Hộ khẩu", r[15], "orange")]),
                ft.Container(height=5),
                ft.Text("Thông tin Xã hội", size=12, weight="bold", color="blue"),
                ft.Row([info_box("medical_services", "BHYT", r[4])]), 
                ft.Container(height=5),
                info_box("groups", "Chính trị - XH", r[7], "blue", True), 
                ft.Container(height=5),
                info_box("policy", "Chế độ Chính sách", r[8], "red", True),
                ft.Divider(height=30),
                ft.Container(content=ft.Row([ft.Icon("location_on", size=24, color="red400"), ft.Column([ft.Text("Địa chỉ thường trú", size=11, color="red800"), ft.Text(full_addr, size=15, weight="bold", color="black87", no_wrap=False)], spacing=2, expand=True)]), padding=15, bgcolor="red50", border_radius=8)
            ], scroll=ft.ScrollMode.AUTO, spacing=5)
        )
        dlg = ft.AlertDialog(
            title=ft.Text("Hồ Sơ Cư Dân", weight="bold"), 
            content=content, 
            actions=[ft.TextButton("Đóng", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update())]
        )
        self.page.open(dlg)
        self.page.update()

    # --- POPUP SỔ HỘ KHẨU ---
    def open_detail_dialog(self, ma_hk):
        hks = db.get_all_households()
        target_hk = next((h for h in hks if h[0] == ma_hk), None)
        if not target_hk: return

        # Lấy địa chỉ Full từ chủ hộ
        cccd_chu_ho = target_hk[5]
        full_address = target_hk[2]
        if cccd_chu_ho:
            res = db.get_resident_by_cccd(cccd_chu_ho)
            if res:
                r = res[0]
                addr_parts = [r[12], r[11], r[10], r[9]]
                full_address = ", ".join([str(x) for x in addr_parts if x])

        members = db.get_members_of_household(ma_hk)
        
        members_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=300)
        
        for mem in members:
            # mem: (cccd, ten, is_chu_ho, ngaysinh, quanhe)
            is_head = mem[2] == 1
            quan_he = "Chủ hộ" if is_head else (mem[4] if mem[4] else "Thành viên")
            
            card = ft.Container(
                content=ft.Row([
                    ft.Icon("stars" if is_head else "person", size=20, color="orange" if is_head else "blue"),
                    ft.Column([
                        ft.Row([
                            ft.Text(mem[1], weight="bold", size=14), 
                            ft.Container(
                                content=ft.Text(quan_he, size=10, color="white", weight="bold"), 
                                bgcolor="orange" if is_head else "blue400", 
                                padding=ft.padding.symmetric(horizontal=8, vertical=2), 
                                border_radius=10
                            )
                        ], spacing=5),
                        ft.Text(f"CCCD: {mem[0]} | Sinh: {mem[3]}", size=12, color="grey")
                    ], spacing=2, expand=True),
                    
                    ft.IconButton(icon="visibility", icon_color="green", tooltip="Xem hồ sơ", on_click=lambda e, c=mem[0]: self.open_resident_detail(c))
                ]),
                padding=10, bgcolor="orange50" if is_head else "grey50", border_radius=8, border=ft.border.all(1, "orange200" if is_head else "grey200")
            )
            members_list.controls.append(card)

        content = ft.Container(
            width=600, padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Icon("menu_book", size=40, color="blue900"), 
                    ft.Column([
                        ft.Text(f"SỔ HỘ KHẨU SỐ: {target_hk[0]}", size=20, weight="bold", color="blue900"), 
                        ft.Text(f"Ngày lập: {target_hk[3]}", size=12, color="grey")
                    ], spacing=0)
                ]),
                
                ft.Divider(),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("THÔNG TIN CHUNG", size=12, weight="bold", color="blue"), 
                        ft.Row([ft.Icon("person", size=16, color="grey"), ft.Text(f"Chủ hộ: {target_hk[1]}", weight="bold")]), 
                        ft.Row([
                            ft.Icon("location_on", size=16, color="grey"), 
                            ft.Text(f"Địa chỉ: {full_address}", expand=True, no_wrap=False)
                        ], vertical_alignment=ft.CrossAxisAlignment.START)
                    ], spacing=5), 
                    padding=15, bgcolor="blue50", border_radius=8
                ),
                
                ft.Container(height=10),
                ft.Text(f"DANH SÁCH THÀNH VIÊN ({len(members)})", size=12, weight="bold", color="blue"),
                members_list
            ])
        )
        
        dlg = ft.AlertDialog(
            content=content, 
            actions=[
                ft.TextButton("Đóng", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()), 
                ft.ElevatedButton("Quản lý", icon="people", on_click=lambda e: self.open_members_dialog(ma_hk, None))
            ]
        )
        self.page.open(dlg)
        self.page.update()

    def load_data(self):
        rows = db.get_all_households()
        self.data_table.rows.clear()
        self.total_households_text.value = str(len(rows))
        self.all_data = db.get_all_households()
        self.render_table(self.all_data)

        for r in rows:
            # r: (ma_hk, ten_chu_ho, dia_chi, ngay_lap, count_mem, cccd_chu_ho)
            badge_bg = "blue50" if r[4] > 0 else "grey100"
            badge_border = "blue200" if r[4] > 0 else "grey300"
            text_color = "blue800" if r[4] > 0 else "grey500"

            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(r[0], weight="bold", color=self.primary_color)), 
                        ft.DataCell(ft.Text(r[1])), 
                        ft.DataCell(ft.Text(r[2])), 
                        ft.DataCell(ft.Text(r[3])),
                        ft.DataCell(ft.Container(content=ft.Text(str(r[4]), size=12, weight="bold", color=text_color), bgcolor=badge_bg, border=ft.border.all(1, badge_border), width=30, height=30, border_radius=15, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Row([
                            ft.IconButton(icon="visibility", icon_color="green", tooltip="Xem Sổ", on_click=lambda e, m=r[0]: self.open_detail_dialog(m)),
                            
                            # Nút Đồng bộ
                            ft.IconButton(icon="sync", icon_color="orange", tooltip="Đồng bộ ĐC", on_click=lambda e, m=r[0], c=r[5], a=r[2]: self.sync_address(m, c, a)),
                            
                            ft.IconButton(icon="people", icon_color="blue", tooltip="Thành viên", on_click=lambda e, m=r[0], c=r[5]: self.open_members_dialog(m, c)),
                            ft.IconButton(icon="delete", icon_color="red", tooltip="Xóa hộ khẩu", on_click=lambda e, m=r[0]: self.delete_household(m))
                        ]))
                    ]
                )
            )
        try: self.page.update()
        except: pass

    def filter_data(self, e):
        search_term = e.control.value.lower()
        if not search_term:
            self.render_table(self.all_data)
        else:
            # Lọc theo Mã HK (index 0) hoặc Tên Chủ Hộ (index 1)
            filtered = [
                row for row in self.all_data 
                if search_term in str(row[0]).lower() or search_term in str(row[1]).lower()
            ]
            self.render_table(filtered)

    def render_table(self, data_list):
        self.data_table.rows.clear()
        self.total_households_text.value = str(len(data_list))

        for r in data_list:
            # r: (ma_hk, ten_chu_ho, dia_chi, ngay_lap, count_mem, cccd_chu_ho)
            badge_bg = "blue50" if r[4] > 0 else "grey100"
            badge_border = "blue200" if r[4] > 0 else "grey300"
            text_color = "blue800" if r[4] > 0 else "grey500"

            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(r[0], weight="bold", color=self.primary_color)), 
                        ft.DataCell(ft.Text(r[1], weight="w500")), 
                        ft.DataCell(ft.Text(r[2], size=13)), 
                        ft.DataCell(ft.Text(r[3])),
                        ft.DataCell(ft.Container(content=ft.Text(str(r[4]), size=12, weight="bold", color=text_color), bgcolor=badge_bg, border=ft.border.all(1, badge_border), width=30, height=30, border_radius=15, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Row([
                            ft.IconButton(icon="visibility", icon_color="green", tooltip="Xem Sổ", on_click=lambda e, m=r[0]: self.open_detail_dialog(m)),
                            ft.IconButton(icon="sync", icon_color="orange", tooltip="Đồng bộ ĐC", on_click=lambda e, m=r[0], c=r[5], a=r[2]: self.sync_address(m, c, a)),
                            ft.IconButton(icon="people", icon_color="blue", tooltip="Thành viên", on_click=lambda e, m=r[0], c=r[5]: self.open_members_dialog(m, c)),
                            ft.IconButton(icon="delete", icon_color="red", tooltip="Xóa", on_click=lambda e, m=r[0]: self.delete_household(m))
                        ]))
                    ]
                )
            )
        try: self.page.update()
        except: pass

    # --- DIALOG TẠO MỚI HỘ KHẨU ---
    def open_create_dialog(self):
        txt_ma = ft.TextField(label="Mã HK", border_radius=8)
        txt_dc = ft.TextField(label="Địa chỉ (Tự động lấy từ Chủ hộ)", border_radius=8, read_only=True, disabled=True)
        txt_cccd = ft.TextField(label="CCCD Chủ hộ", border_radius=8, on_change=lambda e: check_cccd_name(e))
        lbl_name_check = ft.Text("Nhập CCCD để kiểm tra...", size=12, italic=True, color="grey")

        def check_cccd_name(e):
            if len(txt_cccd.value) > 5:
                res = db.get_resident_by_cccd(txt_cccd.value)
                if res:
                    r = res[0]
                    # Mapping: 12:ChiTiet, 11:Khom, 10:Phuong, 9:Tinh
                    addr_parts = [r[12], r[11], r[10], r[9]]
                    auto_addr = ", ".join([str(x) for x in addr_parts if x])
                    txt_dc.value = auto_addr # Tự điền địa chỉ
                    txt_dc.update()

                    if r[15]: 
                        lbl_name_check.value = f"⚠️ {r[1]} đã thuộc hộ {r[15]}!"
                        lbl_name_check.color = "orange"
                    else: 
                        lbl_name_check.value = f"✅ Hợp lệ: {r[1]}"
                        lbl_name_check.color = "green"
                else: 
                    lbl_name_check.value = "❌ Không tìm thấy CCCD!"
                    lbl_name_check.color = "red"
                    txt_dc.value = ""
                    txt_dc.update()
            else: 
                lbl_name_check.value = "..."
            
            lbl_name_check.update()

        def save_household():
            if not txt_ma.value or not txt_cccd.value: return
            
            def execute_save():
                try:
                    today = datetime.now().strftime("%d/%m/%Y")
                    # Địa chỉ lấy từ txt_dc (đã được tự động điền)
                    db.create_household(txt_ma.value, {'dia_chi': txt_dc.value, 'cccd_chu_ho': txt_cccd.value, 'ngay_lap': today})
                    dlg.open = False
                    self.load_data()
                    self.page.update()
                except Exception as ex:
                    self.page.open(ft.AlertDialog(title=ft.Text("Lỗi"), content=ft.Text(f"Lỗi: {ex}"), open=True))
                    self.page.update()

            self.show_auth_dialog(execute_save)

        dlg = ft.AlertDialog(
            title=ft.Text("Tạo Hộ Khẩu Mới"),
            content=ft.Container(
                width=400, height=300,
                content=ft.Column([txt_ma, txt_cccd, lbl_name_check, txt_dc])
            ),
            actions=[
                ft.ElevatedButton("Tạo", on_click=lambda e: save_household()),
                ft.TextButton("Hủy", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update())
            ]
        )
        self.page.open(dlg)
        self.page.update()

    # --- QUẢN LÝ THÀNH VIÊN (THÊM/BỚT/SỬA) ---
    def open_members_dialog(self, ma_hk, cccd_chu_ho):
        lv_members = ft.ListView(expand=1, spacing=10, padding=20)
        txt_add_cccd = ft.TextField(label="Nhập CCCD thành viên", text_size=14, expand=2)
        dd_add_quanhe = ft.Dropdown(label="Quan hệ", options=[ft.dropdown.Option(x) for x in ["Vợ","Chồng","Con","Con dâu","Con rể","Bố","Mẹ","Ông","Bà","Cháu","Anh/Em","Ở nhờ","Khác"]], text_size=14, expand=1)
        lbl_check_status = ft.Text("...", size=12, italic=True, color="grey")
        lbl_add_msg = ft.Text("", size=12, weight="bold")

        def on_cccd_change(e):
            cccd = txt_add_cccd.value.strip()
            if len(cccd) < 9: lbl_check_status.value = "..."; lbl_check_status.color = "grey"
            else:
                res = db.get_resident_by_cccd(cccd)
                if res:
                    ho_ten = res[0][1]; current_hk = res[0][15]
                    if current_hk == ma_hk: lbl_check_status.value = f"⚠️ {ho_ten} đã có trong hộ này!"; lbl_check_status.color = "orange"
                    elif current_hk: lbl_check_status.value = f"⚠️ {ho_ten} đang thuộc hộ {current_hk}"; lbl_check_status.color = "orange"
                    else: lbl_check_status.value = f"✅ Tìm thấy: {ho_ten}"; lbl_check_status.color = "green"
                else: lbl_check_status.value = "❌ Không tìm thấy!"; lbl_check_status.color = "red"
            lbl_check_status.update()

        txt_add_cccd.on_change = on_cccd_change

        # HÀM SỬA QUAN HỆ (MỚI)
        def open_edit_rel_dialog(cccd, current_rel, name):
            dd_edit_rel = ft.Dropdown(label="Quan hệ mới", value=current_rel, options=[ft.dropdown.Option(x) for x in ["Vợ","Chồng","Con","Con dâu","Con rể","Bố","Mẹ","Ông","Bà","Cháu","Anh/Em","Ở nhờ","Khác"]])
            
            def save_rel(e):
                self.show_auth_dialog(lambda: (
                    db.update_member_relationship(cccd, dd_edit_rel.value), 
                    setattr(dlg_edit, 'open', False), 
                    load_members(), 
                    self.page.update()
                ))
            
            dlg_edit = ft.AlertDialog(
                title=ft.Text(f"Sửa quan hệ: {name}"),
                content=ft.Container(height=100, content=dd_edit_rel),
                actions=[
                    ft.TextButton("Hủy", on_click=lambda e: setattr(dlg_edit, 'open', False) or self.page.update()), 
                    ft.ElevatedButton("Lưu", on_click=save_rel)
                ]
            )
            self.page.open(dlg_edit); self.page.update()

        def load_members():
            lv_members.controls.clear()
            mems = db.get_members_of_household(ma_hk)
            for m in mems:
                is_head = m[2] == 1
                quan_he = "Chủ hộ" if is_head else (m[4] if m[4] else "Thành viên")
                
                icon = ft.Icon("stars", color="orange") if is_head else ft.Icon("person", color="blue")
                
                info_col = ft.Column([
                    ft.Row([
                        ft.Text(m[1], weight="bold", size=14),
                        ft.Container(content=ft.Text(quan_he, size=10, color="white", weight="bold"), bgcolor="orange" if is_head else "blue400", padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=10)
                    ]),
                    ft.Text(f"CCCD: {m[0]} | Sinh: {m[3]}", size=12, color="grey")
                ], spacing=2, expand=True)
                
                # Nút hành động
                actions_row = ft.Row(spacing=0)
                actions_row.controls.append(ft.IconButton(icon="visibility", icon_color="green", tooltip="Xem hồ sơ", icon_size=20, on_click=lambda e, c=m[0]: self.open_resident_detail(c)))

                if not is_head:
                    actions_row.controls.append(ft.IconButton(icon="edit", icon_color="blue", tooltip="Sửa quan hệ", icon_size=20, on_click=lambda e, c=m[0], r=quan_he, n=m[1]: open_edit_rel_dialog(c, r, n)))
                    actions_row.controls.append(ft.IconButton(icon="remove_circle_outline", icon_color="red", tooltip="Tách khẩu", icon_size=20, on_click=lambda e, c=m[0]: self.show_auth_dialog(lambda: (db.remove_member_from_household(c), load_members(), self.load_data()))))

                lv_members.controls.append(ft.Container(content=ft.Row([icon, info_col, actions_row]), padding=10, border=ft.border.all(1, "grey200"), border_radius=8, bgcolor="white"))
            try: lv_members.update()
            except: pass

        def add_member(e):
            cccd = txt_add_cccd.value.strip(); quan_he = dd_add_quanhe.value
            if not cccd: return
            if not quan_he: lbl_add_msg.value = "Chọn quan hệ!"; lbl_add_msg.color="red"; lbl_add_msg.update(); return
            
            def execute_add():
                db.add_member_to_household(ma_hk, cccd, quan_he)
                lbl_add_msg.value = "Đã thêm thành công!"
                lbl_add_msg.color = "green"
                txt_add_cccd.value = ""; dd_add_quanhe.value = None
                load_members()
                self.load_data()
                self.page.update()

            self.show_auth_dialog(execute_add)
            lbl_add_msg.update()

        load_members()
        dlg = ft.AlertDialog(
            title=ft.Text(f"Quản lý Hộ: {ma_hk}"),
            content=ft.Container(
                width=600, height=500,
                content=ft.Column([
                    ft.Text("Thêm thành viên mới:", weight="bold", color="blue"),
                    ft.Row([txt_add_cccd, dd_add_quanhe, ft.IconButton(icon="person_add", icon_color="green", on_click=add_member)]),
                    lbl_check_status, lbl_add_msg,
                    ft.Divider(),
                    ft.Text("Danh sách thành viên hiện tại:", weight="bold"),
                    lv_members
                ])
            ),
            actions=[ft.TextButton("Đóng", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update())]
        )
        self.page.open(dlg)
        self.page.update()

    # --- XÓA HỘ KHẨU ---
    def delete_household(self, ma_hk):
        def confirm(e):
            def execute_delete():
                db.delete_household(ma_hk)
                confirm_dlg.open = False
                self.load_data()
                self.page.update()
            self.show_auth_dialog(execute_delete)

        confirm_dlg = ft.AlertDialog(
            title=ft.Text("Xác nhận xóa Hộ khẩu"),
            content=ft.Text(f"Bạn có chắc muốn xóa hộ {ma_hk}?\nTất cả thành viên sẽ bị tách khỏi hộ."),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: setattr(confirm_dlg, 'open', False) or self.page.update()),
                ft.TextButton("Xóa", on_click=confirm, style=ft.ButtonStyle(color="red"))
            ]
        )
        self.page.open(confirm_dlg)
        self.page.update()