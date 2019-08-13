import time
import app.mylogging as log
from app.kticket import check_and_reinit_kticket
from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()

def time_usage(func):
    def wrapper(*args, **kwargs):
        beg_ts = time.time()
        retval = func(*args, **kwargs)
        end_ts = time.time()
        log.info("elapsed time: %fs" % (end_ts - beg_ts))
        return retval
    return wrapper

@time_usage
def f1():
    if False:
        log.info("<something 1>, FAIL!")
    else:
        log.info("<something 1>, PASS!")

@time_usage
def f2():
    if False:
        log.info("<something 2>, FAIL!")
    else:
        log.info("<something 2>, PASS!")

@sched.scheduled_job('interval', minutes=5)
def once_per():
    """
    If you lauch this script at time T, then this function will be called
    at T+60 minutes for the first time.
    Ex.: if you lauch the script at 13h07, then this function will be called at 14h07
    for the first time.
    """
    log.info('calling every 5 mins')
    check_and_reinit_kticket()
    log.info('f1 case ...' )
    run_df_filter(spark)
    log.info('f2 case ...')
    run_df_write(spark)

def main():
    log.info('the scheduler is running...')
    sched.start()

if __name__ == "__main__":
    main()