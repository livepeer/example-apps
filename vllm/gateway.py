#!/usr/bin/env python3
"""Minimal local OpenAI -> Livepeer gateway.

A lightweight, single-app process you run on your host. Exposes a normal OpenAI
endpoint on localhost and forwards each request through the orchestrator to the
vLLM runner, doing Livepeer's discovery + payment handshake behind the scenes.
Point ANY OpenAI client at it -- no code changes, any language -- and it works
on-chain:

    uv run gateway.py --signer http://localhost:7936 &
    export OPENAI_BASE_URL=http://localhost:8080/v1 OPENAI_API_KEY=unused
    # then plain `openai`, curl, or any SDK just works

Each request: reserve a session, forward the body, release the session. call_runner
does the 402 payment challenge internally, so the client never sees discovery or
payment. (Release matters: the runner has capacity 1, so an unreleased session
would block the next call.)
"""
from __future__ import annotations

import argparse
import logging
from contextlib import suppress

from aiohttp import web

from livepeer_gateway.live_runner import call_runner, stop_runner_session
from livepeer_gateway.selection import reserve_session

APP_ID = "vllm/qwen2.5-0.5b-instruct"

log = logging.getLogger("vllm-gateway")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenAI-compatible gateway in front of a vLLM Live Runner.")
    parser.add_argument("--discovery", default="https://localhost:8935/discovery")
    parser.add_argument("--signer", default="", help="Remote signer base URL; omit for the offchain (free) path.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args()
    signer_url = args.signer.strip() or None

    async def _forward(request: web.Request) -> web.Response:
        session = await reserve_session(discovery_url=args.discovery, app=APP_ID, signer_url=signer_url)
        try:
            result = await call_runner(
                runner_url=session.app_url.rstrip("/") + request.path,  # e.g. .../app + /v1/chat/completions
                payload=await request.json(),
                signer_url=signer_url,
            )
            # TODO(streaming): this buffers the whole response, so OpenAI stream=True
            # (text/event-stream) is collected into one blob -- call_runner reads the
            # full body via request_json. True SSE passthrough needs a streaming variant
            # of call_runner in the SDK (e.g. stream=True returning a chunk iterator);
            # the gateway would then pipe chunks into a web.StreamResponse.
            return web.json_response(result.data)
        finally:
            with suppress(Exception):
                await stop_runner_session(session)

    app = web.Application()
    app.router.add_post("/v1/{tail:.*}", _forward)  # forward every OpenAI path
    log.info("gateway on http://%s:%d/v1 -> %s (signer=%s)", args.host, args.port, args.discovery, signer_url or "none")
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
