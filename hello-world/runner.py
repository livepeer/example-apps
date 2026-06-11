#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
from contextlib import suppress

from aiohttp import web

from livepeer_gateway.live_runner import LiveRunnerRegistration, register_runner

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
APP_ID = "livepeer-sample/hello-world"

log = logging.getLogger("hello-world")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live Runner hello-world demo.")
    parser.add_argument("--orchestrator", default="http://localhost:8935")
    parser.add_argument("--orchSecret", default="abcdef")
    parser.add_argument("--runner-url", default=f"http://{DEFAULT_HOST}:{DEFAULT_PORT}")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind address (use 0.0.0.0 in containers).")
    parser.add_argument("--price", type=int, default=0, help="Price in USD per pixels-per-unit (0 = free, the offchain default).")
    parser.add_argument("--pixels-per-unit", type=int, default=1, help="Scale factor: price is charged per this many units.")
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
        price_per_unit=args.price,
        pixels_per_unit=args.pixels_per_unit,
    )
    app["registration"] = registration
    log.info(
        "registered runner_id=%s orchestrator=%s",
        registration.runner_id,
        registration.orchestrator_url,
    )


async def _on_cleanup(app: web.Application) -> None:
    registration = app.get("registration")
    if isinstance(registration, LiveRunnerRegistration):
        with suppress(Exception):
            await registration.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = web.Application()
    app.router.add_post("/hello", _handle_hello)
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    # print=None suppresses aiohttp's stdout banner (which would block-buffer);
    # everything goes through logging, which flushes per record.
    web.run_app(app, host=_parse_args().host, port=DEFAULT_PORT, print=None)


if __name__ == "__main__":
    main()
