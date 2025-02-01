# **Apache Airflow with Docker: Data Science Project**

This guide walks you through setting up and running Apache Airflow using Docker for a data science project. It includes instructions for defining a DAG, running tasks, and monitoring workflows in the Airflow UI.

---

## **Prerequisites**
1. **Docker**: Install Docker Desktop from [here](https://www.docker.com/products/docker-desktop).
2. **Docker Compose**: Ensure Docker Compose is installed (it comes with Docker Desktop).
3. **Python Libraries**: The required libraries (`pandas`, `scikit-learn`, `joblib`) are installed automatically via the `docker-compose.yml` file.

---

## **Setup**

### **1. Clone the Project**
Clone or create a project directory with the following structure:
```
airflow-project/
├── dags/
│   └── iris_pipeline.py
├── data/
├── models/
├── results/
├── logs/
├── docker-compose.yml
└── .env
```

---

### **2. Create `docker-compose.yml`**
Create a `docker-compose.yml` file with the following content:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  redis:
    image: redis:7.2-bookworm
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 30s
      retries: 50
      start_period: 30s
    restart: always

  airflow-webserver:
    image: apache/airflow:2.10.4
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
      AIRFLOW__CORE__FERNET_KEY: ''
      AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
      AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
      _PIP_ADDITIONAL_REQUIREMENTS: "pandas scikit-learn joblib"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./data:/opt/airflow/data
      - ./models:/opt/airflow/models
      - ./results:/opt/airflow/results
    ports:
      - "8080:8080"
    restart: always
    depends_on:
      - postgres
      - redis

  airflow-scheduler:
    image: apache/airflow:2.10.4
    environment:
      <<: *airflow-common-env
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./data:/opt/airflow/data
      - ./models:/opt/airflow/models
      - ./results:/opt/airflow/results
    restart: always
    depends_on:
      - airflow-webserver

volumes:
  postgres-db-volume:
```

---

### **3. Create `.env` File**
Create a `.env` file to set environment variables:
```plaintext
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=admin
```

---

### **4. Create the DAG**
Create a file `dags/iris_pipeline.py` with the following content:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Define functions for each task
def download_dataset():
    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df['target'] = iris.target
    df.to_csv('/opt/airflow/data/iris.csv', index=False)

def preprocess_data():
    df = pd.read_csv('/opt/airflow/data/iris.csv')
    X = df.drop('target', axis=1)
    y = df['target']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    X_train.to_csv('/opt/airflow/data/X_train.csv', index=False)
    X_test.to_csv('/opt/airflow/data/X_test.csv', index=False)
    y_train.to_csv('/opt/airflow/data/y_train.csv', index=False)
    y_test.to_csv('/opt/airflow/data/y_test.csv', index=False)

def train_model():
    X_train = pd.read_csv('/opt/airflow/data/X_train.csv')
    y_train = pd.read_csv('/opt/airflow/data/y_train.csv')
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train.values.ravel())
    joblib.dump(model, '/opt/airflow/models/iris_model.pkl')

def evaluate_model():
    X_test = pd.read_csv('/opt/airflow/data/X_test.csv')
    y_test = pd.read_csv('/opt/airflow/data/y_test.csv')
    model = joblib.load('/opt/airflow/models/iris_model.pkl')
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    with open('/opt/airflow/results/accuracy.txt', 'w') as f:
        f.write(f'Model Accuracy: {accuracy:.2f}')

# Define the DAG
with DAG(
    dag_id='iris_pipeline',
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',
    catchup=False,
) as dag:

    # Define tasks
    download_task = PythonOperator(
        task_id='download_dataset',
        python_callable=download_dataset,
    )

    preprocess_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_data,
    )

    train_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
    )

    evaluate_task = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
    )

    # Set task dependencies
    download_task >> preprocess_task >> train_task >> evaluate_task
```

---

## **Running Airflow**

### **1. Start Airflow**
Run the following command to start all services:
```bash
curl -o docker-compose.yml "https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml" # to get the docker compose file from airflow docs 
docker-compose up -d
```

### **2. Access the Airflow UI**
Open your browser and go to:
```
http://localhost:8080
```
- **Username**: `admin`
- **Password**: `admin`

---

## **Using the Airflow UI**

### **1. View DAGs**
- Go to the **DAGs** page.
- You should see the `iris_pipeline` DAG listed.

### **2. Trigger the DAG**
- Toggle the **On/Off** switch next to the `iris_pipeline` DAG to enable it.
- Click the **Trigger DAG** button to run the DAG manually.

### **3. Monitor Tasks**
- Go to the **Graph View** to see the status of each task.
- Click on a task to view logs and debug issues.

---

## **Stopping Airflow**
To stop all services, run:
```bash
docker-compose down
```

---

## **Expected Output**
- **Data**: The Iris dataset will be saved in `./data/iris.csv`.
- **Preprocessed Data**: Split datasets (`X_train.csv`, `X_test.csv`, etc.) will be saved in `./data`.
- **Model**: The trained model will be saved in `./models/iris_model.pkl`.
- **Results**: The model accuracy will be saved in `./results/accuracy.txt`.

---

## **Troubleshooting**
- **DAG Not Appearing**: Check the scheduler logs:
  ```bash
  docker logs airflow-scheduler-1
  ```
- **Task Failures**: Check the task logs in the Airflow UI.

---

## **Conclusion**
This setup allows you to automate a complete machine learning pipeline using Apache Airflow and Docker. You can extend the pipeline by adding more tasks or integrating with other tools.

Let me know if you need further assistance! 😊

--- 

Save this as `README.md` in your project directory. It provides a comprehensive guide for anyone (including yourself) to set up and run the project.