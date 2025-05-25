# Hướng dẫn sử dụng Module Phê Duyệt

## Tổng quan
Module phê duyệt (purchase_approval) được tách thành một module độc lập, có thể tái sử dụng cho nhiều loại yêu cầu phê duyệt khác nhau, không chỉ giới hạn ở purchase request.

## Cấu trúc module
1. **Module purchase_approval**: Module độc lập chứa logic phê duyệt chung
   - Model `approval.mixin`: Cung cấp các phương thức chung cho việc phê duyệt
   - Model `approval.request`: Quản lý các yêu cầu phê duyệt
   - Trường `is_approval` trong `hr.employee`: Xác định quyền phê duyệt

2. **Module final_n6 (Purchase Request)**: Đã được refactor để sử dụng module phê duyệt
   - Kế thừa `approval.mixin`
   - Sử dụng `approval.request` để quản lý quy trình phê duyệt

## Cách sử dụng

### Cấu hình quyền phê duyệt
1. Truy cập module Nhân viên (Employees)
2. Chọn nhân viên cần cấp quyền phê duyệt
3. Đánh dấu vào trường "Có quyền phê duyệt"

### Quy trình phê duyệt
1. Khi người dùng gửi PR (nhấn nút "Gửi PR"), hệ thống sẽ:
   - Tạo một bản ghi `approval.request` mới
   - Chuyển trạng thái PR thành "Chờ phê duyệt"
2. Người có quyền phê duyệt có thể:
   - Truy cập menu "Phê duyệt PR" trong module Purchase Request
   - Hoặc truy cập menu "Yêu cầu phê duyệt" trong module Phê duyệt
3. Xem xét thông tin chi tiết và quyết định:
   - Nhấn "Phê duyệt" để chấp nhận yêu cầu
   - Nhấn "Từ chối" để từ chối yêu cầu

### Mở rộng cho các module khác
Để sử dụng module phê duyệt cho các module khác:
1. Thêm phụ thuộc vào module `purchase_approval`
2. Kế thừa `approval.mixin` trong model cần phê duyệt
3. Sử dụng các phương thức `need_approval()`, `get_approval_status()` và `_check_approval_rights()`

## Lưu ý
- Module phê duyệt hoạt động độc lập và có thể được cài đặt riêng
- Các module sử dụng logic phê duyệt cần phụ thuộc vào module `purchase_approval`
- Quyền phê duyệt được quản lý tập trung thông qua trường `is_approval` trong `hr.employee`
