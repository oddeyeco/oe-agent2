import glob, os, sys
import time
import ConfigParser
import logging
from daemon import runner
#from multiprocessing import Process
import threading

sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/checks_enabled')
sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/lib')

config = ConfigParser.RawConfigParser()
config.read(os.getcwd()+'/conf/config.ini')
cron_interval = int(config.get('SelfConfig', 'check_period_seconds'))
log_file = config.get('SelfConfig', 'log_file')
pid_file = config.get('SelfConfig', 'pid_file')

library_list = []

os.chdir("checks_enabled")

checklist = glob.glob("check_*.py")

def run_shell_scripts():
    runbash = __import__('run_bash')
    runbash.run_shell_scripts()

def run_scriptos(methon):
    methon()

def run_scripts():
   for checks in checklist:
        start_time = time.time()
        module_name, ext = os.path.splitext(checks)
        module = __import__(module_name)
        module.runcheck()
        time_elapsed = "{:.9f}".format(time.time() - start_time) + " seconds"
        message = time_elapsed + ' ' + str(module_name)
        logger.info(message)


def upload_cache():
    from lib.upload_cached import cache_uploader
    cache_uploader()


class App():


    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = log_file
        self.stderr_path = log_file
        self.pidfile_path = pid_file
        self.pidfile_timeout = 5

    def run(self):
        tsdb_type = config.get('TSDB', 'tsdtype')
        backends = ('OddEye', 'InfluxDB', 'KairosDB', 'OpenTSDB')
        if tsdb_type in backends:
            def run_normal():
                while True:
                    run_scripts()
                    run_shell_scripts()
                    time.sleep(cron_interval)

            def run_cache():
                while True:
                    upload_cache()
                    time.sleep(cron_interval)

            # p1 = Process(target=run_normal)
            # p1.daemon = True
            # p1.start()
            #
            # p2 = Process(target=run_cache())
            # if not p2.is_alive():
            #     p2.daemon = True
            #     p2.start()
            #     p2.join()
            # p1.join()

            cache=threading.Thread(target=run_cache, name='Run Cache')
            cache.daemon = True
            cache.start()

            run_normal()
        else:
            while True:
                run_scripts()
                run_shell_scripts()
                time.sleep(cron_interval)

try:
  import setproctitle
  setproctitle.setproctitle('puypuy-mukik')
except:
  pass

app = App()
logger = logging.getLogger("PuyPuy")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler = logging.FileHandler(log_file)
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()


