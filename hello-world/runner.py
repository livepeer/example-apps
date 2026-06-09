#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import suppress

from aiohttp import web

from livepeer_gateway.live_runner import LiveRunnerRegistration, register_runner

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
APP_ID = "livepeer-sample/hello-world"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live Runner hello-world demo.")
    parser.add_argument("--orchestrator", default="http://localhost:8935")
    parser.add_argument("--orchSecret", default="abcdef")
    parser.add_argument("--runner-url", default=f"http://{DEFAULT_HOST}:{DEFAULT_PORT}")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind address (use 0.0.0.0 in containers).")
    return parser.parse_args()


async def _handle_hello(request: web.Request) -> web.Response:
    payload = await request.json()
    name = str(payload.get("name", "world"))
    return web.json_response({"message": f"Hello, {name}!"})


async def _on_startup(app: web.Application) -> None:
    args = _parse_args()
    registration = await register_runner(
        args.orchestrator,
        secret=args.orchSecret,
        runner_url=args.runner_url,
        app=APP_ID,
    )
    app["registration"] = registration
    print(
        f"runner_id={registration.runner_id} orchestrator={registration.orchestrator_url}"
    )


async def _on_cleanup(app: web.Application) -> None:
    registration = app.get("registration")
    if isinstance(registration, LiveRunnerRegistration):
        with suppress(Exception):
            await registration.close()


def main() -> None:
    app = web.Application()
    app.router.add_post("/hello", _handle_hello)
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    web.run_app(app, host=_parse_args().host, port=DEFAULT_PORT)


if __name__ == "__main__":
    main()
