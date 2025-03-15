import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = BackgroundScheduler()

def run_job():
    print("Running job")

scheduler.add_job(run_job, 'interval', seconds=2)
scheduler.start()

while True:
    time.sleep(1)
    print("awake")