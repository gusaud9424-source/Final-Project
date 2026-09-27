FROM python:3.12-slim
WORKDIR /sandbox
RUN useradd -m runner && mkdir -p /ipc && chown runner:runner /ipc
COPY runner.py /sandbox/runner.py
USER runner
CMD ["python3", "/sandbox/runner.py"]
