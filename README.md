# Livepeer example apps

Example **apps** for the Livepeer network. An app is a container you build and put on the network: a normal HTTP or WebSocket service that exposes your endpoints. Orchestrators host and run your app via the **general runner**, and clients call it through the orchestrator using the [livepeer-gateway](https://github.com/livepeer/livepeer-python-gateway) Python SDK.

This repo starts with one example, [`hello-world`](./hello-world), the smallest possible app. More will follow.

## hello-world

A normal aiohttp service that exposes `POST /hello`, self-registers with an orchestrator (`register_runner`), and is then reachable through the orchestrator. It is the smallest end-to-end app: a single JSON HTTP endpoint, no video or streaming.

|              |                                      |
| ------------ | ------------------------------------ |
| App id       | `livepeer-sample/hello-world`        |
| Transport    | HTTP (JSON request/response)         |
| Registration | dynamic (self-registers via the SDK) |

General runners are not on go-livepeer `main` yet; they live on the `ja/live-runner` branch. Until it merges, both the orchestrator image and the SDK come from that branch.

## Prerequisites

- Docker for the end-to-end demo below. It uses the `livepeer/go-livepeer:ja-live-runner` image (a build of the branch), so there is nothing to install. For the local flow instead, run a [go-livepeer](https://github.com/livepeer/go-livepeer) orchestrator built from `ja/live-runner` with `-useLiveRunners`.
- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/) for the client.
- The `livepeer-gateway` SDK, installed from the `ja/live-runner` branch (not yet on PyPI):

```sh
pip install "git+https://github.com/livepeer/livepeer-python-gateway@ja/live-runner"
```

## Run it offchain

```bash
cd hello-world
docker compose up -d --build
uv run client.py --name livepeer --discovery https://localhost:8935/discovery
# {'message': 'Hello, livepeer!'}
docker compose down
```

`docker-compose.yml` brings up an orchestrator (`-useLiveRunners`) and the app. The app self-registers, the client discovers it via `/discovery`, reserves a session, calls `POST /hello` through the orchestrator, and prints the reply. The orchestrator service is defined once in `compose.orchestrator.yml` and pulled in with `extends`, so future examples reuse it without duplication.

## Notes

- Apps bind to `127.0.0.1` by default (safe for local runs). In a container the compose file passes `--host=0.0.0.0` so the orchestrator can reach the app.
- Orchestrators serve a self-signed TLS cert; the SDK skips verification.
