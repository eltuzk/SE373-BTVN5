---
name: refund-policy
description: Tra cứu tài liệu chính sách hoàn tiền trong workspace, chọn đúng phiên bản chính sách theo ngày mua và kết luận khách hàng có đủ điều kiện hoàn tiền hay không, kèm phí và tài liệu căn cứ. Dùng khi người dùng hỏi có được hoàn tiền/trả hàng không, điều kiện, thời hạn hoặc phí hoàn tiền của một đơn hàng.
---

# Refund policy

Chọn và áp dụng chính sách hoàn tiền **theo ngày mua**, chỉ dựa trên tài liệu đọc được trong cuộc trò chuyện hiện tại. Không trả lời từ kiến thức sẵn có.

## 1. Kiểm tra thông tin đầu vào

Cần đủ ba thông tin từ người dùng:

- **Ngày mua**.
- **Ngày yêu cầu hoàn tiền**.
- **Trạng thái kích hoạt** sản phẩm (đã kích hoạt hay chưa).

Nếu thiếu bất kỳ thông tin nào: hỏi lại đúng thông tin còn thiếu và **dừng, chưa kết luận**. Không tự giả định (ví dụ không mặc định "chưa kích hoạt", không lấy ngày hiện tại của máy làm ngày yêu cầu). Dùng mẫu "Thiếu thông tin" trong reference.

Ngày viết dạng `dd/mm/yyyy` là ngày/tháng/năm. Nếu ngày mơ hồ hoặc ngày yêu cầu sớm hơn ngày mua, hỏi lại.

## 2. Tìm tài liệu chính sách

1. Dùng `list_files` với `data/policies` để xem tài liệu hiện có. **Không đoán tên file** và không dùng tên file hay nội dung đã thấy ở cuộc trò chuyện khác: tên file có thể đã đổi.
2. Nếu có thư mục con, liệt kê tiếp để tìm hết tài liệu. Nếu thư mục không tồn tại hoặc không có tài liệu, báo cho người dùng và dừng.
3. Dùng `read_file` đọc từng tài liệu chính sách (theo trường `path` trong kết quả `list_files`).

## 3. Chọn chính sách theo ngày mua

- Xác định phạm vi hiệu lực từ **nội dung** tài liệu (dòng "Áp dụng cho ngày mua ..."), không suy ra từ tên file.
- So sánh **ngày mua** (không phải ngày yêu cầu, không phải ngày hiện tại) với phạm vi:
  - "trước D": ngày mua < D.
  - "từ D, bao gồm ngày này": ngày mua ≥ D.
- Phải có đúng một chính sách khớp. Nếu không có hoặc có nhiều hơn một, báo mâu thuẫn và dừng, không đoán.

## 4. Áp dụng chính sách

1. **Số ngày đã qua** = chênh lệch ngày lịch giữa ngày yêu cầu hoàn và ngày mua. Tính cẩn thận theo số ngày thực của từng tháng (tháng 4, 6, 9, 11 có 30 ngày; tháng 2 có 28/29 ngày; các tháng còn lại 31 ngày) và ghi rõ phép tính. Ví dụ: mua 25/01, yêu cầu 03/02 → (31 − 25) + 3 = 9 ngày.
2. **Điều kiện thời gian**: số ngày đã qua ≤ giới hạn của chính sách thì đạt. Bằng đúng giới hạn vẫn đạt.
3. **Các điều kiện khác** ghi trong chính sách (ví dụ trạng thái kích hoạt) phải thỏa hết.
4. **Kết luận**: đủ điều kiện chỉ khi mọi điều kiện đều đạt; nêu rõ điều kiện nào không đạt.
5. **Phí**: chỉ nêu khi đủ điều kiện, theo đúng chính sách đã chọn. Nếu phí tính theo % giá trị đơn mà người dùng chưa cho giá trị đơn, ghi tỷ lệ phần trăm, không tự bịa số tiền. Không đủ điều kiện thì ghi "Không áp dụng".

## 5. Trả lời

Đọc `references/answer-template.md` trong thư mục skill này, tức `skills/refund-policy/references/answer-template.md`, và trả lời đúng cấu trúc đó. Đường dẫn căn cứ là `path` của tài liệu đã đọc thành công bằng `read_file`. Không cần ghi file.
