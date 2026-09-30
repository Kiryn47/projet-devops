FROM python:3.12.7-slim AS build
RUN python -m venv /venv
COPY config/requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12.7-slim
RUN useradd --system app
WORKDIR /app
COPY --from=build /venv /venv
COPY app.py .
ARG APP_VERSION=dev
ARG GIT_SHA=unknown
ENV APP_VERSION=$APP_VERSION GIT_SHA=$GIT_SHA PATH="/venv/bin:$PATH"
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["gunicorn", "-b", "0.0.0.0:8001", "--workers", "1", "--threads", "4", "app:create_app()"]
