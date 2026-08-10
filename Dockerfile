# Python minor version을 고정해 local 환경과 분리된 실행 기준을 만든다.
FROM python:3.12-slim

# Python cache 파일을 줄이고 log가 terminal에 즉시 출력되게 한다.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# dependency layer를 먼저 만들면 source만 바뀔 때 설치 cache를 재사용할 수 있다.
COPY requirements.txt ./
RUN python -m pip install \
    --disable-pip-version-check \
    --no-cache-dir \
    -r requirements.txt

COPY src/ ./src/

# 실행 결과 경로를 준비하고 root 대신 전용 사용자로 작업을 실행한다.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/logs /app/artifacts \
    && chown -R appuser:appuser /app/logs /app/artifacts

USER appuser

CMD ["python", "src/run_job.py"]
