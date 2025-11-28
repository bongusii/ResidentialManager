import flet as ft
from database.db_manager import db
from datetime import datetime

class StatsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.bg_color = "#F7F9FC" # Màu nền sáng xanh nhẹ
        
        # --- SỐ LIỆU ---
        self.total_pop = 0
        self.total_households = 0
        self.total_voters = 0
        self.male_count = 0
        self.female_count = 0
        self.age_groups = {"duoi_18": 0, "18_35": 0, "36_60": 0, "tren_60": 0}
        self.social_stats = {}
        self.policy_stats = {}

        # Main Content
        self.main_content = ft.Column(scroll=ft.ScrollMode.HIDDEN, expand=True, spacing=30)
        self.process_data()
        self.render()

    def get_content(self):
        return ft.Container(
            content=self.main_content,
            padding=30, bgcolor=self.bg_color, expand=True
        )

    def process_data(self):
        # Lấy dữ liệu từ Firestore (Tuple list)
        residents = db.get_all_residents()
        households = db.get_all_households()
        
        self.total_pop = len(residents)
        self.total_households = len(households)
        current_year = datetime.now().year

        for r in residents:
            # r[2]: GioiTinh, r[3]: NgaySinh, r[7]: ChinhTri, r[8]: ChinhSach
            ngay_sinh_str = r[3]
            gioi_tinh = r[2]
            chinhtri = r[7]
            chinhsach = r[8]

            if gioi_tinh == "Nam": self.male_count += 1
            elif gioi_tinh == "Nữ": self.female_count += 1
            
            age = 0
            try:
                if "/" in str(ngay_sinh_str):
                    parts = str(ngay_sinh_str).split("/")
                    born_year = int(parts[-1])
                    age = current_year - born_year
            except: age = 0

            if age >= 18: self.total_voters += 1
            
            if age < 18: self.age_groups["duoi_18"] += 1
            elif 18 <= age <= 35: self.age_groups["18_35"] += 1
            elif 36 <= age <= 60: self.age_groups["36_60"] += 1
            else: self.age_groups["tren_60"] += 1

            if chinhtri:
                for item in chinhtri.split(","):
                    if item.strip(): self.social_stats[item.strip()] = self.social_stats.get(item.strip(), 0) + 1
            if chinhsach:
                for item in chinhsach.split(","):
                    if item.strip(): self.policy_stats[item.strip()] = self.policy_stats.get(item.strip(), 0) + 1

    def render(self):
        # 1. Header
        header = ft.Column([
            ft.Text("Tổng quan số liệu", size=24, weight="bold", color="#2D3748"),
            ft.Text("Cập nhật thời gian thực từ hệ thống", size=14, color="#718096"),
        ], spacing=2)

        # 2. Summary Cards
        summary_row = ft.ResponsiveRow([
            ft.Column([self.build_stat_card("Tổng Dân Số", str(self.total_pop), "people", "blue")], col={"sm": 6, "md": 3}),
            ft.Column([self.build_stat_card("Hộ Khẩu", str(self.total_households), "home", "orange")], col={"sm": 6, "md": 3}),
            ft.Column([self.build_stat_card("Cử Tri (18+)", str(self.total_voters), "how_to_vote", "green")], col={"sm": 6, "md": 3}),
            ft.Column([self.build_stat_card("Nam / Nữ", f"{self.male_count} / {self.female_count}", "wc", "purple")], col={"sm": 6, "md": 3}),
        ])

        # 3. Charts Area
        charts_row = ft.ResponsiveRow([
            # Pie Chart
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Tỷ lệ Cử tri", weight="bold", size=16, color="#4A5568"),
                        ft.Divider(color="transparent", height=20),
                        ft.PieChart(
                            sections=[
                                ft.PieChartSection(self.age_groups["duoi_18"], title="", color="red200", radius=25),
                                ft.PieChartSection(self.total_voters, title="", color="green400", radius=30),
                            ],
                            sections_space=2,
                            center_space_radius=40,
                            height=180
                        ),
                        ft.Divider(color="transparent", height=20),
                        ft.Row([
                            self.legend_item("green400", "Đủ tuổi bầu cử"),
                            self.legend_item("red200", "Dưới 18 tuổi")
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor="white", padding=30, border_radius=16,
                    shadow=ft.BoxShadow(blur_radius=20, color="#0D000000"), # Sửa lỗi màu
                    height=380 # Cố định chiều cao
                )
            ], col={"md": 4}),
            
            # Bar Chart
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Phân bố nhóm tuổi", weight="bold", size=16, color="#4A5568"),
                        ft.Divider(color="transparent", height=30),
                        ft.BarChart(
                            bar_groups=[
                                ft.BarChartGroup(x=0, bar_rods=[ft.BarChartRod(from_y=0, to_y=self.age_groups["duoi_18"], width=40, color="red200", tooltip="Dưới 18", border_radius=5)]),
                                ft.BarChartGroup(x=1, bar_rods=[ft.BarChartRod(from_y=0, to_y=self.age_groups["18_35"], width=40, color="blue300", tooltip="18-35 Tuổi", border_radius=5)]),
                                ft.BarChartGroup(x=2, bar_rods=[ft.BarChartRod(from_y=0, to_y=self.age_groups["36_60"], width=40, color="orange300", tooltip="36-60 Tuổi", border_radius=5)]),
                                ft.BarChartGroup(x=3, bar_rods=[ft.BarChartRod(from_y=0, to_y=self.age_groups["tren_60"], width=40, color="grey400", tooltip="Trên 60", border_radius=5)]),
                            ],
                            border=ft.border.all(0, "transparent"),
                            left_axis=ft.ChartAxis(labels_size=30, title=ft.Text("Người", size=10)),
                            
                            # SỬA LỖI: Thêm labels_size để không bị cắt chữ
                            bottom_axis=ft.ChartAxis(
                                labels_size=40, 
                                labels=[
                                    ft.ChartAxisLabel(value=0, label=ft.Container(ft.Text("< 18", size=12), padding=5)),
                                    ft.ChartAxisLabel(value=1, label=ft.Container(ft.Text("18-35", size=12), padding=5)),
                                    ft.ChartAxisLabel(value=2, label=ft.Container(ft.Text("36-60", size=12), padding=5)),
                                    ft.ChartAxisLabel(value=3, label=ft.Container(ft.Text("> 60", size=12), padding=5)),
                                ],
                            ),
                            height=180,
                            min_y=0,
                            interactive=True,
                        )
                    ]),
                    bgcolor="white", padding=30, border_radius=16,
                    shadow=ft.BoxShadow(blur_radius=20, color="#0D000000"),
                    height=380 # Cố định chiều cao cho bằng bên trái
                )
            ], col={"md": 8})
        ])

        # 4. Details Lists
        details_row = ft.ResponsiveRow([
            ft.Column([self.build_list_stat("Tổ chức Chính trị - Xã hội", self.social_stats, "blue")], col={"md": 6}),
            ft.Column([self.build_list_stat("Đối tượng Chính sách", self.policy_stats, "orange")], col={"md": 6}),
        ])

        self.main_content.controls = [header, summary_row, charts_row, details_row]

    # --- HELPER WIDGETS ---
    def build_stat_card(self, title, value, icon, color):
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(title, size=13, color="#A0AEC0", weight="w500"),
                    ft.Text(value, size=26, weight="bold", color="#2D3748")
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Icon(icon, color=f"{color}500", size=28),
                    padding=12, 
                    bgcolor=f"{color}50", 
                    border_radius=12
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=20, bgcolor="white", border_radius=16,
            shadow=ft.BoxShadow(blur_radius=15, color="#0D000000")
        )

    def legend_item(self, color, text):
        return ft.Row([
            ft.Container(width=12, height=12, bgcolor=color, border_radius=4),
            ft.Text(text, size=12, color="#718096")
        ], spacing=5)

    def build_list_stat(self, title, data_dict, color_theme):
        items = []
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        
        for key, val in sorted_data:
            percent = val / self.total_pop if self.total_pop > 0 else 0
            items.append(
                ft.Column([
                    ft.Row([
                        ft.Text(key, size=13, color="#4A5568", expand=1),
                        ft.Text(str(val), size=13, weight="bold", color="#2D3748")
                    ]),
                    ft.ProgressBar(value=percent, color=f"{color_theme}400", bgcolor="#EDF2F7", height=6, border_radius=3)
                ], spacing=5)
            )
        
        if not items:
            items.append(ft.Container(content=ft.Text("Chưa có dữ liệu", size=13, color="#A0AEC0", italic=True), padding=20, alignment=ft.alignment.center))

        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=16, weight="bold", color="#2D3748"),
                ft.Divider(color="transparent", height=10),
                ft.Column(items, spacing=15)
            ]),
            padding=30, bgcolor="white", border_radius=16,
            shadow=ft.BoxShadow(blur_radius=20, color="#0D000000")
        )