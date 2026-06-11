# Registrar that advertises the vLLM OpenAI server as a Live Runner.
# vLLM itself runs from the official `vllm/vllm-openai` image (see docker-compose.yml);
# this small container only calls register_runner + heartbeats. The gateway and
# OpenAI client are consumer-side and run on the host (see gateway.py / client.py).
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# livepeer-gateway SDK isn't on PyPI yet; install from Git.
RUN pip install --no-cache-dir \
    "livepeer-gateway @ git+https://github.com/livepeer/livepeer-python-gateway@ja/live-runner"

WORKDIR /app
COPY runner.py ./

CMD ["python", "runner.py"]
