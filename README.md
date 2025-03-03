# Airflow, Docker, and Python Setup
Apache Airflow is a powerful workflow automation tool used for scheduling, monitoring, and managing workflows. Running Airflow in Docker provides a containerized, easy-to-maintain environment. This guide will help you set up Airflow using Docker and configure Python scripts with AWS for seamless workflow execution.

## Prerequisites
Ensure you have the following installed on your system:

### 1. Install Docker Desktop (includes Docker & Docker Compose v2)
Run this command in the terminal:
```sh
brew install --cask docker
```

### 2. Start Docker Desktop
Verify installation:
```sh
docker --version
docker compose version
```

## Setup Airflow with Docker

### Step 1: Clone the Official Apache Airflow Docker Repo
```sh
git clone https://github.com/apache/airflow.git
cd airflow
```

### Step 2: Set Up the Environment
Create an `.env` file to define environment variables:
```sh
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### Step 3: Initialize Airflow
Run the following command to set up the database and create default users:
```sh
docker-compose up airflow-init
```

### Step 4: Start Airflow
```sh
docker-compose up -d
```

### Step 5: Access the Airflow Web UI
Open [http://localhost:8080](http://localhost:8080) in your browser.
Login with:
- **Username:** airflow
- **Password:** airflow

### Create Your Own Credentials to Login
Run the following commands:
```sh
docker exec -it <AIRFLOW_WEBSERVER_CONTAINER_ID> bash
```
```sh
airflow users create \
    --username YOUR_USERNAME \
    --firstname YOUR_FIRSTNAME \
    --lastname YOUR_LASTNAME \
    --role Admin \
    --email YOUR_EMAIL \
    --password YOUR_P
