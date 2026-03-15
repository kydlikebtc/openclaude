"""轻量级 Mock Anthropic API 服务器，用于负载测试。

仅实现 POST /v1/messages，返回预设响应（无真实 LLM 调用）。
通过 MOCK_LATENCY_MS 环境变量模拟网络延迟（默认 10ms）。

启动方式:
    uvicorn tests.benchmarks.mock_anthropic_server:app --port 9999 --workers 4
"""

import asyncio
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock Anthropic API", docs_url=None, redoc_url=None)

_LATENCY_MS = int(os.getenv("MOCK_LATENCY_MS", "10"))


@app.post("/v1/messages")
async def messages(request: Request) -> JSONResponse:
    """模拟 Anthropic Messages API 响应，含可配置延迟。"""
    body = await request.json()
    model = body.get("model", "claude-haiku-4-5-20251001")
    messages_count = len(body.get("messages", []))
    input_tokens = max(10, messages_count * 15)
    output_tokens = int(body.get("max_tokens", 100) * 0.3)

    if _LATENCY_MS > 0:
        await asyncio.sleep(_LATENCY_MS / 1000)

    return JSONResponse(
        content={
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": "Mock response for load testing."}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "server": "mock-anthropic"}
