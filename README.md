# D05: Tool Use & Skill Use: bài luyện tập

Bài làm cho hai bài luyện tập của buổi D05 (Agentic AI Engineering):

- **Block 1: Tra cứu chính sách đúng phiên bản** (stage 00 → 02): tool `list_files` mới và skill `refund-policy`.
- **Block 2: Kiểm tra quá tải theo người** (stage 03 → 04): mở rộng `check_csv.py` với `--max-hours` và cập nhật skill `csv-quality`.

Các stage là **bản sao** của `agent-tools-skills-lab`; project mẫu không bị sửa.

## Cấu trúc

```
d05-tool-use-skill-use/
├── pyproject.toml              # uv workspace gồm 5 stage
├── scripts/trace_summary.py    # trích bằng chứng từ trace JSONL cho analysis.md
├── block-1/
│   ├── analysis.md
│   ├── results/                # kết quả gọi list_files trực tiếp
│   ├── stage-00-chat/          # không đổi code, chỉ dùng để quan sát giới hạn
│   ├── stage-01-files/         # + list_files, + data/policies
│   └── stage-02-skills/        # + list_files, + data/policies, + skills/refund-policy
└── block-2/
    ├── analysis.md
    ├── results/                # JSON chạy script trực tiếp (ngưỡng 8, 9, edge, lỗi)
    ├── stage-03-bash/          # + data/workload.csv
    └── stage-04-script-skill/  # + workload*.csv, csv-quality cập nhật, test mới
```

## Đối chiếu yêu cầu nộp bài

| Yêu cầu | Vị trí |
|---|---|
| B1: mã nguồn tool mới + đăng ký tool (stage 01, 02) | `block-1/stage-0{1,2}-*/tools/files.py` (`_list`, `list_files`), `tools/__init__.py`, `agent.py` (`TOOLS`) |
| B1: skill `refund-policy/` + 2 tài liệu chính sách | `block-1/stage-02-skills/workspace/skills/refund-policy/`, `.../workspace/data/policies/` (có bản trong `fixtures/`) |
| B1: trace A, B sau đổi tên, thiếu thông tin | `block-1/stage-02-skills/traces/` (sinh ra khi chạy app) |
| B1: `analysis.md` | [`block-1/analysis.md`](block-1/analysis.md) |
| B2: skill `csv-quality` (script, hướng dẫn, reference) + bản trong fixtures | `block-2/stage-04-script-skill/{workspace,fixtures}/skills/csv-quality/` |
| B2: CSV đầu vào + test tự động cho ID đầu có hours lỗi | `.../workspace/data/workload*.csv`, `tests/test_check_csv.py::test_first_occurrence_with_invalid_hours_still_claims_id` |
| B2: JSON chạy trực tiếp (8, 9, edge) | `block-2/results/` |
| B2: báo cáo agent + trace (8, 9, thiếu ngưỡng, file không tồn tại) | `block-2/stage-04-script-skill/workspace/output/`, `.../traces/` (sinh ra khi chạy app) |
| B2: `analysis.md` | [`block-2/analysis.md`](block-2/analysis.md) |

`.gitignore` của từng stage **không** bỏ qua `traces/` và `workspace/output/`, để trace và báo cáo được commit. `.env` luôn bị bỏ qua: **không commit API key**.

## Cài đặt

Cần Python 3.11+ và [uv](https://docs.astral.sh/uv/). Stage 03/04 cần `bash` POSIX: trên Windows chạy trong WSL2.

```bash
uv sync --all-packages
```

Mỗi stage cần `.env` riêng (copy từ `.env.example`, điền `OPENAI_API_KEY`, `MODEL_NAME`, tùy chọn `OPENAI_BASE_URL`).

```bash
cd block-1/stage-02-skills
cp -n .env.example .env
uv run streamlit run app.py
```

Test (không cần API key), chạy trong thư mục stage:

```bash
uv run pytest
```

## Trình tự chạy để lấy trace

**Block 1**

1. `block-1/stage-00-chat`: gửi câu hỏi trường hợp A, ghi nhận giới hạn.
2. `block-1/stage-02-skills`: tải lại trang, mở cuộc trò chuyện mới cho mỗi trường hợp:
   - A: `Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?`
   - B: `Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?`
   - Đổi tên hai file trong `workspace/data/policies/` (giữ nội dung), mở cuộc trò chuyện mới, chạy lại A và B.
   - Thiếu thông tin: `Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026.`

**Block 2** (WSL/Linux)

1. `block-2/stage-03-bash`: `Dùng Python qua Bash để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Cho biết cách xử lý dòng lỗi và task_id trùng.`
2. `block-2/stage-04-script-skill`, mỗi trường hợp một cuộc trò chuyện mới:
   - `Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md.`
   - Như trên với 9 giờ, ghi vào `output/workload-9.md`.
   - `Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải.`
   - `Kiểm tra data/workload-missing.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload-missing.md.`

> `reset_workspace.py` ghi đè `workspace/` từ `fixtures/`. Skill và dữ liệu đã có bản trong `fixtures/` nên reset không làm mất bài, nhưng sẽ xóa báo cáo trong `output/` và hoàn tác việc đổi tên file chính sách.

Sau khi chạy, trích bằng chứng để điền các mục **[TRACE]** trong `analysis.md`:

```bash
python scripts/trace_summary.py block-1/stage-02-skills/traces/
```
