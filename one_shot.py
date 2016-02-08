__author__ = 'Ara Sadoyan'

import glob, os, sys
import ConfigParser
import logging
import threading

sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/checks-enabled')

config = ConfigParser.RawConfigParser()
config.read(os.getcwd()+'/conf/config.ini')
cron_interval = int(config.get('SelfConfig', 'check_period_seconds'))
proc_count = int(config.get('SelfConfig', 'parallels_count'))
log_file = config.get('SelfConfig', 'log_file')
pid_file = config.get('SelfConfig', 'pid_file')

library_list = []

os.chdir("checks-enabled")

checklist = str(sys.argv[1])

def run_scripts():
    module_name, ext = os.path.splitext(checklist)
    module = __import__(module_name)
    library_list.append(module)
    run = 'run_'+module_name.rsplit('.')[0].rsplit('check_')[1]
    run_method = getattr(module, run)
    run_method()

def do_every (interval, worker_func, iterations=1):
  if iterations != 1:
    threading.Timer (
      interval,
      do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]
    ).start ()

  worker_func()

do_every (int(cron_interval), run_scripts)
