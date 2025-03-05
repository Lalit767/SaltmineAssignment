# Use official Airflow image
FROM apache/airflow:2.7.2

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow

# Install additional dependencies if needed
RUN pip install --no-cache-dir apache-airflow-providers-amazon

# Copy the Airflow configuration file (Modify this if needed)
COPY airflow.cfg ${AIRFLOW_HOME}/airflow.cfg

# Copy DAGs and requirements
COPY dags/ ${AIRFLOW_HOME}/dags/
COPY requirements.txt ${AIRFLOW_HOME}/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r ${AIRFLOW_HOME}/requirements.txt

# Set proper permissions
RUN chmod -R 755 ${AIRFLOW_HOME}

# Set default command to start Airflow webserver
CMD ["airflow", "webserver"]
