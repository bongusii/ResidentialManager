import flet as ft
import pandas as pd
import os
import time
from datetime import datetime
from database.db_manager import db

class ImportView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.primary_color = "blue700"
        self.bg_color = "bluegrey50"
        self.card_bg = "white"
        
        # Biến cờ để kiểm soát việc ghi đè hàng loạt (Cho import Cư dân)
        self.overwrite_all_mode = False 

        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)
        self.page.update()
        
        self.current_import_type = None 
        
        # UI Components cho Tiến độ & Log
        self.pb = ft.ProgressBar(width=400, color="blue", bgcolor="#eeeeee", value=0, visible=False)
        self.pb_label = ft.Text("", size=12, color="blue", visible=False, italic=True)
        self.log_view = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=2)
        
        self.render()

    def get_content(self):
        return self.main_container

    def render(self):
        # 1. Header
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Nhập Dữ Liệu Hệ Thống", size=28, weight="bold", color="black87"),
                    ft.Text("Import dữ liệu hàng loạt từ file Excel (.xlsx)", size=14, color="grey500"),
                ]),
                ft.Icon("upload_file", size=50, color="blue200"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            margin=ft.margin.only(bottom=20)
        )

        # 2. Card Công cụ
        tools_card = ft.Container(
            content=ft.Column([
                ft.Text("Công cụ nhập liệu", size=16, weight="bold", color="blue900"),
                ft.Divider(),
                ft.Row([
                    # NHÓM 1: CƯ DÂN CƠ BẢN
                    self.build_tool_item("Cư Dân", "download", "Tải mẫu", "green", lambda e: self.generate_template("resident")),
                    self.build_tool_item("Cư Dân", "upload", "Import Cư dân", "blue", lambda e: self.pick_file("resident")),
                    
                    ft.VerticalDivider(width=10),
                    
                    # NHÓM 2: AUTO HỘ KHẨU (TÍNH NĂNG CAO CẤP)
                    self.build_tool_item("Auto Hộ", "auto_awesome", "Import Auto", "purple", lambda e: self.pick_file("resident_auto")),

                    ft.VerticalDivider(width=10),
                    
                    # NHÓM 3: HỘ KHẨU THỦ CÔNG
                    self.build_tool_item("Hộ Khẩu", "download", "Tải mẫu (+TV)", "orange", lambda e: self.generate_template("household")),
                    self.build_tool_item("Hộ Khẩu", "upload", "Import Hộ khẩu", "blue", lambda e: self.pick_file("household")),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
            ]),
            padding=20, bgcolor="white", border_radius=10,
            shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
        )

        # 3. Card Nhật ký
        logs_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Tiến độ & Nhật ký", size=16, weight="bold", color="blue900"),
                    ft.IconButton(icon="delete_outline", tooltip="Xóa log", on_click=lambda e: self.clear_logs())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Khu vực Progress Bar
                ft.Column([self.pb_label, self.pb], spacing=5),
                
                ft.Divider(),
                
                # Khu vực Log Console
                ft.Container(
                    content=self.log_view,
                    bgcolor="black", border_radius=5, padding=10, height=300
                )
            ]),
            padding=20, bgcolor="white", border_radius=10, margin=ft.margin.only(top=20),
            shadow=ft.BoxShadow(blur_radius=10, color="#1A000000"), expand=True
        )

        self.main_container = ft.Container(
            content=ft.Column([header, tools_card, logs_card], scroll=ft.ScrollMode.AUTO),
            padding=30, bgcolor=self.bg_color, expand=True
        )

    def build_tool_item(self, title, icon, btn_text, color, on_click):
        return ft.Column([
            ft.Text(title, weight="bold", color="grey700", size=12),
            ft.ElevatedButton(
                text=btn_text, icon=icon,
                style=ft.ButtonStyle(color="white", bgcolor=color, shape=ft.RoundedRectangleBorder(radius=8), padding=15),
                on_click=on_click
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def log(self, message, type="info"):
        colors = {"info": "white", "success": "greenaccent", "error": "redaccent", "warning": "orangeaccent"}
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.controls.append(
            ft.Text(f"[{timestamp}] {message}", color=colors.get(type, "white"), font_family="Consolas", size=12, selectable=True)
        )
        self.log_view.update()

    def clear_logs(self):
        self.log_view.controls.clear()
        self.log_view.update()

    def update_progress(self, current, total):
        percent = int((current / total) * 100) if total > 0 else 0
        self.pb.value = current / total if total > 0 else 0
        self.pb_label.value = f"Đang xử lý: {current}/{total} dòng ({percent}%)"
        self.pb.visible = True; self.pb_label.visible = True; self.page.update()

    def finish_progress(self):
        self.pb.value = 1; self.pb_label.value = "Hoàn tất!"; self.page.update()

    def generate_template(self, type):
        try:
            if type == "resident":
                df = pd.DataFrame(columns=[
                    "CCCD", "HoTen", "GioiTinh", "NgaySinh", "BHYT", "NgheNghiep", "SDT", 
                    "ChinhTri_XH", "ChinhSach", "TrinhDo", "DanToc", "TonGiao",
                    "TinhThanh", "PhuongXa", "KhomAp", "DiaChiChiTiet"
                ])
                filename = "Mau_Import_CuDan.xlsx"
            else:
                # Mẫu Hộ khẩu
                df = pd.DataFrame(columns=["MaHoKhau", "CCCD_ChuHo", "NgayLap", "CCCD_ThanhVien", "QuanHeVoiChuHo"])
                filename = "Mau_Import_HoKhau.xlsx"
            
            try:
                df.to_excel(filename, index=False)
                self.log(f"✅ Đã tạo file mẫu '{filename}' tại thư mục gốc!", "success")
                try: os.startfile(os.getcwd())
                except: pass
            except PermissionError:
                self.log(f"❌ Lỗi: File '{filename}' đang mở. Vui lòng đóng lại!", "error")
                self.page.open(ft.AlertDialog(title=ft.Text("Lỗi"), content=ft.Text(f"Vui lòng đóng file Excel '{filename}' trước khi tải lại!")))
                self.page.update()

        except Exception as e:
            self.log(f"❌ Lỗi tạo mẫu khác: {e}", "error")

    def pick_file(self, type):
        self.current_import_type = type
        self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["xlsx"])

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if not e.files: return
        file_path = e.files[0].path
        self.log(f"📂 Bắt đầu đọc file: {file_path}", "info")
        
        # Reset trạng thái
        self.overwrite_all_mode = False 
        self.pb.value = None; self.pb.visible = True; self.pb_label.value = "Đang đọc dữ liệu..."; self.pb_label.visible = True; self.page.update()
        
        try:
            df = pd.read_excel(file_path, dtype=str).fillna("")
            df.columns = [c.strip() for c in df.columns]
            
            if self.current_import_type == "resident":
                records = df.to_dict('records')
                # Gọi logic Queue Cư dân
                self.process_resident_queue(records, 0, 0, 0)
            
            elif self.current_import_type == "resident_auto":
                # Gọi logic Auto Hộ khẩu
                self.process_resident_auto_household(df)

            else:
                # Gọi logic Hộ khẩu thường
                self.process_import_household(df)
                
        except Exception as ex:
            self.log(f"❌ Lỗi đọc file: {ex}", "error"); self.pb.visible = False; self.pb_label.visible = False; self.page.update()

    def clean_cccd(self, value):
        s = str(value).strip()
        if s.lower() == 'nan' or not s: return ""
        if s.endswith(".0"): s = s[:-2]
        if s.isdigit() and len(s) < 12: s = s.zfill(12)
        return s

    # =========================================================================
    # [LOGIC 1] IMPORT CƯ DÂN (QUEUE + OVERWRITE ALL)
    # =========================================================================
    def process_resident_queue(self, records, index, success_count, error_count):
        if index >= len(records):
            self.finish_progress(); self.log(f"🏁 HOÀN TẤT! Thành công: {success_count}, Lỗi/Bỏ qua: {error_count}", "success"); return

        self.update_progress(index, len(records))
        row = records[index]
        cccd = self.clean_cccd(row.get('CCCD', ''))
        
        if not cccd:
            self.process_resident_queue(records, index + 1, success_count, error_count)
            return

        data = {
            'ho_ten': str(row.get('HoTen', '')).strip(), 'gioi_tinh': str(row.get('GioiTinh', '')).strip(),
            'ngay_sinh': str(row.get('NgaySinh', '')).strip(), 'bhyt': str(row.get('BHYT', '')).strip(),
            'nghe_nghiep': str(row.get('NgheNghiep', '')).strip(), 'sdt': str(row.get('SDT', '')).strip(),
            'chinh_tri_xh': str(row.get('ChinhTri_XH', '')).strip(), 'che_do_chinh_sach': str(row.get('ChinhSach', '')).strip(),
            'trinh_do': str(row.get('TrinhDo', '')).strip(), 'dan_toc': str(row.get('DanToc', '')).strip(), 'ton_giao': str(row.get('TonGiao', '')).strip(),
            'tinh_thanh': str(row.get('TinhThanh', '')).strip(), 'phuong_xa': str(row.get('PhuongXa', '')).strip(), 'khom_ap': str(row.get('KhomAp', '')).strip(), 'dia_chi_chi_tiet': str(row.get('DiaChiChiTiet', '')).strip(),
            'ma_ho_khau': '', 'is_chu_ho': False, 'quan_he_chu_ho': ''
        }

        # 1. Chế độ Ghi đè tất cả
        if self.overwrite_all_mode:
            try:
                db.upsert_resident(cccd, data)
                self.log(f"Dòng {index+2}: Tự động ghi đè {cccd}", "warning")
                self.process_resident_queue(records, index + 1, success_count + 1, error_count)
            except Exception as ex:
                self.log(f"Lỗi: {ex}", "error")
                self.process_resident_queue(records, index + 1, success_count, error_count + 1)
            return

        # 2. Kiểm tra trùng lặp
        check_exist = db.get_resident_by_cccd(cccd)
        
        if check_exist:
            def on_ov(e): dlg.open=False; self.page.update(); db.upsert_resident(cccd, data); self.log(f"Đã ghi đè {cccd}", "warning"); self.process_resident_queue(records, index + 1, success_count + 1, error_count)
            def on_skip(e): dlg.open=False; self.page.update(); self.log(f"Đã bỏ qua {cccd}", "info"); self.process_resident_queue(records, index + 1, success_count, error_count + 1)
            def on_all(e): self.overwrite_all_mode=True; on_ov(e)
            
            dlg = ft.AlertDialog(
                title=ft.Text("Phát hiện trùng lặp"),
                content=ft.Column([
                    ft.Text(f"CCCD: {cccd} đã tồn tại!"),
                    ft.Text(f"Tên cũ: {check_exist[0][1]}"),
                    ft.Text(f"Tên mới (Excel): {data['ho_ten']}", weight="bold"),
                ], tight=True),
                actions=[
                    ft.TextButton("Bỏ qua (Skip)", on_click=on_skip),
                    ft.ElevatedButton("Ghi đè", on_click=on_ov),
                    ft.ElevatedButton("Ghi đè TẤT CẢ", on_click=on_all, bgcolor="red", color="white"),
                ],
                modal=True
            )
            self.page.open(dlg); self.page.update()
        else:
            try:
                db.upsert_resident(cccd, data)
                self.process_resident_queue(records, index + 1, success_count + 1, error_count)
            except Exception as ex:
                self.log(f"Dòng {index+2} Lỗi: {ex}", "error")
                self.process_resident_queue(records, index + 1, success_count, error_count + 1)

    # =========================================================================
    # [LOGIC 2] CƯ DÂN -> AUTO HỘ KHẨU (TỰ ĐỘNG GOM NHÓM)
    # =========================================================================
    def process_resident_auto_household(self, df):
        self.log("🚀 Bắt đầu: Cư dân & Tự động tạo Hộ khẩu...", "info")
        grouped_data = {} 
        total_rows = len(df)
        self.update_progress(10, 100) 
        
        # 1. Gom nhóm theo địa chỉ
        for idx, row in df.iterrows():
            tinh = str(row.get('TinhThanh', '')).strip(); phuong = str(row.get('PhuongXa', '')).strip()
            khom = str(row.get('KhomAp', '')).strip(); chitiet = str(row.get('DiaChiChiTiet', '')).strip()
            
            # Key rác nếu không có địa chỉ
            if not tinh and not phuong and not khom and not chitiet: addr_key = f"UNKNOWN_{idx}"
            else: addr_key = f"{chitiet}|{khom}|{phuong}|{tinh}".lower()
            
            if addr_key not in grouped_data: grouped_data[addr_key] = []
            grouped_data[addr_key].append(row)

        self.log(f"🔍 Đã phân loại thành {len(grouped_data)} hộ gia đình tiềm năng.", "info")
        
        current_processed = 0; success_hk = 0; success_res = 0

        # 2. Xử lý từng nhóm
        for addr_key, rows in grouped_data.items():
            timestamp_code = int(time.time() * 1000) 
            auto_ma_hk = f"HK{str(timestamp_code)[-8:]}"
            
            # Người đầu tiên là Chủ hộ
            head_row = rows[0]
            head_cccd = self.clean_cccd(head_row.get('CCCD', ''))
            
            if not head_cccd: continue

            # Tạo địa chỉ hiển thị cho Hộ
            tinh = str(head_row.get('TinhThanh', '')).strip(); phuong = str(head_row.get('PhuongXa', '')).strip()
            khom = str(head_row.get('KhomAp', '')).strip(); chitiet = str(head_row.get('DiaChiChiTiet', '')).strip()
            display_addr = ", ".join([p for p in [chitiet, khom, phuong, tinh] if p])

            # Tạo Hộ Khẩu
            try:
                db.create_household(auto_ma_hk, {'dia_chi': display_addr, 'cccd_chu_ho': head_cccd, 'ngay_lap': datetime.now().strftime("%d/%m/%Y")})
                success_hk += 1
                self.log(f"🏠 Tạo hộ {auto_ma_hk} - Chủ hộ: {head_cccd}", "success")
            except Exception as e:
                self.log(f"❌ Lỗi tạo hộ {auto_ma_hk}: {e}", "error"); continue

            # Lưu Cư Dân & Gán vào Hộ
            for i, row in enumerate(rows):
                cccd = self.clean_cccd(row.get('CCCD', '')); 
                if not cccd: continue
                res_data = {
                    'ho_ten': str(row.get('HoTen', '')).strip(), 'gioi_tinh': str(row.get('GioiTinh', '')).strip(),
                    'ngay_sinh': str(row.get('NgaySinh', '')).strip(), 'bhyt': str(row.get('BHYT', '')).strip(),
                    'nghe_nghiep': str(row.get('NgheNghiep', '')).strip(), 'sdt': str(row.get('SDT', '')).strip(),
                    'chinh_tri_xh': str(row.get('ChinhTri_XH', '')).strip(), 'che_do_chinh_sach': str(row.get('ChinhSach', '')).strip(),
                    'trinh_do': str(row.get('TrinhDo', '')).strip(), 'dan_toc': str(row.get('DanToc', '')).strip(), 'ton_giao': str(row.get('TonGiao', '')).strip(),
                    'tinh_thanh': tinh, 'phuong_xa': phuong, 'khom_ap': khom, 'dia_chi_chi_tiet': chitiet,
                    # Logic gán hộ
                    'ma_ho_khau': auto_ma_hk, 'is_chu_ho': (i == 0), 'quan_he_chu_ho': 'Chủ hộ' if i == 0 else 'Thành viên'
                }
                try: db.upsert_resident(cccd, res_data); success_res += 1
                except Exception as ex: self.log(f"Lỗi thêm cư dân {cccd}: {ex}", "error")

            current_processed += len(rows); self.update_progress(current_processed, total_rows); time.sleep(0.1)

        self.finish_progress()
        self.log(f"🏁 HOÀN TẤT! Tạo được {success_hk} hộ khẩu, {success_res} cư dân.", "success")

    # =========================================================================
    # [LOGIC 3] IMPORT HỘ KHẨU (LOOP + AUTO ĐỊA CHỈ + THÀNH VIÊN)
    # =========================================================================
    def process_import_household(self, df):
        success = 0; error = 0; total = len(df); self.log("⏳ Đang xử lý dữ liệu Hộ khẩu...", "warning")

        for idx, row in df.iterrows():
            self.update_progress(idx + 1, total)
            try:
                ma_hk = str(row.get('MaHoKhau', '')).strip(); cccd_chu_ho = self.clean_cccd(row.get('CCCD_ChuHo', ''))
                if not ma_hk or not cccd_chu_ho: continue

                # Lấy thông tin Chủ hộ để TỰ ĐỘNG ĐIỀN ĐỊA CHỈ
                res_info = db.get_resident_by_cccd(cccd_chu_ho)
                if not res_info: self.log(f"Dòng {idx+2}: Lỗi - Chủ hộ {cccd_chu_ho} chưa có!", "error"); error += 1; continue
                r = res_info[0]; addr_parts = [r[12], r[11], r[10], r[9]]; auto_dia_chi = ", ".join([str(x) for x in addr_parts if x])

                ngay_lap = str(row.get('NgayLap', '')).strip() or datetime.now().strftime("%d/%m/%Y")
                data_hk = {'dia_chi': auto_dia_chi, 'cccd_chu_ho': cccd_chu_ho, 'ngay_lap': ngay_lap}
                db.create_household(ma_hk, data_hk)

                # Xử lý Thành viên đi kèm
                cccd_tv = self.clean_cccd(row.get('CCCD_ThanhVien', '')); quan_he = str(row.get('QuanHeVoiChuHo', '')).strip()
                if cccd_tv and cccd_tv != cccd_chu_ho:
                    if db.get_resident_by_cccd(cccd_tv): db.add_member_to_household(ma_hk, cccd_tv, quan_he); self.log(f" -> Thêm thành viên {cccd_tv}", "info")
                    else: self.log(f" -> Cảnh báo: Thành viên {cccd_tv} chưa có trong hệ thống!", "warning")
                success += 1
            except Exception as ex: self.log(f"Dòng {idx+2} Lỗi: {ex}", "error"); error += 1
        self.finish_progress(); self.log(f"🏁 HOÀN TẤT! Thành công: {success}, Lỗi: {error}", "success" if error == 0 else "warning")