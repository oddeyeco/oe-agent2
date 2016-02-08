import glob, os, sys
import time
import ConfigParser
import logging
from daemon import runner
import threading

sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/checks-enabled')
sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/lib')

config = ConfigParser.RawConfigParser()
config.read(os.getcwd()+'/conf/config.ini')
cron_interval = int(config.get('SelfConfig', 'check_period_seconds'))
proc_count = int(config.get('SelfConfig', 'parallels_count'))
log_file = config.get('SelfConfig', 'log_file')
pid_file = config.get('SelfConfig', 'pid_file')

library_list = []

os.chdir("checks-enabled")

checklist = glob.glob("check_*.py")


def run_shell_scripts():
    runbash = __import__('run_bash')
    runbash.run_shell_scripts()


def run_scripts():
    for checks in checklist:
        module_name, ext = os.path.splitext(checks)
        module = __import__(module_name)
        library_list.append(module)
        run = 'run_'+module_name.rsplit('.')[0].rsplit('check_')[1]
        run_method = getattr(module, run)
        run_method()
        message=module_name, time.clock()
        logger.debug(message)


class App():


    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = log_file
        self.pidfile_path = pid_file
        self.pidfile_timeout = 5

    def run(self):
        while True:
            run_scripts()
            run_shell_scripts()
            time.sleep(cron_interval)


app = App()
logger = logging.getLogger("PuyPuy")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler = logging.FileHandler(log_file)
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
