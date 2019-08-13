import os
import sys
from app import scheduler as logsched
from threading import Thread
import app.mylogging as log
from bottle import Bottle, run, static_file
app = Bottle()

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

@app.route('/')
def server_static():
    return static_file("info.log",root=dir_path+"/")

def main():
    try:
        log.info("before starting threads ...")
        h = Thread(name="scheduler",target=logsched.main,daemon=True)
        t = Thread(name="bottle",target=run, kwargs=dict(app=app, host='30.161.120.108', port=45001,
                                           debug=True, reloader=True))
        h.start()
        t.start()
        h.join()
        t.join()
    except KeyboardInterrupt:
        sys.stdout.write("Aborted by user.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
