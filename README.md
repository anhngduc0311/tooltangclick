# 🚀 AutoTraffic & SEO CTR Master (Python)

Phần mềm tự động hóa tăng lượt xem (Traffic), tăng nhận diện và đẩy thứ hạng từ khóa Google (SEO CTR Manipulation) chuyên nghiệp bằng Python.

---

## 🌟 Tính Năng Nổi Bật

1. **SEO CTR Bot (Tăng thứ hạng từ khóa Google)**:
   - Tự động vào Google (hỗ trợ `google.com` và `google.com.vn`).
   - Gõ từ khóa tìm kiếm theo nhịp điệu ngẫu nhiên như người thật (Human Typing).
   - Tự động lướt qua các trang kết quả (Trang 1, 2, 3...) để tìm website mục tiêu của bạn.
   - Nhận diện đúng vị trí (Top ranking), cuộn mượt đến kết quả và click vào website.
   - Giữ chân trên trang (Dwell Time ngẫu nhiên 40 - 90 giây) với cuộn chuột tự nhiên (Smooth human scroll).
   - Tự động bấm vào 1 - 3 liên kết nội bộ trong website để tăng số trang xem (Pageviews) và giảm tỷ lệ thoát (Bounce Rate).

2. **Direct & Referral Traffic**:
   - Truy cập thẳng website mục tiêu để đẩy nhanh chỉ số Google Analytics.
   - Giả lập người dùng đến từ các mạng xã hội phổ biến: Facebook, YouTube, X (Twitter), Reddit.

3. **Chống Phát Hiện Bot & An Toàn Tuyệt Đối**:
   - Sử dụng **DrissionPage** trực tiếp điều khiển Chromium qua CDP (Chrome DevTools Protocol), loại bỏ hoàn toàn cờ `navigator.webdriver`.
   - Mỗi luồng chạy trên một thư mục Profile tạm thời độc lập, tự động dọn dẹp sạch sẽ sau mỗi phiên, không chia sẻ cookies hay lịch sử.
   - Đa dạng hóa User-Agent và độ phân giải màn hình (Desktop Windows, Mac, Android, iPhone).

4. **Hỗ Trợ Mọi Loại Proxy**:
   - Hỗ trợ định dạng `ip:port` và `ip:port:user:pass` (tự động nhúng Chrome Extension xác thực tài khoản/mật khẩu).
   - Hỗ trợ URL API xoay IP tự động (tương thích TMProxy, Tinsoft, ShopLike...).
   - Tích hợp công cụ kiểm tra độ trễ (Ping) và tình trạng sống/chết của Proxy ngay trên giao diện.

5. **Giao Diện Desktop Hiện Đại (CustomTkinter)**:
   - Phong cách Dark Mode sang trọng, hiển thị biểu đồ thống kê thời gian thực (Tổng lượt chạy, Thành công, Thất bại, Thứ hạng trung bình).
   - Khung nhật ký hoạt động (Live Logs) cập nhật từng giây có phân loại màu sắc đẹp mắt.
   - Tự động lưu và khôi phục cài đặt (`config.json`).

---

## 💻 Hướng Dẫn Cài Đặt & Sử Dụng

### Cách 1: Khởi chạy nhanh bằng file `.bat` (Khuyên dùng trên Windows)
- Nhấp đúp chuột vào file **`run.bat`** trong thư mục dự án.
- Tool sẽ tự động kiểm tra thư viện và mở giao diện ứng dụng.

### Cách 2: Khởi chạy bằng dòng lệnh
Mở Terminal hoặc PowerShell tại thư mục dự án:
```powershell
pip install -r requirements.txt
python app.py
```

---

## ⚙️ Hướng Dẫn Cấu Hình Chiến Dịch

### 1. Tab "Chiến Dịch SEO"
- **Website Mục Tiêu**: Nhập URL hoặc Domain của bạn (ví dụ: `https://yourdomain.com` hoặc `yourdomain.com`).
- **Chế độ**:
  - `SEO Google CTR`: Tìm từ khóa trên Google rồi click vào website.
  - `Direct Visit`: Mở trực tiếp link website.
  - `Referral`: Giả lập truy cập từ mạng xã hội.
- **Danh sách từ khóa SEO**: Nhập các từ khóa người dùng tìm kiếm dẫn đến web của bạn (mỗi dòng 1 từ).
- **Thời gian xem trang (Dwell time)**: Khuyên dùng từ 40 đến 90 giây để Google đánh giá cao thời lượng tương tác.
- **Duyệt trang con**: Đặt 1 - 3 trang để tăng lượt xem tự nhiên.

### 2. Tab "Cấu Hình Proxy"
- **Proxy Tĩnh**: Dán danh sách Proxy vào khung (mỗi dòng 1 proxy: `ip:port` hoặc `ip:port:user:pass`).
- **API Xoay IP (Proxy.vn / Proxyxoay.shop)**:
  - Bạn chỉ cần dán **Key xoay** (ví dụ: `rwywzSOvFNZOWDVJJBrQRb`) vào ô URL API Xoay IP.
  - Hoặc dán đầy đủ đường link: `https://proxyxoay.shop/api/get.php?key=KEY_CUA_BAN&nhamang=Random&tinhthanh=0`
  - Bấm nút **"🔄 Test API Xoay (Proxy.vn)"** để kiểm tra ngay xem Key có hợp lệ và lấy được IP, nhà mạng, vị trí không trước khi khởi chạy chiến dịch!

### 3. Tab "Cài Đặt Nâng Cao"
- **Số luồng chạy (Threads)**: Tùy theo cấu hình máy tính (1 - 5 luồng cho máy cá nhân, 5 - 10 luồng cho VPS mạnh).
- **Tổng lượt chạy mục tiêu**: Đặt số lượng mong muốn (ví dụ 50, 100) hoặc đặt `0` để chạy liên tục không giới hạn.
- **Giả lập thiết bị**: Chọn Desktop, Mobile hoặc Ngẫu nhiên kết hợp cả hai.

---

## 📁 Cấu Trúc Mã Nguồn

```
tooltangclick/
├── app.py                   # Khởi chạy ứng dụng GUI
├── run.bat                  # File nhấp đúp chạy nhanh trên Windows
├── requirements.txt         # Các thư viện phụ thuộc
├── config.json              # File lưu cấu hình người dùng
├── core/
│   ├── browser_engine.py    # Điều khiển Chromium CDP, chống bot, cuộn mượt
│   ├── seo_bot.py           # Nghiệp vụ tìm kiếm Google SEO & Click CTR
│   ├── direct_bot.py        # Nghiệp vụ Direct & Referral traffic
│   ├── proxy_manager.py     # Quản lý xoay Proxy, API IP và Extension xác thực
│   └── user_agents.py       # Kho User-Agent và độ phân giải màn hình
├── ui/
│   ├── main_window.py       # Giao diện chính CustomTkinter
│   ├── theme.py             # Bảng màu Dark Mode và font chữ
│   └── components/
│       └── log_view.py      # Khung hiển thị nhật ký thời gian thực
└── utils/
    ├── helpers.py           # Tiện ích domain, độ trễ ngẫu nhiên
    └── logger.py            # Hệ thống truyền nhận log thread-safe
```
