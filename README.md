# Projet DevOps

API Flask avec une base PostgreSQL, conteneurisée avec Docker, avec une CI/CD GitHub Actions et des métriques Prometheus.

## Lancer en local

```
cd application
cp .env.example .env        # mettre un mot de passe dans POSTGRES_PASSWORD
docker compose up -d --build
```

- API : http://localhost:8000/health
- Métriques : http://localhost:8000/metrics
- Prometheus : http://localhost:9090

Tests :

```
cd application
docker compose up -d db
pip install -r config/requirements.txt -r config/requirements-dev.txt
export DATABASE_URL=postgresql://app:<mot_de_passe>@localhost:5432/app
pytest
```

## Routes

- `GET /health` : 200 si la base répond, 503 sinon
- `GET /items` : liste des items
- `POST /items` : ajoute un item `{"name": "..."}`
- `GET /metrics` : métriques Prometheus

## CI

Sur chaque push et pull request : yamllint, flake8, tests pytest sur Python 3.11 et 3.12 avec un Postgres, build de l'image, puis `ci-ok` qui échoue si un job a échoué. `ci-ok` est le check obligatoire pour merger sur main.

## CD

Après une CI verte sur main (ou lancement manuel) : build et push de l'image sur ghcr.io avec les tags `latest`, SHA court et `1.0.<numéro de run>`, puis déploiement sur un runner self-hosted. Le job deploy vérifie `/health` avec curl (3 retries) et remet l'image précédente si ça échoue.

Secret à créer dans l'environnement `production` : `POSTGRES_PASSWORD`.

## Métriques et alertes

- `http_requests_total` : nombre de requêtes par endpoint et code
- `http_request_duration_seconds` : histogramme des durées par endpoint
- `app_version_info` : version et commit déployés

Alertes dans `application/prometheus/alerts.yml` :

- Plus de 5 % d'erreurs 5xx sur 5 minutes pendant 5 minutes. 5 % c'est déjà une requête sur 20 en erreur, et les 5 minutes évitent d'alerter pour un redémarrage rapide de la base. `/metrics` est exclu car Prometheus l'appelle tout le temps et ça fausserait le ratio.
- p95 au dessus de 500 ms pendant 10 minutes. Les requêtes normales sont sous 50 ms, donc 500 ms c'est une vraie dégradation. 10 minutes car des pics courts de latence sont normaux.
