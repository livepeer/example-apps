# Hello-world example app.
#
# Requires the livepeer-gateway SDK, which is not yet on PyPI, so it is
# installed straight from the Git repo.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "livepeer-gateway @ git+https://github.com/livepeer/livepeer-python-gateway@ja/live-runner"

WORKDIR /app
COPY runner.py client.py ./

EXPOSE 5000

CMD ["python", "runner.py"]
