import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import FieldFilter
from utils.security import hash_password, verify_password
import json

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả dev và PyInstaller """
    try:
        # PyInstaller tạo ra thư mục tạm _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ĐƯỜNG DẪN ĐẾN FILE KEY FIREBASE (Cùng thư mục với main.py)
CRED_PATH = resource_path("serviceAccountKey.json")

class DatabaseManager:
    def __init__(self):
        # Kiểm tra xem App đã khởi tạo chưa để tránh lỗi init 2 lần
        if not firebase_admin._apps:
            cred = credentials.Certificate(CRED_PATH)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.check_default_admin()

    def check_default_admin(self):
        """Tạo tài khoản admin mặc định nếu chưa có"""
        doc_ref = self.db.collection('admins').document('admin')
        if not doc_ref.get().exists:
            doc_ref.set({
                'username': 'admin',
                'password_hash': hash_password("admin123"),
                'role': 'SuperAdmin'
            })

    # =========================================================================
    # 1. QUẢN LÝ CƯ DÂN (RESIDENTS)
    # =========================================================================
    
    def get_all_residents(self):
        """Lấy toàn bộ danh sách cư dân, trả về list tuple để hiển thị lên Bảng"""
        docs = self.db.collection('residents').stream()
        result = []
        for doc in docs:
            d = doc.to_dict()
            # Mapping dữ liệu Dict -> Tuple (Đúng thứ tự cột UI yêu cầu)
            # 0:cccd, 1:ho_ten, 2:gioitinh, 3:ngay_sinh, 4:bhyt, 5:nghe_nghiep, 
            # 6:sdt, 7:chinh_tri_xh, 8:che_do_chinh_sach, 9:tinh_thanh, 
            # 10:phuong_xa, 11:khom_ap, 12:dia_chi_chi_tiet, 13:quan_he_chu_ho, 
            # 14:trinh_do, 15:ma_ho_khau, 16:is_chu_ho,
            # 17:dan_toc, 18:ton_giao
            row = (
                doc.id,                         # 0. CCCD (Key)
                d.get('ho_ten', ''),            # 1
                d.get('gioi_tinh', ''),         # 2
                d.get('ngay_sinh', ''),         # 3
                d.get('bhyt', ''),              # 4
                d.get('nghe_nghiep', ''),       # 5
                d.get('sdt', ''),               # 6
                d.get('chinh_tri_xh', ''),      # 7
                d.get('che_do_chinh_sach', ''), # 8
                d.get('tinh_thanh', ''),        # 9
                d.get('phuong_xa', ''),         # 10
                d.get('khom_ap', ''),           # 11
                d.get('dia_chi_chi_tiet', ''),  # 12
                d.get('quan_he_chu_ho', ''),    # 13
                d.get('trinh_do', ''),          # 14
                d.get('ma_ho_khau', ''),        # 15
                1 if d.get('is_chu_ho') else 0, # 16
                d.get('dan_toc', ''),           # 17
                d.get('ton_giao', '')           # 18
            )
            result.append(row)
        return result

    def get_resident_by_cccd(self, cccd):
        """Lấy thông tin 1 người theo CCCD"""
        doc = self.db.collection('residents').document(cccd).get()
        if doc.exists:
            d = doc.to_dict()
            # Trả về list chứa 1 tuple (để tương thích logic cũ của UI)
            return [(
                doc.id, d.get('ho_ten', ''), d.get('gioi_tinh', ''), d.get('ngay_sinh', ''),
                d.get('bhyt', ''), d.get('nghe_nghiep', ''), d.get('sdt', ''),
                d.get('chinh_tri_xh', ''), d.get('che_do_chinh_sach', ''),
                d.get('tinh_thanh', ''), d.get('phuong_xa', ''), d.get('khom_ap', ''),
                d.get('dia_chi_chi_tiet', ''), d.get('quan_he_chu_ho', ''), 
                d.get('trinh_do', ''), d.get('ma_ho_khau', ''),
                1 if d.get('is_chu_ho') else 0,
                d.get('dan_toc', ''),
                d.get('ton_giao', '')
            )]
        return []

    def upsert_resident(self, cccd, data_dict):
        """Thêm mới hoặc Cập nhật cư dân (Upsert)"""
        self.db.collection('residents').document(cccd).set(data_dict, merge=True)

    def delete_resident(self, cccd):
        """Xóa cư dân"""
        self.db.collection('residents').document(cccd).delete()

    # =========================================================================
    # 2. QUẢN LÝ HỘ KHẨU (HOUSEHOLDS)
    # =========================================================================

    def get_all_households(self):
        """Lấy danh sách hộ khẩu (Phiên bản siêu tốc)"""
        hks = self.db.collection('households').stream()
        result = []
        
        for hk in hks:
            d = hk.to_dict()
            ma_hk = hk.id
            
            # Lấy dữ liệu có sẵn (Cache), nếu không có thì hiển thị tạm
            ten_chu_ho = d.get('cache_ten_chu_ho', '--- (Chờ cập nhật)')
            count_mem = d.get('cache_count_mem', 0)
            
            # Không thực hiện Query con ở đây nữa!
            
            row = (
                ma_hk,
                ten_chu_ho,
                d.get('dia_chi', ''),
                d.get('ngay_lap', ''),
                count_mem,
                d.get('cccd_chu_ho', '')
            )
            result.append(row)
        return result

    def recalculate_household_info(self, ma_hk):
        """
        Tính toán lại Số lượng thành viên và Tên chủ hộ, 
        sau đó lưu thẳng vào bảng Households để đọc cho nhanh.
        """
        if not ma_hk: return

        # 1. Lấy tất cả thành viên
        mems = self.db.collection('residents').where(filter=FieldFilter('ma_ho_khau', '==', ma_hk)).stream()
        members_list = [m.to_dict() for m in mems]
        
        count_mem = len(members_list)
        ten_chu_ho = "---"
        
        # 2. Tìm tên chủ hộ trong đám thành viên đó
        for m in members_list:
            if m.get('is_chu_ho') == True:
                ten_chu_ho = m.get('ho_ten', '')
                break
        
        # 3. Cập nhật ngược lại vào Households
        self.db.collection('households').document(ma_hk).update({
            'cache_count_mem': count_mem,   # Trường mới để lưu số lượng
            'cache_ten_chu_ho': ten_chu_ho  # Trường mới để lưu tên
        })

    def create_household(self, ma_hk, data_dict):
        """Tạo hộ khẩu mới và update trạng thái chủ hộ cho cư dân"""
        # 1. Lưu hộ khẩu (QUAN TRỌNG: Thêm merge=True để không xóa mất dữ liệu cũ khi update)
        self.db.collection('households').document(ma_hk).set(data_dict, merge=True)
        
        # 2. Update người được chọn làm chủ hộ
        if data_dict.get('cccd_chu_ho'):
            # Trước tiên xóa vai trò chủ hộ cũ của người này (nếu có) để tránh lỗi logic
            # (Optional: Tùy nghiệp vụ, nhưng ở đây ta cứ set thẳng)
            self.db.collection('residents').document(data_dict['cccd_chu_ho']).update({
                'ma_ho_khau': ma_hk,
                'is_chu_ho': True,
                'quan_he_chu_ho': 'Chủ hộ'
            })

        self.recalculate_household_info(ma_hk)
    
    def update_household_address(self, ma_hk, new_address):
        """Cập nhật riêng địa chỉ cho hộ khẩu"""
        self.db.collection('households').document(ma_hk).update({
            'dia_chi': new_address
        })

    def delete_household(self, ma_hk):
        """Xóa hộ khẩu và giải phóng thành viên"""
        # 1. Xóa hộ khẩu
        self.db.collection('households').document(ma_hk).delete()
        
        # 2. Update tất cả thành viên trong hộ về trạng thái "vô gia cư"
        mems = self.db.collection('residents').where(filter=FieldFilter('ma_ho_khau', '==', ma_hk)).stream()
        batch = self.db.batch()
        for mem in mems:
            ref = self.db.collection('residents').document(mem.id)
            batch.update(ref, {
                'ma_ho_khau': '',
                'is_chu_ho': False,
                'quan_he_chu_ho': ''
            })
        batch.commit()

    # =========================================================================
    # 3. QUẢN LÝ THÀNH VIÊN TRONG HỘ
    # =========================================================================

    def get_members_of_household(self, ma_hk):
        """Lấy danh sách thành viên của 1 hộ cụ thể"""
        docs = self.db.collection('residents').where(filter=FieldFilter('ma_ho_khau', '==', ma_hk)).stream()
        result = []
        for doc in docs:
            d = doc.to_dict()
            # Tuple: 0:cccd, 1:ho_ten, 2:is_chu_ho, 3:ngay_sinh, 4:quan_he
            result.append((
                doc.id,
                d.get('ho_ten', ''),
                1 if d.get('is_chu_ho') else 0,
                d.get('ngay_sinh', ''),
                d.get('quan_he_chu_ho', '')
            ))
        return result

    def add_member_to_household(self, ma_hk, cccd, quan_he):
        """Thêm người vào hộ (Cập nhật mã hộ khẩu và quan hệ)"""
        self.db.collection('residents').document(cccd).update({
            'ma_ho_khau': ma_hk,
            'quan_he_chu_ho': quan_he
        })
        self.recalculate_household_info(ma_hk)

    def remove_member_from_household(self, cccd):
        """Tách người khỏi hộ (Xóa mã hộ khẩu và quan hệ)"""
        self.db.collection('residents').document(cccd).update({
            'ma_ho_khau': '',
            'quan_he_chu_ho': '',
            'is_chu_ho': False
        })

    def update_member_relationship(self, cccd, new_quan_he):
        """Cập nhật quan hệ của thành viên với chủ hộ"""
        self.db.collection('residents').document(cccd).update({
            'quan_he_chu_ho': new_quan_he
        })

    # =========================================================================
    # 4. HỆ THỐNG & BẢO MẬT & PHÂN QUYỀN
    # =========================================================================

    def verify_login(self, username, password):
        """Kiểm tra đăng nhập cho bất kỳ user nào"""
        doc = self.db.collection('admins').document(username).get()
        if doc.exists:
            stored_hash = doc.to_dict().get('password_hash')
            return verify_password(stored_hash, password)
        return False

    def verify_admin_action(self, password):
        """Dùng cho các hành động xóa/sửa (Check pass của user 'admin' gốc)"""
        # Đây là chốt chặn an toàn cuối cùng
        doc = self.db.collection('admins').document('admin').get()
        if doc.exists:
            return verify_password(doc.to_dict().get('password_hash'), password)
        return False
    
    def get_user_role(self, username):
        """Lấy vai trò của user"""
        doc = self.db.collection('admins').document(username).get()
        if doc.exists:
            return doc.to_dict().get('role', 'Cán bộ')
        return None

    def get_all_users(self):
        """Lấy danh sách tài khoản hệ thống"""
        docs = self.db.collection('admins').stream()
        return [doc.to_dict() for doc in docs]

    def create_user(self, username, password, role="Cán bộ"):
        """Tạo tài khoản mới"""
        if self.db.collection('admins').document(username).get().exists:
            return False
        self.db.collection('admins').document(username).set({
            'username': username,
            'password_hash': hash_password(password),
            'role': role
        })
        return True

    def delete_user(self, username):
        """Xóa tài khoản (Trừ admin gốc)"""
        if username == 'admin': return False
        self.db.collection('admins').document(username).delete()
        return True

    def update_user(self, username, new_password=None, new_role=None):
        """Cập nhật thông tin user (Mật khẩu hoặc Role)"""
        data = {}
        if new_password and new_password.strip():
            data['password_hash'] = hash_password(new_password)
        if new_role:
            data['role'] = new_role
        if data:
            self.db.collection('admins').document(username).update(data)
            return True
        return False

    def change_password(self, new_pass):
        """Hàm cũ: Đổi mật khẩu admin gốc (Giữ lại để tương thích)"""
        self.update_user('admin', new_password=new_pass)

    # =========================================================================
    # 5. SAO LƯU & PHỤC HỒI (JSON)
    # =========================================================================

    def backup_to_json(self):
        """Xuất toàn bộ dữ liệu ra chuỗi JSON để backup"""
        data = {
            'residents': [],
            'households': []
        }
        
        for r in self.db.collection('residents').stream():
            d = r.to_dict(); d['id'] = r.id
            data['residents'].append(d)
            
        for h in self.db.collection('households').stream():
            d = h.to_dict(); d['id'] = h.id
            data['households'].append(d)
            
        return json.dumps(data, ensure_ascii=False, indent=4)

    def restore_from_json(self, json_str):
        """Khôi phục dữ liệu từ chuỗi JSON"""
        data = json.loads(json_str)
        batch = self.db.batch()
        count = 0
        BATCH_LIMIT = 400
        
        for r in data.get('residents', []):
            res_id = r.pop('id')
            ref = self.db.collection('residents').document(res_id)
            batch.set(ref, r)
            count += 1
            if count >= BATCH_LIMIT:
                batch.commit(); batch = self.db.batch(); count = 0
        
        for h in data.get('households', []):
            hk_id = h.pop('id')
            ref = self.db.collection('households').document(hk_id)
            batch.set(ref, h)
            count += 1
            if count >= BATCH_LIMIT:
                batch.commit(); batch = self.db.batch(); count = 0
                
        if count > 0:
            batch.commit()

# Instance dùng chung cho toàn app
db = DatabaseManager()