FROM python:3.12-slim
# iputils-ping: DVWA Command Injection 실습(ping 도구) 재현용
RUN apt-get update \
    && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /sandbox
RUN useradd -m runner && mkdir -p /ipc && chown runner:runner /ipc
COPY runner.py /sandbox/runner.py
USER runner
CMD ["python3", "/sandbox/runner.py"]
