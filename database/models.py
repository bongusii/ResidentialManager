-- Bảng Cư Dân (Residents)
CREATE TABLE residents (
    cccd TEXT PRIMARY KEY,
    ho_ten TEXT NOT NULL,
    gioi_tinh TEXT,             -- 'Nam', 'Nữ'
    ngay_sinh TEXT,             -- Lưu dạng YYYY-MM-DD để dễ sort/thống kê
    bhyt TEXT,
    nghe_nghiep TEXT,
    sdt TEXT,
    chinh_tri_xh TEXT,          -- Lưu chuỗi JSON hoặc String phân cách: "Đảng, Đoàn, Khác: Hội thơ"
    che_do_chinh_sach TEXT,     -- Tương tự trên
    ma_ho_khau TEXT,            -- Khóa ngoại liên kết hộ khẩu (có thể null nếu chưa vào hộ)
    is_chu_ho BOOLEAN DEFAULT 0 -- Đánh dấu là chủ hộ
);

-- Bảng Hộ Khẩu (Households)
CREATE TABLE households (
    ma_ho_khau TEXT PRIMARY KEY,
    dia_chi TEXT,
    cccd_chu_ho TEXT,           -- Khóa ngoại
    ngay_lap DATE
);

-- Bảng Admin (Cho bảo mật)
CREATE TABLE admins (
    username TEXT PRIMARY KEY,
    password_hash TEXT          -- SHA-256
);