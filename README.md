# Hướng dẫn sử dụng Module Phê Duyệt Purchase Request

## Tổng quan
Module phê duyệt Purchase Request được phát triển để quản lý quy trình phê duyệt các yêu cầu mua hàng. Module này cho phép người dùng có quyền phê duyệt xem danh sách các PR đang chờ phê duyệt và thực hiện các thao tác phê duyệt hoặc từ chối.

## Các tính năng chính
1. Danh sách các PR đang chờ phê duyệt (state = 'to_approve')
2. Form phê duyệt với các thông tin chi tiết về PR
3. Chức năng phê duyệt và từ chối PR
4. Phân quyền dựa trên trường is_approval của nhân viên

## Cách sử dụng

### Cấu hình quyền phê duyệt
1. Truy cập module Nhân viên (Employees)
2. Chọn nhân viên cần cấp quyền phê duyệt
3. Đánh dấu vào trường "Có quyền phê duyệt PR"

### Quy trình phê duyệt
1. Khi người dùng gửi PR (nhấn nút "Gửi PR"), trạng thái PR sẽ chuyển thành "Chờ phê duyệt"
2. Người có quyền phê duyệt truy cập menu "Phê duyệt PR"
3. Chọn PR cần xem xét từ danh sách
4. Xem xét thông tin chi tiết và quyết định:
   - Nhấn "Phê duyệt" để chấp nhận PR (trạng thái chuyển thành "Đã phê duyệt")
   - Nhấn "Từ chối" để từ chối PR (trạng thái chuyển thành "Hủy")
5. Có thể nhập ghi chú phê duyệt trước khi thực hiện quyết định

### Lưu ý
- Chỉ người dùng có liên kết với nhân viên có trường is_approval = True mới thấy được nút "Phê duyệt" và "Từ chối"
- Thông tin người phê duyệt và thời gian phê duyệt được tự động cập nhật khi thực hiện thao tác phê duyệt/từ chối
- Người không có quyền phê duyệt vẫn có thể xem thông tin PR nhưng không thể thực hiện các thao tác phê duyệt/từ chối
