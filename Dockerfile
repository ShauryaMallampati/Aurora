FROM python:3.12-slim
WORKDIR /artifact
COPY . .
RUN python -m pip install --no-cache-dir ".[interfaces]"
CMD ["python", "artifact/scripts/run_artifact.py", "--mode", "smoke", "--output-dir", "/tmp/aurora-artifact"]
