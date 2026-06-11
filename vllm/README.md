# vLLM app (OpenAI-compatible LLM)

Runs an OpenAI-compatible LLM on the Livepeer network and consumes it with the **unmodified `openai` library**. The official `vllm/vllm-openai` image serves the model; a small **registrar** (`runner.py`) advertises it to an orchestrator, which reverse-proxies OpenAI requests to it. A lightweight **local gateway** (`gateway.py`) runs on your host and does Livepeer's discovery + payment, so the client is plain OpenAI code that knows nothing about Livepeer.

|              |                                          |
| ------------ | ---------------------------------------- |
| App id       | `vllm/qwen2.5-0.5b-instruct`             |
| Transport    | HTTP (OpenAI `/v1/chat/completions`)     |
| Registration | dynamic (registrar self-registers vLLM)  |
| Port         | 8000 (vLLM), 8080 (gateway)              |

**Requires an NVIDIA GPU** for vLLM. The default model (`Qwen/Qwen2.5-0.5B-Instruct`) is tiny so it fits a modest card; override with `VLLM_MODEL`. Prerequisites (Docker, `uv`, the not-yet-released SDK) and the shared on-chain/payment setup are in the [repo README](../README.md).

## How it's wired

Two sides, split on the natural boundary:

- **Network (compose):** `orchestrator` + `vllm` (serves `/v1/...`) + `runner` (registers `runner_url=http://vllm:8000` and heartbeats). On-chain adds a `signer`.
- **Consumer (host):** the local gateway (`gateway.py`) — an OpenAI endpoint on `:8080` that reserves a session, forwards the request through the orchestrator, and (on-chain) pays via the signer — plus any OpenAI client (`client.py`, another SDK, `curl`) pointed at it.

The local gateway is a *client-side* component, so it runs on the host like the client, not in the infra compose.

## Run offchain (free)

```sh
docker compose up -d --build          # first run pulls the vLLM image + model (slow)
uv run gateway.py &                    # OpenAI endpoint on http://localhost:8080/v1
uv run client.py --prompt "In one sentence, what is Livepeer?"
kill %1; docker compose down           # stop the gateway, then the stack
```

`client.py` is stock `openai` with `base_url=http://localhost:8080/v1` (the `api_key` is ignored — it just needs *a* value). Pass a `--model` that matches `VLLM_MODEL`, the name vLLM serves under. Any OpenAI tool works the same way — e.g. `curl`:

```sh
curl http://localhost:8080/v1/chat/completions \
  -d '{"model":"Qwen/Qwen2.5-0.5B-Instruct","messages":[{"role":"user","content":"hi"}]}'
```

## Run on-chain (paid)

Layer `docker-compose.onchain.yml` to add a remote signer and run the orchestrator on-chain, so vLLM advertises a price and the gateway pays per call. Needs an Ethereum RPC, a funded signer wallet (deposit + reserve), and an orchestrator wallet — see [On-chain (paid) setup](../README.md#on-chain-paid-setup) in the repo README.

```sh
cp .env.example .env   # fill in RPC, network, keystore paths, accounts, pricing
docker compose -f docker-compose.yml -f docker-compose.onchain.yml up -d --build
uv run gateway.py --signer http://localhost:7936 &     # gateway pays per request
uv run client.py --prompt "In one sentence, what is Livepeer?"
kill %1; docker compose -f docker-compose.yml -f docker-compose.onchain.yml down
```

The client is **unchanged** — only the gateway gets `--signer`. The registrar advertises a price (`PRICE_PER_UNIT` / `PIXELS_PER_UNIT` from `.env`), the orchestrator advertises it in `/discovery`, and the gateway pays through the remote signer. That's the full paid stack (vLLM + orchestrator + signer + gateway), and the consumer never sees discovery or payment.
