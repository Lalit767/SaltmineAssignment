Airflow, Docker, and Python Setup

Apache Airflow is a powerful workflow automation tool used for scheduling, monitoring, and managing workflows. Running Airflow in Docker provides a containerized, easy-to-maintain environment. This guide will help you set up Airflow using Docker and configure Python scripts with AWS for seamless workflow execution.

Prerequisites

Ensure you have the following installed on your system:

1. Install Docker Desktop (includes Docker & Docker Compose v2)

Run this command in the terminal:

brew install --cask docker

2. Start Docker Desktop

Verify installation:

docker --version
docker compose version

Setup Airflow with Docker

Step 1: Clone the Official Apache Airflow Docker Repo

git clone https://github.com/apache/airflow.git
cd airflow

Step 2: Set Up the Environment

Create an .env file to define environment variables:

echo -e "AIRFLOW_UID=$(id -u)" > .env

Step 3: Initialize Airflow

Run the following command to set up the database and create default users:

docker-compose up airflow-init

Step 4: Start Airflow

docker-compose up -d

Step 5: Access the Airflow Web UI

Open http://localhost:8080 in your browser.
Login with:

Username: airflow

Password: airflow

Create Your Own Credentials to Login

Run the following commands:

docker exec -it <AIRFLOW_WEBSERVER_CONTAINER_ID> bash

airflow users create \
    --username YOUR_USERNAME \
    --firstname YOUR_FIRSTNAME \
    --lastname YOUR_LASTNAME \
    --role Admin \
    --email YOUR_EMAIL \
    --password YOUR_PASSWORD

Common Airflow Docker Commands

View logs of a container:

docker-compose logs -f airflow-webserver

Restart Airflow:

docker-compose restart

Stop Airflow:

docker-compose down

Check running containers:

docker ps

Setup AWS Credentials Locally to Test Python Logic Scripts

Step 1: Verify AWS CLI installation

aws --version

Step 2: Configure AWS Credentials

aws configure

Step 3: Check the stored credentials

cd ~/.aws/credentials
cat credentials

Step 4: Add Access Key & Secret Key

Edit the credentials file:

[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

Setup AWS Resources

Step 1: Create AWS Account

Sign up at AWS

Step 2: Create an IAM Role

Assign necessary permissions

Step 3: Copy Secret Key for Future Reference

Store it securely using AWS Secrets Manager

Step 4: Create AWS Redshift Cluster & S3 Buckets

Set up S3 buckets for ingestion, processing, and final results

Launch a Redshift Cluster

Step 5: Assign IAM Role Access

Provide S3 full permissions

Grant Glue Catalog table permissions

Step 6: Create AWS Glue Crawler

Crawl data from the processed S3 bucket to the Glue Catalog

Ensure IAM Role has proper permissions

Step 7: Create Redshift Table

Use Amazon Spectrum to query external Glue tables

This setup ensures a smooth workflow for Airflow, AWS, and Python scripts. 🚀

