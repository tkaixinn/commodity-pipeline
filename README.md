# commodity-pipeline

A Python data pipeline that ingests commodity futures price data, validates its quality, stores it in PostgreSQL, and runs automatically on a schedule via a Kubernetes CronJob.

## What it does

1. **Ingests** commodity futures price data (Crude Oil, Gold, Natural Gas) from Yahoo Finance
2. **Transforms** the raw data: standardizes columns, validates prices, flags and removes bad rows (missing values, invalid prices, duplicates)
3. **Loads** the cleaned data into PostgreSQL using an upsert pattern, so re-running the pipeline never creates duplicate rows
4. **Runs automatically** on a schedule via a Kubernetes CronJob, requiring no manual intervention

## Architecture

    Yahoo Finance API
          |
          v
      ingest.py          (pull raw price data)
          |
          v
      transform.py       (clean, validate, generate data quality summary)
          |
          v
      load.py            (upsert into PostgreSQL)
          |
          v
      PostgreSQL         (commodity_prices table)

The pipeline runs inside a Docker container, deployed to Kubernetes as a CronJob, connecting to a PostgreSQL Deployment also running inside the cluster.

    Kubernetes Cluster
    -------------------------------
    | CronJob                     |
    | (commodity-pipeline)        |
    |          |                  |
    |          v                  |
    | Postgres Deployment         |
    | + Service                   |
    -------------------------------

## Tech stack

- **Python**: pipeline logic
- **pandas**: data cleaning and transformation
- **yfinance**: data source
- **PostgreSQL**: storage
- **Docker**: containerization
- **Kubernetes (minikube)**: scheduled orchestration via CronJob

## Data quality checks

Every pipeline run tracks and reports:
- Rows with missing critical price fields
- Rows with invalid prices (zero or negative)
- Duplicate ticker + date rows

A summary is logged after each run, e.g.:

    Final data quality summary: {'total_rows_received': 15, 'rows_missing_price_data': 0, 'rows_with_invalid_prices': 0, 'duplicate_rows_dropped': 0, 'total_rows_clean': 15, 'rows_dropped_total': 0}

## Local setup

1. Clone the repo and set up a virtual environment:

        git clone https://github.com/tkaixinn/commodity-pipeline.git
        cd commodity-pipeline
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

2. Create a `.env` file:

        DB_HOST=localhost
        DB_PORT=5432
        DB_NAME=commodity_data
        DB_USER=kaixin
        DB_PASSWORD=localdevpassword

3. Start Postgres and run the pipeline via Docker Compose:

        docker compose up --build

## Running on Kubernetes (minikube)

1. Start minikube and load the image:

        minikube start
        docker build -t commodity-pipeline .
        minikube image load commodity-pipeline:latest

2. Deploy Postgres:

        kubectl apply -f k8s/postgres.yaml

3. Create the schema inside the Postgres pod:

        kubectl cp db/schema.sql <postgres-pod-name>:/tmp/schema.sql
        kubectl exec -it <postgres-pod-name> -- psql -U kaixin -d commodity_data -f /tmp/schema.sql

4. Deploy the CronJob:

        kubectl apply -f k8s/cronjob.yaml

The pipeline will now run automatically every 10 minutes. To trigger a manual test run:

        kubectl create job --from=cronjob/commodity-pipeline manual-test
        kubectl logs -l job-name=manual-test

## Project structure

    commodity-pipeline/
    ├── src/
    │   ├── ingest.py
    │   ├── transform.py
    │   ├── load.py
    │   └── pipeline.py
    ├── db/
    │   └── schema.sql
    ├── k8s/
    │   ├── postgres.yaml
    │   └── cronjob.yaml
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    └── .env.example