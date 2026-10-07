# Block 2: Kiểm tra quá tải theo người: phân tích

Thành viên nhóm: `<điền tên>`. Model: `<điền MODEL_NAME trong .env>`.

> Các mục đánh dấu **[TRACE]** cần điền tên file trace và số `sequence` sau khi chạy app (stage 03/04 cần bash: chạy trong WSL/Linux).
> Lấy nhanh bằng chứng: `python scripts/trace_summary.py block-2/stage-04-script-skill/traces/` (chạy từ thư mục gốc package).

## 1. Thay đổi đã làm

Chỉ sửa skill `csv-quality` (script, `SKILL.md`, reference) và thêm dữ liệu/test. **Không thêm tool, không sửa `agent.py`, không viết cố định ngưỡng 8 hay kết quả** trong script hoặc skill.

| File | Thay đổi |
|---|---|
| `scripts/check_csv.py` | Thêm tham số **bắt buộc** `--max-hours`. Giá trị được kiểm bằng chính `parse_hours()` có sẵn (số hữu hạn, không âm). Thiếu hoặc sai thì argparse ghi lỗi ra stderr và trả exit 2. Trong vòng lặp có sẵn, mỗi dòng gom tập lý do loại; dòng không có lý do nào thì được cộng vào `hours_by_owner[owner]`. Thêm 4 trường JSON: `max_hours`, `hours_by_owner`, `overloaded_owners`, `excluded_rows`. Giữ nguyên các trường và cách tính chất lượng cũ (trên toàn bộ dòng) cùng cách báo lỗi exit 1. |
| `SKILL.md` | `description` thêm tổng giờ và quá tải. Thêm mục **Ngưỡng giờ**: lấy từ yêu cầu trong cuộc trò chuyện hiện tại và truyền đúng vào `--max-hours`; thiếu thì hỏi lại và dừng; không tự chọn, không dùng ngưỡng cũ. Mô tả trường JSON mới, exit 1/2, quy tắc loại dòng. Bỏ quy tắc cũ "không tính tổng giờ khi còn dữ liệu lỗi" (script đã loại dòng lỗi). |
| `references/report-template.md` | Thêm mục **Tải công việc theo người**: ngưỡng, bảng tổng giờ theo người, người vượt ngưỡng, bảng dòng bị loại kèm **tất cả** lý do. |
| `fixtures/skills/csv-quality/` | Bản đồng bộ với `workspace/skills/csv-quality/` (test `test_workspace_skill_synced_with_fixtures` kiểm tra byte-by-byte). |
| `data/workload.csv`, `data/workload-edge.csv` | Có trong `workspace/data/` và `fixtures/data/` (stage 03 chỉ có `workload.csv`). |
| `tests/test_check_csv.py` | Cập nhật test cũ để truyền `--max-hours`. Thêm test: ngưỡng 8, ngưỡng 9 (bằng ngưỡng không quá tải), **ID đầu tiên có hours không hợp lệ** (`test_first_occurrence_with_invalid_hours_still_claims_id`), nhiều lý do trên một dòng theo đúng thứ tự, trim/hoa-thường/dòng trống, sắp xếp người quá tải, thiếu/sai `--max-hours`, không sửa input. |
| `tests/test_agent.py` | Luồng skill với mock model chạy lệnh có `--max-hours 8` trên `workload.csv`. |

### Thuật toán (theo đúng đặc tả)

1. Bỏ khoảng trắng đầu/cuối ở `task_id`, `owner`, `hours`. Owner phân biệt hoa/thường. Bỏ qua dòng trống.
2. `first_seen` ghi lại mọi ID không rỗng ở **lần xuất hiện đầu tiên**, kể cả khi dòng đó không hợp lệ. Mọi lần sau đều nhận `duplicate_id`.
3. Lý do loại được kiểm độc lập (một dòng có thể có nhiều lý do) và xuất theo thứ tự cố định `wrong_field_count, missing_task_id, duplicate_id, missing_owner, invalid_hours`.
4. Chỉ cộng dòng không có lý do nào. Tổng dùng `math.fsum` rồi làm tròn 9 chữ số **trước khi so ngưỡng**, để `0.1 + 0.2` không bị coi là "lớn hơn" `0.3`.
5. Quá tải khi `tổng > ngưỡng`. `overloaded_owners` và `hours_by_owner` sắp xếp theo tên.

## 2. JSON khi chạy script trực tiếp

Từ thư mục `block-2/stage-04-script-skill`:

```bash
uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 8
```

| Chạy | File kết quả | Exit | `hours_by_owner` | `overloaded_owners` | `excluded_rows` |
|---|---|---|---|---|---|
| `workload.csv`, ngưỡng 8 | [`results/workload-max8.json`](results/workload-max8.json) | 0 | `{"Lan": 9, "Minh": 3}` | `[{"owner": "Lan", "total_hours": 9}]` | dòng 5 `T04` `[invalid_hours]`; dòng 6 `T02` `[duplicate_id]`; dòng 7 `T05` `[missing_owner]` |
| `workload.csv`, ngưỡng 9 | [`results/workload-max9.json`](results/workload-max9.json) | 0 | `{"Lan": 9, "Minh": 3}` | `[]` | giống ngưỡng 8 |
| `workload-edge.csv`, ngưỡng 0 | [`results/workload-edge-max0.json`](results/workload-edge-max0.json) | 0 | `{"Minh": 0}` | `[]` | dòng 2 `E01` `[invalid_hours]`; dòng 3 `E01` `[duplicate_id]` (không cộng 5 giờ cho Lan) |
| File không tồn tại / thiếu `--max-hours` / `--max-hours -1` | [`results/error-cases.txt`](results/error-cases.txt) | 1 / 2 / 2 | stdout rỗng, lỗi ở stderr | | |

Các trường chất lượng cũ vẫn tính trên toàn bộ 6 dòng: `row_count=6`, `missing_owner_count=1`, `invalid_hours_count=1`, `duplicate_ids=["T02"]`.

Pytest (Windows, Python 3.12): `tests/test_check_csv.py`, `test_skill_catalog.py`, `test_project.py` gồm **34 passed**. Các test của tool `bash` (`test_bash.py`, 2 test trong `test_agent.py`) và 2 test symlink cần môi trường POSIX theo README của lab, nên lỗi trên Windows. Lab gốc cũng lỗi y như vậy. Lệnh của skill đã được chạy lại bằng `bash -c` trong WSL Ubuntu từ thư mục workspace: ra đúng JSON và exit 1 khi file không tồn tại.

## 3. Stage 03: tính tổng giờ bằng Python qua Bash

Prompt gửi stage 03:

> Dùng Python qua Bash để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Cho biết cách xử lý dòng lỗi và task_id trùng.

- **[TRACE]** `block-2/stage-03-bash/traces/<file>.jsonl`: seq `<n>` `tool_started bash` với command `<dán lệnh>`; seq `<n>` `tool_finished` có stdout `<dán>`.
- Kết quả agent: `<Lan = ? giờ, Minh = ? giờ>`.

Đối chiếu (đã chạy trong WSL trên đúng file này):

| Cách tính | Kết quả |
|---|---|
| Không loại trùng, chỉ bỏ hours không phải số | `{'Lan': 14.0, 'Minh': 3.0, '': 2.0}` |
| Giữ lần đầu của `task_id`, bỏ dòng lỗi | `{'Lan': 9.0, 'Minh': 3.0}` |

- **Nếu Lan = 14 giờ**: dòng bị cộng trùng là **dòng 6 `T02,Lan,5`**. `T02` đã xuất hiện ở dòng 3 nên 5 giờ bị cộng hai lần (4 + 5 + 5). Dạng lệnh này thường còn cộng 2 giờ của dòng 7 cho owner rỗng `''`.
- **Nếu Lan = 9 giờ**: chỉ ra đoạn lệnh loại trùng trong command của trace, thường có dạng `if tid in seen: continue` rồi `seen.add(tid)`, hoặc `drop_duplicates('task_id', keep='first')`. Kiểm tra thêm là đoạn đó giữ **lần đầu** chứ không phải "lần hợp lệ đầu tiên", và dòng 5 (`abc`) cùng dòng 7 (owner rỗng) bị loại.
- `<Ghi nhận xét: cách agent tự xử lý không ổn định giữa các lần chạy/model. Đây là lý do stage 04 đưa thuật toán vào script.>`

## 4. Kết quả kiểm tra với agent (stage 04)

Prompt chính (cuộc trò chuyện mới, không nhắc tên skill/script):

> Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md.

| Trường hợp | Kết quả cần đạt | Kết quả thực tế | Bằng chứng trong trace |
|---|---|---|---|
| Ngưỡng 8 | Lan 9, Minh 3; chỉ Lan quá tải; loại dòng 5 `invalid_hours`, 6 `duplicate_id`, 7 `missing_owner` | `<điền>` | **[TRACE]** `<file>`: seq `<n>` `read_file skills/csv-quality/SKILL.md`; seq `<n>` `bash` command `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8`, `exit_code=0`, stdout JSON; seq `<n>` `read_file .../report-template.md`; seq `<n>` `write_file output/workload.md`. Báo cáo: `workspace/output/workload.md` (`<lưu bản copy, ví dụ results/workload-report-max8.md>`) |
| Ngưỡng 9 | Tổng giờ và dòng bị loại không đổi; không ai quá tải | `<điền>` | **[TRACE]** `<file>`: command có `--max-hours 9`; JSON `overloaded_owners: []` |
| Không cung cấp ngưỡng | Hỏi ngưỡng trước khi kết luận | `<điền>` | **[TRACE]** `<file>`: có `read_file SKILL.md`; **không** có `bash` chạy script với ngưỡng tự chọn; câu trả lời hỏi ngưỡng |
| File không tồn tại | stderr + exit ≠ 0; agent báo không phân tích được | `<điền>` | **[TRACE]** `<file>`: `bash` → `exit_code=1`, stderr `ERROR: Không đọc được file ...`; không có `write_file` báo cáo như khi thành công |

Prompt cho trường hợp thiếu ngưỡng: `Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải.`
Prompt gợi ý cho file không tồn tại: `Kiểm tra data/workload-missing.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload-missing.md.`

Lưu ý: chạy ngưỡng 9 ở cuộc trò chuyện mới và ghi báo cáo vào file khác (ví dụ `output/workload-9.md`) để không ghi đè báo cáo ngưỡng 8.

## 5. Câu hỏi cuối bài

**Phần nào do script tính, phần nào do model diễn giải?**

- **Script (tất định, kiểm thử được)**: đọc và parse CSV, kiểm tra header và cột bắt buộc, chuẩn hóa khoảng trắng, xác định dòng hợp lệ, loại trùng theo lần xuất hiện đầu, gán mã lý do và thứ tự lý do, cộng tổng giờ theo người, so với ngưỡng (`>`), sắp xếp, toàn bộ thống kê chất lượng, và mã thoát (0 thành công, 1 lỗi input, 2 sai tham số).
- **Model**: nhận ra yêu cầu khớp skill; trích ngưỡng từ câu hỏi của người dùng (hoặc hỏi lại khi thiếu); dựng lệnh với đúng `--input` và `--max-hours`; đọc `exit_code`/`stderr` để phân biệt thành công với lỗi thực thi; ánh xạ các trường JSON vào template; diễn giải mã lý do bằng ngôn ngữ tự nhiên (ví dụ "dòng 6 trùng T02 với dòng 3"); viết phần đánh giá và khuyến nghị; trả lời tóm tắt. Model **không** tự cộng hay tự loại dòng.

**Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu gì?**

- **Lệnh sai**: `SKILL.md` cũ chạy `check_csv.py --input ...` không có `--max-hours`, nên script trả exit 2. Theo skill cũ thì "exit 1 là lỗi thực thi", còn exit 2 không được mô tả, nên agent có thể báo lỗi khó hiểu, đoán kết quả, hoặc tự thêm một ngưỡng tùy ý.
- **Ngưỡng sai**: skill cũ không bảo hỏi lại khi thiếu ngưỡng và không cấm dùng ngưỡng cũ, nên agent có thể tự chọn (ví dụ 8) hoặc lấy ngưỡng từ cuộc trò chuyện trước.
- **Mâu thuẫn quy tắc**: skill cũ có quy tắc "Không tính tổng giờ hay KPI khi còn dữ liệu lỗi". Agent có thể từ chối báo tổng giờ dù script đã tính đúng trên các dòng hợp lệ, hoặc tự tính lại bằng tay và ra Lan 14 giờ.
- **Báo cáo thiếu**: template cũ không có mục ngưỡng, tổng giờ theo người, người vượt ngưỡng hay dòng bị loại. Báo cáo sẽ thiếu đúng những thông tin người dùng hỏi, hoặc model tự chế cấu trúc không ổn định giữa các lần.
- **Diễn giải sai trường mới**: skill cũ không mô tả `excluded_rows`, `reasons`, quy tắc "bằng ngưỡng không phải quá tải" và "giữ lần đầu kể cả khi lần đầu không hợp lệ". Model dễ hiểu nhầm, ví dụ coi Lan 9 giờ là quá tải với ngưỡng 9, hoặc cho rằng 5 giờ của `E01` ở dòng 3 nên được cộng.

Kết luận: script, skill và reference là một hợp đồng chung. Script đổi đầu vào/đầu ra thì hướng dẫn gọi lệnh và mẫu báo cáo phải đổi theo, nếu không agent chạy sai lệnh hoặc diễn giải sai kết quả đúng.
