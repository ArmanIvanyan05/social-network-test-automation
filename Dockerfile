FROM mcr.microsoft.com/playwright/python:v1.61.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /automation

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY conftest.py ./

RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "pytest"]
CMD ["tests/smoke", "-v"]
