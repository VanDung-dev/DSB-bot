# 🤖 DSB Discord Bot

**DSB Bot** là một bot Discord đa chức năng được phát triển bằng Python và `discord.py`, hỗ trợ quản lý máy chủ, phát nhạc, tương tác AI (Google Gemini), kiểm duyệt nội dung, tìm kiếm hình ảnh và gửi tin nhắn chào mừng/tạm biệt.
 
> Phát triển bởi: [VanDung-dev](https://github.com/VanDung-dev)

---

## 🚀 Tính năng chính

| Danh mục       | Mô tả |
|----------------|-------|
| 🎵 Phát nhạc     | Phát video từ YouTube bằng từ khóa hoặc URL. Hỗ trợ hàng đợi, tạm dừng, bỏ qua, xóa bài, v.v. |
| 🤖 Trò chuyện AI | Tương tác tự nhiên với Google Gemini AI. |
| 🚨 Kiểm duyệt    | Tự động kiểm tra tin nhắn chứa từ cấm và cảnh báo. |
| 🖼️ Tìm kiếm ảnh | Tìm kiếm ảnh từ DuckDuckGo theo từ khóa. |
| 👋 Chào mừng     | Gửi tin nhắn tự động khi thành viên tham gia hoặc rời server. |
| 📢 Text-to-Speech| Chuyển đổi văn bản thành giọng nói trong kênh thoại. |
| 📋 Trợ giúp      | Giao diện trợ giúp bằng nút tương tác, hiển thị danh mục lệnh rõ ràng. |

---

## 🧠 Các lệnh tiêu biểu

### 📋 Cơ bản
- `/hello` – Chào hỏi bot.
- `/help` – Hiển thị danh sách lệnh.

### 🎵 Âm nhạc
- `/play <từ khóa|URL>` – Phát nhạc hoặc thêm vào hàng đợi.
- `/queue`, `/np`, `/pause`, `/skip`, `/resume`, `/clear`, `/remove <số>`, `/stop`, `/leave`.

### 🤖 AI
- `/ai <tin nhắn>` – Chat với Gemini AI.
- `/aistatus`, `/aihelp`, `/aiconfig`.

### 🖼️ Hình ảnh
- `/image <từ khóa>` – Tìm kiếm ảnh từ DuckDuckGo.

### 📢 Nói chuyện
- `/say <tin nhắn>` – Bot sẽ nói thay cho bạn trong kênh thoại.

### 🚨 Kiểm duyệt
- `/addbadword`, `/removebadword`, `/listbadwords`, `/modhelp`.

### ⚙️ Quản trị viên
- `/setwelcome <#channel>`, `/testwelcome <@user>`, `/aiconfig`.

> Gõ `/help <danh mục>` để xem hướng dẫn chi tiết từng nhóm lệnh: `basic`, `music`, `speak`, `image`, `ai`, `moderation`, `admin`.

---

## 🛠️ Cài đặt

### 1. Clone project
```bash
git clone <URL-repository-của-bạn>
cd <tên-thư-mục>
```

### 2. Tạo môi trường ảo

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 4. Tạo file `.env`

```env
KEY_DISCORD=<your_discord_bot_token>
GEMINI_API_KEY=<your_gemini_api_key>
SPOTIFY_CLIENT_ID=<your_spotify_client_id>
SPOTIFY_CLIENT_SECRET=<your_spotify_client_secret>
TTS_DEFAULT_LANGUAGE=<mã_ngôn_ngữ_mặc_định> # Mặc định là 'vi' (Tiếng Việt)
```

> Có thể sao chép từ `.env.example` nếu có.

### 5. Khởi chạy bot

```bash
python main.py
```

---

## 🐳 Chạy với Docker

### 1. Tạo file `.env` từ mẫu

```bash
cp .env.example .env
```

### 2. Chỉnh sửa file `.env` với token và API key của bạn

```env
KEY_DISCORD=your_actual_discord_bot_token
GEMINI_API_KEY=your_actual_gemini_api_key
SPOTIFY_CLIENT_ID=<your_spotify_client_id>
SPOTIFY_CLIENT_SECRET=<your_spotify_client_secret>
TTS_DEFAULT_LANGUAGE=<mã_ngôn_ngữ_mặc_định> # Mặc định là 'vi' (Tiếng Việt)
```

### 3. Build và chạy container

```bash
docker-compose up --build
```

### Hoặc build và chạy trực tiếp với Docker

```bash
# Build image
docker build -t dsb-bot .

# Run container
docker run --env-file .env dsb-bot
```

---

## ☁️ Chạy trên Replit

* Đảm bảo có file `replit.nix` để cài `ffmpeg` và `libopus`.
* Thêm `KEY_DISCORD` và `GEMINI_API_KEY` vào phần **Secrets**.
* Chạy:

```bash
python main.py
```

---

## 📬 Đóng góp

* 📥 Báo lỗi: mở [issue](https://github.com/VanDung-dev/DSB-bot/issues)
* 🔁 Đóng góp mã: gửi Pull Request
* ✉️ Liên hệ trực tiếp: **VanDung-dev**

---

## 📄 License

Dự án sử dụng giấy phép **MIT License**.
Chi tiết: [LICENSE](./LICENSE)