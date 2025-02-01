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