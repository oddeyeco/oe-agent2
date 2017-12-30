import glob
import os
import sys
import time
import threading
from lib.daemon import Daemon
import lib.upload_cached
import lib.run_bash
import lib.pushdata
import lib.puylogger
import lib.getconfig
import gc

sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/checks_enabled')
sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/lib')

cron_interval = int(lib.getconfig.getparam('SelfConfig', 'check_period_seconds'))
log_file = lib.getconfig.getparam('SelfConfig', 'log_file')
pid_file = lib.getconfig.getparam('SelfConfig', 'pid_file')
tsdb_type = lib.getconfig.getparam('TSDB', 'tsdtype')

library_list = []

os.chdir("checks_enabled")

checklist = glob.glob("check_*.py")

# def run_shell_scripts():
#     lib.run_bash.run_shell_scripts()

module_names = []
for checks in checklist:
    module_names.append(checks.split('.')[0])
modules = map(__import__, module_names)


cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
extra_tags = ('chart_type', 'check_type')
jsondata = lib.pushdata.JonSon()


def run_scripts():
    if len(modules) > 0:
        try:
            start_gtime = time.time()
            jsondata.prepare_data()
            for modol in modules:
                try:
                    # jsondata.prepare_data()
                    start_time = time.time()
                    a = modol.Check().runcheck()
                    time_elapsed = "{:.9f}".format(time.time() - start_time) + " seconds"
                    message = time_elapsed + ' ' + str(modol).split("'")[1]
                    for b in a:
                        jsondata.gen_data_json(b, b['host'], cluster_name)
                    lib.puylogger.print_message(message)
                except Exception as e:
                    lib.puylogger.print_message(str(e))
            jsondata.put_json()
            time_elapsed2 = '{:.9f}'.format(time.time() - start_gtime) + ' seconds '
            lib.puylogger.print_message('Spent ' + time_elapsed2 + 'to complete interation')
        except Exception as e:
            lib.puylogger.print_message(str(e))
    else:
        lib.puylogger.print_message(str('None of python modules is enabled'))

def upload_cache():
    lib.upload_cached.cache_uploader()


class App(Daemon):
    def run(self):
        backends = ('OddEye', 'InfluxDB', 'KairosDB', 'OpenTSDB')
        self.hast = 1
        if tsdb_type in backends:
            def run_normal():
                while True:
                    run_scripts()
                    if lib.puylogger.debug_log:
                        lib.puylogger.print_message(str(run_scripts))
                    try:
                        lib.run_bash.run_shell_scripts()
                    except Exception as d:
                        lib.puylogger.print_message(str(d))

                    if lib.puylogger.debug_log:
                        lib.puylogger.print_message(str(lib.run_bash.run_shell_scripts()))
                    if self.hast % 25 == 0:
                          gc.collect()
                          self.hast = 1
                    else:
                        self.hast += 1
                    time.sleep(cron_interval)
                    #lib.puylogger.print_message('----------------------------------------')

            def run_cache():
                while True:
                    upload_cache()
                    if lib.puylogger.debug_log:
                        lib.puylogger.print_message(str(upload_cache))
                    time.sleep(cron_interval)


            cache = threading.Thread(target=run_cache, name='Run Cache')
            cache.daemon = True
            cache.start()

            run_normal()

        else:
            while True:
                run_scripts()
                lib.run_bash.run_shell_scripts()
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
                    print ("Unknown command")
                    sys.exit(2)
            sys.exit(0)
        else:
                print ("usage: %s start|stop|restart" % sys.argv[0])
                sys.exit(2)
