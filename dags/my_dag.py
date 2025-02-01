from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    'my_data_science_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',
) as dag:

    task1 = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    task2 = BashOperator(
        task_id='echo_hello',
        bash_command='echo "Hello from Airflow!"',
    )

    task1 >> task2