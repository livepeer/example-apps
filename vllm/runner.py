#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from contextlib import suppress

from livepeer_gateway.live_runner import register_runner

DEFAULT_RUNNER_URL = "http://localhost:8000"
APP_ID = "vllm/qwen2.5-0.5b-instruct"

log = logging.getLogger("vllm-runner")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advertise a vLLM OpenAI server as a Live Runner.")
    parser.add_argument("--orchestrator", default="http://localhost:8935")
    parser.add_argument("--orchSecret", default="abcdef")
    parser.add_argument("--runner-url", default=DEFAULT_RUNNER_URL,
                        help="URL of the vLLM OpenAI server the orchestrator proxies to.")
    parser.add_argument("--price", type=int, default=0, help="Price in USD per pixels-per-unit (0 = free).")
    parser.add_argument("--pixels-per-unit", type=int, default=1, help="Scale factor for the price.")
    return parser.parse_args()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args()

    # vLLM serves the API; this process only registers it and keeps the heartbeat
    # alive. The orchestrator proxies client requests to --runner-url (vLLM).
    registration = await register_runner(
        args.orchestrator,
        secret=args.orchSecret,
        runner_url=args.runner_url,
        app=APP_ID,
        price_per_unit=args.price,
        pixels_per_unit=args.pixels_per_unit,
    )
    log.info(
        "registered runner_id=%s app=%s runner_url=%s",
        registration.runner_id,
        APP_ID,
        args.runner_url,
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)

    try:
        await stop.wait()  # heartbeat runs in the background; stay alive
    finally:
        with suppress(Exception):
            await registration.close()


if __name__ == "__main__":
    asyncio.run(main())
