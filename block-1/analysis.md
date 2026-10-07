# Block 1: Tra cứu chính sách đúng phiên bản: phân tích

Thành viên nhóm: `<điền tên>`. Model: `<điền MODEL_NAME trong .env>`.

> Các mục đánh dấu **[TRACE]** cần điền tên file trace và số `sequence` sau khi chạy app.
> Lấy nhanh bằng chứng: `python scripts/trace_summary.py block-1/stage-02-skills/traces/` (chạy từ thư mục gốc package).

## 1. Thay đổi đã làm

| Stage | File | Thay đổi |
|---|---|---|
| 01, 02 | `tools/files.py` | Thêm `_list(workspace, path)` và tool `list_files(path)`. Tái sử dụng `_resolve()` (chặn path rỗng, path tuyệt đối/`~`, `..`, symlink thoát workspace) và `_error()` (cấu trúc `{"ok": false, "error": {"code", "message"}}`). Liệt kê mục trực tiếp, không đệ quy, sắp xếp theo tên; mỗi mục có `name`, `path` (tương đối workspace), `type` (`file`/`directory`). Symlink con trỏ ra ngoài workspace bị bỏ khỏi danh sách. |
| 01, 02 | `tools/__init__.py`, `agent.py` | Đăng ký: `TOOLS = [read_file, write_file, list_files]`, nên `list_files` có trong schema `tools` gửi model. |
| 01, 02 | `config.py` | Chỉ cập nhật `CAPABILITY_TEXT` (caption trên UI) cho đúng danh sách tool. **Không sửa `prompts.py`**: system prompt không chứa tên file, nội dung chính sách hay đáp án. |
| 01, 02 | `workspace/data/policies/`, `fixtures/data/policies/` | Hai tài liệu chính sách theo đề. Có bản trong `fixtures/` để `reset_workspace.py` không làm mất. |
| 02 | `workspace/skills/refund-policy/` (+ bản trong `fixtures/skills/`) | `SKILL.md` và `references/answer-template.md`. |
| 01, 02 | `tests/` | Test cho `list_files` (sắp xếp, không đệ quy, file → lỗi, không tồn tại → lỗi, `..`/tuyệt đối/symlink → lỗi, có trong schema request). Cập nhật số tool (3) và số skill trong catalog (2). |

Không có tên file chính sách, ngày hiệu lực, thời hạn hay phí nào được viết cố định trong system prompt, mã nguồn tool hay skill. Test `test_refund_policy_skill_layout_and_no_hard_coded_policy` kiểm tra điều này cho skill.

### Skill `refund-policy`

- Frontmatter: `name: refund-policy`. `description` nêu nhiệm vụ (tra tài liệu, chọn phiên bản theo ngày mua, kết luận, phí, căn cứ) và điều kiện dùng (hỏi về hoàn tiền/trả hàng, điều kiện, thời hạn, phí).
- Quy trình: (1) kiểm tra đủ ngày mua, ngày yêu cầu, trạng thái kích hoạt; thiếu thì hỏi lại và dừng. (2) `list_files data/policies`, không đoán tên file, không dùng tài liệu từ cuộc trò chuyện khác. (3) `read_file` từng tài liệu, đọc phạm vi hiệu lực **trong nội dung**. (4) Chọn theo **ngày mua** với quy tắc "trước D" là `<`, "từ D, bao gồm" là `>=`. (5) Tính số ngày lịch, bằng giới hạn vẫn đạt. (6) Trả lời theo reference.
- Reference có đủ: chính sách áp dụng, số ngày đã qua, kết luận đủ/không đủ, phí (nếu đủ điều kiện), đường dẫn tài liệu căn cứ, và mẫu câu hỏi lại khi thiếu thông tin.
- Không yêu cầu Bash/script.

## 2. Kiểm tra tool trực tiếp

Kết quả đầy đủ: [`results/list_files_direct_stage-01-files.txt`](results/list_files_direct_stage-01-files.txt), [`results/list_files_direct_stage-02-skills.txt`](results/list_files_direct_stage-02-skills.txt). Chỉ dùng đường dẫn giả, không nhắm vào file bí mật.

| Trường hợp | Gọi | Kết quả |
|---|---|---|
| Thư mục hợp lệ | `list_files("data/policies")` | `ok: true`, 2 mục `type: file`, sắp xếp theo tên, `path` dạng `data/policies/...` |
| Đường dẫn là file | `list_files("data/policies/policy-before-oct.md")` | `ok: false`, `NOT_A_DIRECTORY` |
| Không tồn tại | `list_files("data/khong-ton-tai")` | `ok: false`, `DIRECTORY_NOT_FOUND` (không trả danh sách rỗng) |
| Vượt workspace (`..`) | `list_files("../")`, `list_files("data/../../fixtures")` | `ok: false`, `PATH_OUTSIDE_WORKSPACE` |
| Đường dẫn tuyệt đối | `list_files("C:/fake-outside-dir")` | `ok: false`, `PATH_OUTSIDE_WORKSPACE` |
| Symlink ra ngoài | test `test_list_symlink_escape_blocked` | Liệt kê thư mục symlink → `PATH_OUTSIDE_WORKSPACE`; symlink ra ngoài không xuất hiện trong danh sách thư mục cha |

Pytest (Windows, Python 3.12): stage 01 **42 passed**, stage 02 **50 passed**. 3 test symlink (2 test có sẵn của lab và 1 test mới) lỗi `WinError 1314` vì Windows chưa bật quyền tạo symlink; lab gốc cũng lỗi y như vậy. Logic symlink của `_read`, `_write`, `_list` đã được chạy lại trên Linux (WSL Ubuntu) và đều chặn đúng.

## 3. Stage 00: giới hạn của agent

Câu hỏi trường hợp A gửi cho stage 00 (không dán chính sách):

> Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?

- **[TRACE]** `block-1/stage-00-chat/traces/<file>.jsonl`: `user_submitted.tools = []`, không có `tool_started`.
- Quan sát: `<ghi lại câu trả lời: agent trả lời chung chung / theo kiến thức sẵn có / thừa nhận không có chính sách>`.
- Agent còn thiếu:
  - **Thông tin**: nội dung chính sách hoàn tiền của cửa hàng (thời hạn, phí, điều kiện) và việc có **hai phiên bản** theo ngày mua.
  - **Khả năng**: không có tool để tìm (liệt kê) hay đọc tài liệu, nên mọi câu trả lời chỉ dựa vào kiến thức sẵn có. Đó là đoán, không có căn cứ.
  - **Quy trình**: không biết phải chọn chính sách theo ngày mua, cách tính số ngày và quy tắc biên.

## 4. Kết quả các trường hợp kiểm tra (stage 02)

Đáp án tính tay để đối chiếu:

- A: mua 28/09/2026 (< 2026-10-01) → chính sách **cũ**. Số ngày = (30 − 28) + 6 = **8** > 7 → **không đủ điều kiện** (dù chưa kích hoạt). Phí: không áp dụng.
- B: mua 02/10/2026 (≥ 2026-10-01) → chính sách **mới**. Số ngày = 12 − 2 = **10** ≤ 14, chưa kích hoạt → **đủ điều kiện, không phí**.

| Trường hợp | Kết quả cần đạt | Kết quả thực tế | Bằng chứng trong trace |
|---|---|---|---|
| A | Chính sách cũ; 8 ngày; không đủ điều kiện | `<điền>` | **[TRACE]** `<file>`: seq `<n>` `read_file skills/refund-policy/SKILL.md`; seq `<n>` `list_files data/policies` → 2 mục; seq `<n>` `read_file data/policies/policy-before-oct.md`; câu trả lời dẫn `data/policies/policy-before-oct.md` |
| B (sau khi đổi tên file) | Chính sách mới; 10 ngày; đủ điều kiện, không phí | `<điền>` | **[TRACE]** `<file>`: `model_request` cuối có tool message chứa nội dung `SKILL.md` và `references/answer-template.md`; `list_files` trả **tên mới**; `read_file` tên mới; câu trả lời dẫn đúng đường dẫn mới |
| Đổi tên file (A chạy lại) | Kết luận không đổi | `<điền>` | **[TRACE]** `<file>`: cuộc trò chuyện **mới** (conversation_id khác), `list_files` trả tên mới, không dùng tài liệu từ lịch sử cũ |
| Thiếu thông tin | Hỏi trạng thái kích hoạt, chưa kết luận | `<điền>` | **[TRACE]** `<file>`: có `read_file SKILL.md`; **không** có kết luận đủ/không đủ; câu trả lời hỏi sản phẩm đã kích hoạt chưa |

Lệnh đổi tên dùng khi kiểm tra (giữ nguyên nội dung):

```bash
cd block-1/stage-02-skills/workspace/data/policies
mv policy-before-oct.md refund-v1-legacy.md
mv policy-from-oct.md refund-v2-current.md
```

## 5. Câu hỏi cuối bài

**Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách?**

- **Tool `list_files`** cho agent một cách **quan sát** trạng thái thật của workspace lúc chạy. `read_file` chỉ đọc được khi đã biết chính xác đường dẫn. Không liệt kê được thư mục thì model chỉ có thể đoán tên file, dẫn tới `FILE_NOT_FOUND` hoặc bịa nội dung. Tool là năng lực (capability): nó mở rộng việc agent *có thể làm*.
- **Skill `refund-policy`** là quy trình (procedure): nó quy định agent *nên làm gì* với năng lực đó. Gồm tìm ở đâu, đọc phạm vi hiệu lực trong nội dung, chọn theo **ngày mua** chứ không theo ngày yêu cầu hay ngày máy, quy tắc biên (`<` / `>=`, bằng giới hạn vẫn đạt), hỏi lại khi thiếu dữ liệu và trả lời theo mẫu có căn cứ. Thiếu skill thì model có tool vẫn dễ chọn sai phiên bản, tính sai ngày hoặc tự giả định "chưa kích hoạt". Skill chỉ nạp khi task khớp `description`, nên không làm phình system prompt và sửa được mà không đụng code.
- Hai thứ bổ sung cho nhau: tool trả lời câu hỏi "tài liệu nào đang tồn tại?", skill trả lời câu hỏi "áp dụng tài liệu nào và áp dụng thế nào?".

**Nếu agent chưa có tool tìm file, sửa prompt có giải quyết được yêu cầu đổi tên file không?**

Không. Prompt là văn bản tĩnh, viết **trước** khi chạy, còn tên file thay đổi **khi** chạy:

- Muốn agent đọc được bằng `read_file` thì prompt phải ghi cứng tên file. Đổi tên thì đường dẫn trong prompt sai ngay, `read_file` trả `FILE_NOT_FOUND`, và agent không có cách nào khám phá tên mới. Ghi cứng tên file trong prompt cũng vi phạm giới hạn của đề.
- Dặn "hãy tìm file chính sách" không tạo ra khả năng tìm: model không có tool liệt kê thì chỉ đoán tên, mà đoán không phải tra cứu.
- Dán luôn nội dung chính sách vào prompt thì không còn là tra cứu tài liệu. Prompt sẽ lỗi thời khi tài liệu đổi, và cũng vi phạm yêu cầu "không viết cố định nội dung chính sách".

Vì vậy yêu cầu đổi tên file chỉ giải được bằng một **tool quan sát môi trường** (`list_files`), kết hợp với skill dặn luôn liệt kê lại trong cuộc trò chuyện hiện tại thay vì dựa vào tên cũ.
