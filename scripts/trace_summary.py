#!/usr/bin/env python3
"""Tóm tắt một hoặc nhiều file trace JSONL để lấy bằng chứng cho analysis.md (chỉ dùng stdlib).

Cách chạy (từ thư mục gốc package):
    python scripts/trace_summary.py block-1/stage-02-skills/traces/<file>.jsonl
    python scripts/trace_summary.py block-1/stage-02-skills/traces/          # mọi trace trong thư mục

In ra: câu hỏi, tools/skills có trong request, từng tool call (sequence, tên, tham số, kết quả rút gọn),
và các tool message có trong history ở model_request cuối (để chứng minh nội dung skill/reference đã vào context).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CLIP = 160


def clip(text: str, limit: int = CLIP) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "…"


def short_result(result) -> str:
    if not isinstance(result, dict):
        return clip(result)
    if result.get("ok") is False and "error" in result:
        return f"ERROR {result['error'].get('code')}: {clip(result['error'].get('message', ''))}"
    if "entries" in result:
        return "entries=" + ", ".join(e.get("path", "?") for e in result["entries"])
    if "content" in result:
        return f"path={result.get('path')} content={clip(result['content'], 100)}"
    if "exit_code" in result:
        out = clip(result.get("stdout", ""), 100)
        err = clip(result.get("stderr", ""), 100)
        return f"exit_code={result['exit_code']} stdout={out!r} stderr={err!r}"
    return clip(json.dumps(result, ensure_ascii=False))


def summarize(path: Path) -> None:
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not events:
        return
    first = events[0]
    print(f"=== {path.as_posix()}")
    print(f"project={first.get('project_name')} conversation={first.get('conversation_id', '')[:8]} turn={first.get('chat_turn')}")
    for e in events:
        kind = e.get("type")
        seq = e.get("sequence")
        if kind == "user_submitted":
            print(f"  [{seq}] user: {clip(e.get('text', ''), 500)}")
            print(f"        tools={e.get('tools')} skills={e.get('skills')}")
        elif kind == "tool_started":
            print(f"  [{seq}] tool_started {e.get('tool_name')} {clip(json.dumps(e.get('arguments'), ensure_ascii=False), 300)}")
        elif kind == "tool_finished":
            print(f"  [{seq}] tool_finished {e.get('tool_name')} status={e.get('status')} -> {short_result(e.get('result'))}")
        elif kind == "model_response":
            names = [c.get("name") for c in e.get("tool_calls_requested") or []]
            print(f"  [{seq}] model_response #{e.get('model_call_index')} tool_calls={names}")
        elif kind in ("run_completed", "run_failed", "run_error"):
            extra = {k: v for k, v in e.items() if k not in {"project_name", "conversation_id", "run_id", "chat_turn", "sequence", "type", "timestamp"}}
            print(f"  [{seq}] {kind} {json.dumps(extra, ensure_ascii=False)}")
    requests = [e for e in events if e.get("type") == "model_request"]
    if requests:
        last = requests[-1]
        snapshot = last.get("snapshot") or {}
        tool_names = [t.get("name") for t in snapshot.get("tools") or []]
        print(f"  model_request cuối [seq {last.get('sequence')}] model={snapshot.get('model_name')} tools schema={tool_names}")
        for message in snapshot.get("messages") or []:
            if message.get("role") == "tool":
                print(f"     history tool:{message.get('name')} -> {clip(message.get('content', ''), 120)}")
    print()


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    for arg in argv:
        target = Path(arg)
        files = sorted(target.glob("*.jsonl")) if target.is_dir() else [target]
        for file in files:
            summarize(file)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
