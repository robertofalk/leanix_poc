from apscheduler.schedulers.background import BackgroundScheduler

class Scheduler:

    STOPPED = 'STOPPED'
    RUNNING = 'RUNNING'

    def __init__(self):
        self.scheduler = BackgroundScheduler()
    
    def get_status(self):
        return self.scheduler.get_jobs()

    def start(self, func):
        self.scheduler.add_job(func, 'interval', seconds=30)
        self.scheduler.start()
    
    def stop(self):
        self.scheduler.shutdown()