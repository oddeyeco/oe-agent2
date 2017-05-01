import glob
import os
import sys
import time
import ConfigParser
import logging
from multiprocessing import Process
from lib.daemon import Daemon
import lib.upload_cached
import lib.run_bash
import lib.pushdata
import lib.puylogger
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

logger = logging.getLogger("PuyPuy")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler = logging.FileHandler(log_file)
handler.setFormatter(formatter)
logger.addHandler(handler)

def run_shell_scripts():
    lib.run_bash.run_shell_scripts()


module_names = []
for checks in checklist:
    module_names.append(checks.split('.')[0])
modules = map(__import__, module_names)


def run_scripts():
    for modol in modules:
        start_time = time.time()
        modol.runcheck()
        time_elapsed = "{:.9f}".format(time.time() - start_time) +  " seconds"
        message = time_elapsed +' ' + str(modol).split("'")[1]
        lib.puylogger.print_message(message)

def upload_cache():
    lib.upload_cached.cache_uploader()

class App(Daemon):
    def run(self):
        tsdb_type = config.get('TSDB', 'tsdtype')
        backends = ('OddEye', 'InfluxDB', 'KairosDB', 'OpenTSDB')
        if tsdb_type in backends:
            def run_normal():
                while True:
                    run_scripts()
                    if lib.puylogger.debug_log:
                        lib.puylogger.print_message(str(run_scripts))
                    run_shell_scripts()
                    if lib.puylogger.debug_log:
                        lib.puylogger.print_message(str(run_shell_scripts))
                    time.sleep(cron_interval)


            def run_cache():
                while True:
                    upload_cache()
                    if lib.puylogger.debug_log:
                        lib.puylogger.print_message(str(upload_cache))
                    time.sleep(cron_interval)


            cache=threading.Thread(target=run_cache, name='Run Cache')
            cache.daemon = True
            cache.start()

            run_normal()

            # p1 = Process(target=run_normal)
            # p1.daemon = True
            # p1.start()

            #run_cache()

            # p2 = Process(target=run_cache)
            # if not p2.is_alive():
            #     p2.daemon = True
            #     p2.start()
            #     p2.join()
            # p1.join()

        else:
            while True:
                run_scripts()
                run_shell_scripts()
                time.sleep(cron_interval)

if __name__ == "__main__":
        daemon = App(pid_file)
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart" % sys.argv[0]
                sys.exit(2)
