import os
import time

import psycopg
from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUESTS = Counter("http_requests_total", "Nombre de requêtes", ["endpoint", "code"])
LATENCY = Histogram(
    "http_request_duration_seconds",
    "Durée des requêtes",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
VERSION = Gauge("app_version_info", "Version déployée", ["version", "commit"])


def get_db(url):
    return psycopg.connect(url, connect_timeout=2)


def create_app(database_url=None, init_db=True):
    app = Flask(__name__)
    db_url = database_url or os.environ["DATABASE_URL"]

    VERSION.labels(os.getenv("APP_VERSION", "dev"), os.getenv("GIT_SHA", "unknown")).set(1)

    if init_db:
        with get_db(db_url) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS items (id SERIAL PRIMARY KEY, name TEXT NOT NULL)")

    @app.before_request
    def start_timer():
        g.start = time.perf_counter()

    @app.after_request
    def save_metrics(response):
        endpoint = request.url_rule.rule if request.url_rule else "unknown"
        LATENCY.labels(endpoint).observe(time.perf_counter() - g.start)
        REQUESTS.labels(endpoint, str(response.status_code)).inc()
        return response

    @app.get("/health")
    def health():
        try:
            with get_db(db_url) as conn:
                conn.execute("SELECT 1")
        except psycopg.Error:
            return jsonify(status="ko"), 503
        return jsonify(status="ok")

    @app.get("/items")
    def list_items():
        with get_db(db_url) as conn:
            rows = conn.execute("SELECT id, name FROM items ORDER BY id").fetchall()
        return jsonify([{"id": r[0], "name": r[1]} for r in rows])

    @app.post("/items")
    def add_item():
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        if not name:
            return jsonify(error="name manquant"), 400
        with get_db(db_url) as conn:
            row = conn.execute("INSERT INTO items (name) VALUES (%s) RETURNING id", (name,)).fetchone()
        return jsonify(id=row[0], name=name), 201

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)

    return app
