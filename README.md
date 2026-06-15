# Quản Lý Chi Tiêu - Backend API

Dự án Backend cung cấp API cho ứng dụng Quản Lý Chi Tiêu đa nền tảng (Flutter). Hệ thống được xây dựng với kiến trúc RESTful mạnh mẽ, sử dụng Python và framework FastAPI, kết hợp với cơ sở dữ liệu SQL Server.

## 🚀 Công nghệ sử dụng
- **Ngôn ngữ**: Python 3.10+
- **Framework**: FastAPI (Xử lý bất đồng bộ, tự động sinh tài liệu Swagger/OpenAPI)
- **Database ORM**: SQLAlchemy 2.0+
- **Database Driver**: `pyodbc` (Kết nối Microsoft SQL Server)
- **Xác thực**: JWT (JSON Web Token), mã hóa mật khẩu bằng `passlib (bcrypt)`
- **Xử lý file**: Hỗ trợ Upload ảnh hóa đơn thông qua `python-multipart`

## 🌟 Tính năng nổi bật
- **Hỗ trợ chuẩn Unicode (Tiếng Việt)**: Tự động tương thích với kiểu dữ liệu `NVARCHAR` trên SQL Server thông qua định dạng `Unicode` của SQLAlchemy, khắc phục triệt để lỗi mất chữ hoặc biến thành dấu `???`.
- **Bảo mật Đăng nhập Một thiết bị**: Tích hợp cơ chế theo dõi phiên hoạt động `active_sessions`. Nếu tài khoản được đăng nhập ở thiết bị thứ 2, thiết bị thứ 1 sẽ lập tức bị vô hiệu hóa Token và đăng xuất.
- **Phân quyền và Chia sẻ (Hũ chi tiêu nhóm)**: Hỗ trợ tạo các quỹ chung (Jars), mời thành viên qua Email, phân quyền (Owner, Member) và theo dõi chính xác ai là người thực hiện từng giao dịch.

## 🛠️ Hướng dẫn cài đặt và chạy server

1. **Cài đặt môi trường Python**
Tạo và kích hoạt virtual environment:
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

2. **Cài đặt thư viện phụ thuộc**
```bash
pip install -r requirements.txt
```

3. **Cấu hình Database (Biến môi trường)**
Đổi tên file `.env.example` thành `.env` (hoặc tạo file `.env`) và cập nhật thông tin SQL Server:
```env
DB_SERVER=YOUR_SERVER_NAME
DB_NAME=ManageMoneyDB
DB_DRIVER=ODBC Driver 17 for SQL Server
# Để trống User/Password nếu dùng Windows Authentication
DB_USER=
DB_PASSWORD=

SECRET_KEY=chuoi_ky_tu_bi_mat_de_tao_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

4. **Chạy Server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Truy cập tài liệu API tự động tại: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📚 API Documentation

### Auth (Xác thực)
| API Endpoint | Chức năng |
| :--- | :--- |
| `POST /auth/register` | Đăng ký tài khoản mới. |
| `POST /auth/login` | Đăng nhập và nhận JWT Token. Ghi đè session thiết bị cũ. |
| `GET /auth/me` | Lấy thông tin user hiện tại đang đăng nhập. |
| `PUT /auth/me` | Cập nhật thông tin user. |

### Categories (Danh mục)
| API Endpoint | Chức năng |
| :--- | :--- |
| `GET /categories` | Lấy danh sách danh mục, có thể lọc theo loại (thu/chi). |
| `POST /categories` | Tạo danh mục mới. |
| `GET /categories/{id}`| Lấy chi tiết 1 danh mục. |
| `PUT /categories/{id}`| Sửa thông tin danh mục. |
| `DELETE /categories/{id}`| Xóa danh mục. |

### Jars (Hũ Chi Tiêu)
| API Endpoint | Chức năng |
| :--- | :--- |
| `GET /jars` | Lấy danh sách các Hũ chi tiêu mà user sở hữu/tham gia. |
| `POST /jars` | Tạo Hũ mới (Cá nhân hoặc Nhóm). |
| `GET /jars/{id}` | Lấy chi tiết Hũ. |
| `PUT /jars/{id}` | Chỉnh sửa tên, hạn mức, loại hũ. |
| `DELETE /jars/{id}` | Xóa Hũ. |

### Jar Members (Thành viên Hũ)
| API Endpoint | Chức năng |
| :--- | :--- |
| `GET /jars/{id}/members` | Xem danh sách thành viên của Hũ. |
| `POST /jars/{id}/members` | Mời thêm user vào Hũ bằng UserId. |
| `PUT /jars/{id}/members/{user_id}`| Đổi vai trò thành viên (Owner, Member...). |
| `DELETE /jars/{id}/members/{user_id}`| Xóa thành viên khỏi Hũ. |

### Transactions (Giao dịch)
| API Endpoint | Chức năng |
| :--- | :--- |
| `GET /transactions` | Lấy lịch sử giao dịch (có phân trang và lọc theo hũ/tháng/loại). Trả về tên người thực hiện (`full_name`). |
| `POST /transactions` | Tạo giao dịch mới. Tự động cộng/trừ vào hũ tương ứng. |
| `GET /transactions/{id}`| Chi tiết 1 giao dịch. |
| `PUT /transactions/{id}`| Sửa giao dịch (chỉ áp dụng cho giao dịch của chính mình). |
| `DELETE /transactions/{id}`| Xóa giao dịch. |
| `POST /transactions/{id}/upload`| Upload ảnh hóa đơn (yêu cầu Multipart Form Data). |
| `GET /transactions/summary/monthly`| Thống kê tổng thu chi theo tháng phục vụ biểu đồ phân tích. |

### Dashboard (Tổng quan)
| API Endpoint | Chức năng |
| :--- | :--- |
| `GET /dashboard` | Lấy thông tin tổng số dư, tổng thu, tổng chi của user hiện tại. |
