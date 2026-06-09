# Hello-world app

The smallest possible general-runner app: a batch request/response over HTTP. It self-registers with an orchestrator and exposes `POST /hello`, which takes `{"name": "..."}` and returns `{"message": "Hello, <name>!"}`. This is the most common app shape (synchronous inference), with no video, WebSocket, or streaming machinery.

|              |                                      |
| ------------ | ------------------------------------ |
| App id       | `livepeer-sample/hello-world`        |
| Mode         | persistent                           |
| Registration | dynamic (self-registers via the SDK) |
| Port         | 5000                                 |

## Run locally

Start an orchestrator with general runners enabled:

```sh
./livepeer -orchestrator -useLiveRunners -serviceAddr localhost:8935 -v 99 -orchSecret abcdef
```

Start the app:

```sh
uv run runner.py --orchestrator http://localhost:8935 --orchSecret abcdef
```

Call it through the orchestrator with the SDK:

```sh
uv run client.py --name livepeer
# {'message': 'Hello, livepeer!'}
```

The client discovers the `livepeer-sample/hello-world` app, reserves a session, calls `POST /hello`, prints the reply, and releases the session.

## Run end-to-end with Docker

`docker-compose.yml` brings up an orchestrator and this app together (offchain):

```sh
docker compose up -d --build
uv run client.py --name livepeer --discovery https://localhost:8935/discovery
# {'message': 'Hello, livepeer!'}
docker compose down
```
