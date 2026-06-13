# API Documentation
### Auth (Xác thực)
| API Endpoint | Phương thức trong `ApiService` | Chức năng |
| :--- | :--- | :--- |
| `POST /auth/register` | `register(fullName, email, password)` | Đăng ký tài khoản mới. |
| `POST /auth/login` | `login(email, password)` | Đăng nhập và lưu Token tự động vào Header của Dio. |
| `GET /auth/me` | `getMe()` | Lấy thông tin user hiện tại đang đăng nhập. |
| `PUT /auth/me` | `updateMe(fullName, email)` | Cập nhật thông tin user. |

### Categories (Danh mục)
| API Endpoint | Phương thức trong `ApiService` | Chức năng |
| :--- | :--- | :--- |
| `GET /categories` | `getCategories({isIncome})` | Lấy danh sách danh mục, có thể lọc theo thu/chi. |
| `POST /categories` | `createCategory(name, isIncome, {iconUrl})` | Tạo danh mục mới. |
| `GET /categories/{id}` | `getCategory(categoryId)` | Lấy chi tiết 1 danh mục. |
| `PUT /categories/{id}` | `updateCategory(categoryId, name, isIncome, ...)`| Sửa thông tin danh mục. |
| `DELETE /categories/{id}`| `deleteCategory(categoryId)` | Xóa danh mục. |

### Jars (Hũ Chi Tiêu)
| API Endpoint | Phương thức trong `ApiService` | Chức năng |
| :--- | :--- | :--- |
| `GET /jars` | `getJars()` | Lấy danh sách các Hũ chi tiêu. |
| `POST /jars` | `createJar(name, budget, jarType, ...)` | Tạo Hũ mới. |
| `GET /jars/{id}` | `getJar(jarId)` | Lấy chi tiết Hũ. |
| `PUT /jars/{id}` | `updateJar(jarId, name, budget, jarType)` | Chỉnh sửa Hũ. |
| `DELETE /jars/{id}` | `deleteJar(jarId)` | Xóa Hũ. |

### Jar Members (Thành viên trong Hũ)
| API Endpoint | Phương thức trong `ApiService` | Chức năng |
| :--- | :--- | :--- |
| `GET /jars/{id}/members` | `getJarMembers(jarId)` | Xem danh sách thành viên của Hũ. |
| `POST /jars/{id}/members` | `addJarMember(jarId, userId, {role})` | Thêm user vào Hũ (chia sẻ quỹ). |
| `PUT /jars/{jar_id}/members/{user_id}`| `updateJarMemberRole(jarId, userId, role)` | Đổi vai trò thành viên (Owner, Member...). |
| `DELETE /jars/{jar_id}/members/{user_id}`| `removeJarMember(jarId, userId)` | Xóa thành viên khỏi Hũ. |

### Transactions (Giao dịch)
| API Endpoint | Phương thức trong `ApiService` | Chức năng |
| :--- | :--- | :--- |
| `GET /transactions` | `getTransactions({jarId, month, year, limit})` | Lấy lịch sử giao dịch (có phân trang và bộ lọc). |
| `POST /transactions` | `createTransaction(jarId, categoryId, amount, ...)`| Tạo giao dịch mới. |
| `GET /transactions/{id}` | `getTransaction(transactionId)` | Chi tiết 1 giao dịch. |
| `PUT /transactions/{id}` | `updateTransaction(transactionId, ...)` | Sửa giao dịch. |
| `DELETE /transactions/{id}`| `deleteTransaction(transactionId)` | Xóa giao dịch. |
| `POST /transactions/{id}/upload`| `uploadTransactionReceipt(transactionId, filePath)` | **Upload ảnh hóa đơn**. Hàm này dùng `FormData` và `MultipartFile` từ `dio` để gửi file vật lý. |
| `GET /transactions/summary/monthly`| `getMonthlySummary(year, {jarId})` | Thống kê thu chi theo tháng để vẽ biểu đồ. |

### Dashboard (Tổng quan)
| API Endpoint | Phương thức trong `ApiService` | Chức năng |
| :--- | :--- | :--- |
| `GET /dashboard` | `getDashboard()` | Lấy thông tin tổng số dư, tổng thu, tổng chi để hiện trên màn hình Home. |

## 4. Cách sử dụng trong UI
Để gọi API từ các màn hình UI (như `activity_screen.dart` hoặc `home_screen.dart`), bạn chỉ cần import file `api_service.dart` và gọi trực tiếp các phương thức static.

**Ví dụ - Cách gọi upload ảnh sau khi tạo giao dịch thành công:**
```dart
// 1. Tạo giao dịch trước
final response = await ApiService.createTransaction(
  jarId, categoryId, amount, description, isIncome, date
);

// 2. Lấy ID giao dịch vừa tạo
if (response != null) {
  String transactionId = response['transaction_id'];

  // 3. Nếu người dùng có chọn ảnh, gọi hàm upload ảnh
  if (selectedImagePath != null) {
    await ApiService.uploadTransactionReceipt(transactionId, selectedImagePath);
  }
}
```
Mọi endpoints hiện tại đã được code bao phủ 100% trong `ApiService`. Mọi lỗi từ phía Backend sẽ được catch và trả về Null hoặc `Map` chứa câu báo lỗi để Frontend hiển thị an toàn.

