"""调试：端到端复现，看每一步的 distance"""
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

BASE = "http://localhost:8000/api/v1"
USERNAME = os.getenv("NEXUS_TEST_USERNAME", "")
PASSWORD = os.getenv("NEXUS_TEST_PASSWORD", "")
TEST_DOC = Path(__file__).parent.parent.parent / "README.md"

if not USERNAME or not PASSWORD:
    raise RuntimeError("请先设置 NEXUS_TEST_USERNAME 和 NEXUS_TEST_PASSWORD")

# 1. 登录
tok = requests.post(f"{BASE}/auth/login", data={"username": USERNAME, "password": PASSWORD}).json()["data"]["access_token"]
h = {"Authorization": f"Bearer {tok}"}
print("登录OK")

# 2. 建知识库
kb = requests.post(f"{BASE}/knowledge-bases", json={"name": f"debug-{int(time.time())}", "chunk_strategy": "markdown", "chunk_size": 800, "chunk_overlap": 80}, headers=h).json()["data"]
kb_id = kb["id"]
print(f"KB id={kb_id}")

try:
    # 3. 上传
    p = TEST_DOC
    with p.open("rb") as f:
        upload = requests.post(f"{BASE}/knowledge-bases/{kb_id}/documents", files={"file": (p.name, f, "text/markdown")}, headers=h).json()["data"]
    task_id = upload["task"]["id"]
    print(f"上传 OK task_id={task_id}")

    # 4. 等任务完成
    for _ in range(30):
        s = requests.get(f"{BASE}/tasks/{task_id}", headers=h).json()["data"]
        if s["status"] == "success":
            print(f"任务完成 chunks={s['progress']}%")
            break
        if s["status"] == "failed":
            print(f"失败: {s['error_msg']}")
            sys.exit(1)
        time.sleep(1)

    # 5. 搜索 + 打印完整 distance
    for q in ["什么是 MCP 协议？", "MCP 协议层", "MCP"]:
        r = requests.post(f"{BASE}/knowledge-bases/{kb_id}/search", json={"query": q, "top_k": 5}, headers=h).json()["data"]
        print(f"\nQuery: {q}")
        for hit in r["hits"]:
            print(f"  distance={hit['score']:.4f}  {hit['content'][:50].replace(chr(10), ' ')}...")
finally:
    requests.delete(f"{BASE}/knowledge-bases/{kb_id}", headers=h)
    print("\n清理 OK")
