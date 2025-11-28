# 🛡️ Hệ thống Quản lý Dân cư - The Sentinels

> **Giải pháp phần mềm quản lý dân cư hiện đại, kết nối CSDL đám mây (Cloud Firestore), hỗ trợ nhập liệu thông minh và báo cáo tự động.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Flet](https://img.shields.io/badge/Flet-UI-purple?style=for-the-badge)
![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange?style=for-the-badge&logo=firebase)
![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=for-the-badge&logo=pandas)

## 📖 Giới thiệu

**The Sentinels Residential Manager** là ứng dụng Desktop được xây dựng bằng Python và Flet, nhằm số hóa quy trình quản lý nhân khẩu tại địa phương. Ứng dụng thay thế phương pháp quản lý sổ sách thủ công bằng hệ thống cơ sở dữ liệu tập trung, bảo mật và có khả năng đồng bộ hóa dữ liệu theo thời gian thực.

## ✨ Tính năng Nổi bật

### 1. 👥 Quản lý Cư dân (Residents)
* **Hồ sơ toàn diện:** Quản lý chi tiết thông tin cá nhân: CCCD, Họ tên, Ngày sinh, Giới tính, SĐT, Nghề nghiệp, BHYT.
* **Thông tin mở rộng:** Dân tộc, Tôn giáo, Trình độ học vấn, Tổ chức Chính trị - Xã hội, Đối tượng chính sách.
* **Bộ lọc nâng cao (Advanced Filter):** Tra cứu nhanh theo Độ tuổi (Min-Max), Giới tính, Khu vực (Khóm/Ấp), Trình độ, Tôn giáo...
* **Hồ sơ điện tử:** Xem chi tiết thông tin dạng thẻ (Profile Card) với giao diện trực quan.

### 2. 🏠 Quản lý Hộ khẩu (Households)
* **Sổ hộ khẩu số:** Hiển thị danh sách hộ, Chủ hộ và các thành viên kèm quan hệ (Vợ, Chồng, Con...).
* **Đồng bộ thông minh (Smart Sync):** Tự động cập nhật địa chỉ của Hộ khẩu dựa trên địa chỉ mới nhất của Chủ hộ chỉ với 1 cú click.
* **Biến động nhân khẩu:** Thêm thành viên, Tách khẩu, Chuyển hộ, Sửa quan hệ với chủ hộ dễ dàng.
* **Tối ưu hiệu năng:** Cơ chế Caching giúp tải danh sách hàng nghìn hộ khẩu chỉ trong tích tắc.

### 3. 📥 Nhập liệu Tự động (Smart Import)
* **Hỗ trợ Excel:** Nhập hàng nghìn dòng dữ liệu từ file `.xlsx` với tốc độ cao.
* **Auto Hộ khẩu:** Tính năng đặc biệt tự động gom nhóm các cư dân có cùng địa chỉ để tạo Hộ khẩu mới và xác định Chủ hộ (Không cần tạo thủ công).
* **Xử lý trùng lặp:** Cơ chế phát hiện trùng CCCD thông minh với các tùy chọn: *Bỏ qua / Ghi đè / Ghi đè tất cả*.
* **Tiến độ thực:** Thanh Progress Bar hiển thị trạng thái xử lý thời gian thực.

### 4. 📊 Báo cáo & Thống kê
* **Dashboard trực quan:** Biểu đồ tròn (Tỷ lệ Cử tri), Biểu đồ cột (Phân bố độ tuổi).
* **Thẻ tổng quan:** Theo dõi nhanh tổng dân số, tổng hộ, tỷ lệ nam/nữ.
* **Xuất Báo cáo Excel:** Trích xuất danh sách Cử tri (18+), Người cao tuổi (>60), Trẻ em, Thanh niên nghĩa vụ quân sự, Đảng viên... chuẩn định dạng in ấn.

### 5. 🛡️ Hệ thống & Bảo mật
* **Phân quyền (Role-based):**
    * **SuperAdmin:** Toàn quyền (Quản lý User, Backup, Restore).
    * **Cán bộ:** Chỉ được thao tác dữ liệu dân cư.
* **An toàn dữ liệu:** Sao lưu (Backup) và Phục hồi (Restore) toàn bộ dữ liệu hệ thống qua file JSON.
* **Bảo mật 2 lớp:** Yêu cầu mật khẩu Admin khi thực hiện các thao tác nhạy cảm (Xóa dữ liệu, Sửa thông tin gốc).

---

## 🛠️ Yêu cầu Hệ thống & Cài đặt

### 1. Chuẩn bị môi trường
* Cài đặt **Python 3.10** trở lên.
* Kết nối Internet ổn định (để kết nối Google Firebase).

### 2. Cài đặt mã nguồn
Clone dự án về máy:
```bash
git clone [https://github.com/username-cua-ban/ResidentialManager.git](https://github.com/username-cua-ban/ResidentialManager.git)

cd ResidentialManager
```

Cài đặt các thư viện phụ thuộc:

``` bash
pip install -r requirements.txt
```
(Các thư viện chính: flet, firebase-admin, pandas, openpyxl, pyinstaller)

### 3. Cấu hình Firebase (BẮT BUỘC)
Dự án sử dụng Google Cloud Firestore. Bạn cần file khóa bí mật để chạy:

Truy cập Firebase Console.

Tạo Project mới -> Vào Project Settings -> Service Accounts.

Bấm Generate new private key để tải file .json.

Đổi tên file thành serviceAccountKey.json.

Copy file này vào thư mục gốc của dự án (ngang hàng với main.py).

**4. Chạy ứng dụng**
Mở Terminal tại thư mục dự án và chạy:
``` bash 
python main.py
```
Tài khoản mặc định ban đầu:
User: admin
Pass: admin123

**📦 Đóng gói ra file .EXE (Windows)**
Để tạo file chạy độc lập gửi cho người dùng cuối, sử dụng PyInstaller:
``` bash
pyinstaller --noconsole --onefile --name="ResidentialManager" --icon="assets/icon.ico" --add-data="assets;assets" --add-data="serviceAccountKey.json;." main.py
```
File thành phẩm sẽ nằm trong thư mục dist/.

Lưu ý: Nếu đóng gói xong mà báo lỗi thiếu file key, hãy copy thủ công file serviceAccountKey.json để cạnh file .exe.

**📂 Cấu trúc Dự án**
``` bash
ResidentialManager/
├── assets/                 # Tài nguyên: Icon app, File Excel mẫu
├── database/               # Module xử lý dữ liệu
│   └── db_manager.py       # Lõi kết nối Firestore & Logic CRUD
├── ui/                     # Giao diện người dùng (Flet Views)
│   ├── dashboard_view.py   # Khung điều hướng chính (Sidebar)
│   ├── residents_view.py   # Màn hình quản lý Cư dân
│   ├── households_view.py  # Màn hình quản lý Hộ khẩu
│   ├── import_view.py      # Màn hình Nhập liệu Excel
│   ├── export_view.py      # Màn hình Xuất báo cáo
│   ├── stats_view.py       # Dashboard Thống kê
│   ├── settings_view.py    # Cài đặt, Backup, User System
│   └── login_view.py       # Màn hình Đăng nhập
├── utils/                  # Các tiện ích bổ trợ
│   ├── security.py         # Mã hóa mật khẩu (SHA-256)
│   └── vn_locations.py     # Dữ liệu hành chính (Tỉnh/Huyện/Xã)
├── main.py                 # Điểm khởi chạy ứng dụng
├── requirements.txt        # Danh sách thư viện
└── serviceAccountKey.json  # Khóa bảo mật (Không push lên Git)
```
**🤝 Đóng góp**
Dự án được phát triển với mục đích học tập và phục vụ cộng đồng. Mọi đóng góp (Pull Request) đều được hoan nghênh.

**📝 License**
Dự án này được phân phối dưới giấy phép MIT License.

Developed by Phan Hoàng Anh © 2025
