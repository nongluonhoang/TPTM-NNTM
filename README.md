# Hệ thống quản lý trang trại thông minh qua giọng nói
Là hệ thống theo dõi nhiệt độ, độ ẩm thông minh từ xa và tích hợp thêm nhận diện "Bật" "Tắt" bằng giọng nói xử dụng ESP32, Arduino UNO, micro laptop và cảm biến DHT11

## Thành phần hệ thống
## Phần cứng
* DHT11: Lấy dữ liệu đo nhật độ, độ ẩm theo thời gian thực
* Arduino UNO: Lấy dữ liệu nhệt độ, độ ẩm và đẩy qua ESP32
* ESP32: Kết nối wifi và IPv4 để đẩy code sang VScode
## Phần mềm
* Python Flask Backend: Dùng để tạo ứng dụng trên web sever
* HTML Templates: Tạo giao diện cho websever để hiển thị thông tin đo nhiệt độ bằng biểu đồ và thời gian thực
## Sơ đồ hoạt động
![sodohoatdong](https://github.com/user-attachments/assets/5ef2f577-b9b3-47e3-b9cc-4f01294bcbf7)
## Hình ảnh của hệ thống
![download (4)](https://github.com/user-attachments/assets/86871088-7475-4f1c-be99-45fb6b2e8e5d)
