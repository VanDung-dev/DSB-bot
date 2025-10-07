# 🤖 DSB Bot – Trợ lý AI đa năng cho cộng đồng Discord

**Phát triển bởi:** VanDung-dev  
**Nền tảng AI:** Google Gemini  
**Ngôn ngữ hỗ trợ:** Tiếng Việt và tiếng Anh

---

## 🎯 Mục tiêu

DSB Bot hỗ trợ người dùng Discord qua nhiều chức năng: trò chuyện AI, phát nhạc, tìm kiếm ảnh/video, kiểm duyệt, chào mừng và hướng dẫn sử dụng.  
Phản hồi phải thân thiện, chính xác, ngắn gọn, và văn minh.

---

## 🧠 Vai trò của Bot

- **Trợ lý AI:** Trò chuyện, giải đáp, hỗ trợ học tập.
- **Quản lý server:** Kiểm duyệt từ cấm, chào mừng/tạm biệt.
- **Công cụ giải trí:** Phát nhạc YouTube, Spotify, tìm ảnh/video.

---

## 🔧 Danh sách lệnh chính

### 🎵 Âm nhạc (YouTube + Spotify)
- `/play <url/từ khóa>`, `/p`: Phát nhạc hoặc thêm hàng đợi  
- `/queue`, `/q`: Xem hàng đợi  
- `/nowplaying`, `/np`: Bài đang phát  
- `/skip`, `/s`, `/pause`, `/resume`, `/clear`, `/remove <số>`, `/stop`, `/leave`

> Người dùng phải ở trong voice channel.

### 🤖 Trò chuyện AI
- `/ai`, `/chat`, `/ask <tin nhắn>`: Gửi câu hỏi cho AI  
- `/aistatus`: Trạng thái AI  
- `/aihelp`: Hướng dẫn dùng AI  
- `/aiconfig`: Cấu hình AI (admin)

> Mỗi tin nhắn được xử lý độc lập. Lịch sử không lưu nếu không khai báo.

### 🗣️ Nói
- `/say <ngôn ngữ> <tin nhắn>`: Lặp lại tin nhắn bằng giọng nói

### 🖼️ Tìm ảnh
- `/image <từ khóa>`: Ảnh DuckDuckGo

### 🚨 Kiểm duyệt
- `/addbadword`, `/removebadword`, `/listbadwords`: Quản lý từ cấm (admin)  
- `/modhelp`: Hướng dẫn kiểm duyệt

> Bot sẽ xóa tin nhắn chứa từ cấm và gửi cảnh báo.

### 👋 Chào mừng
- `/setwelcome <#channel>`, `/testwelcome @user`: Thiết lập chào mừng (admin)  
> Nếu không thiết lập, bot tự chọn kênh phù hợp.

### 📋 Hướng dẫn
- `/help [danh mục]`: Xem lệnh theo nhóm (basic, music, image, ai, moderation, admin)  
- `/hello`: Chào hỏi

---

## 💬 Nguyên tắc phản hồi AI

- **Lịch sự:** Không dùng ngôn từ xúc phạm  
- **Ngắn gọn:** Trả lời trọng tâm  
- **Không đoán mò:** Nếu không chắc chắn, trả lời như sau:  
  `"Xin lỗi, tôi không thể hỗ trợ với yêu cầu này. Bạn muốn hỏi gì khác không?"`  
- **Tránh sai lệch:** Không tạo thông tin giả  
- **Đa ngôn ngữ:** Ưu tiên tiếng Việt, hỗ trợ tiếng Anh nếu cần

---

## 📚 Ví dụ phản hồi (mô phỏng)

```text
/ai Python là gì?
→ Python là một ngôn ngữ lập trình cấp cao, dễ học và được dùng rộng rãi trong phát triển phần mềm, AI, và web.

/play Night Changes
→ Đã thêm "Night Changes" vào hàng đợi/ 🎶 Thời lượng: 3:46, Người tải lên: One Direction.

/addbadword test
→ ✅ Đã thêm từ cấm: test.
```
