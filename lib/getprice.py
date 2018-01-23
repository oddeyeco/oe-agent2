import glob
import os
import sys
import json
import time

os.chdir('../')
srcdir = os.path.abspath(os.path.dirname(__file__))
libdir = os.path.join(srcdir, os.getcwd())
sys.path.append(libdir)
sys.path.append(os.path.dirname(os.path.realpath("__file__"))+'/checks_enabled')

import lib.run_bash
import lib.pushdata
import lib.getconfig
import lib.commonclient

cron_interval = int(lib.getconfig.getparam('SelfConfig', 'check_period_seconds'))
log_file = lib.getconfig.getparam('SelfConfig', 'log_file')
pid_file = lib.getconfig.getparam('SelfConfig', 'pid_file')
tsdb_type = lib.getconfig.getparam('TSDB', 'tsdtype')

library_list = []

os.chdir("checks_enabled")

checklist = glob.glob("check_*.py")

module_names = []
for checks in checklist:
    module_names.append(checks.split('.')[0])
modules = list(map(__import__, module_names))

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
extra_tags = ('chart_type', 'check_type')
jsondata = lib.pushdata.JonSon()

pl = json.loads(lib.commonclient.httpget(__name__, 'https://app.oddeye.co/OddeyeCoconut/getpayinfo'))
u_p = float(pl['mp'])


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def calcmodules():
    if len(modules) > 0:
        try:
            jsondata.prepare_data()
            for modol in modules:
                try:
                    a = modol.Check().runcheck()
                    bs = lib.run_bash.run_shell_scripts()
                    for b in a:
                        jsondata.gen_data_json(b, b['host'], cluster_name)
                    for bb in bs:
                        jsondata.gen_data_json(bb, bb['host'], cluster_name)
                except Exception as e:
                    print(str(e))
            a = jsondata.put_json(False)
            return (a)
        except Exception as e:
            print(e)
    else:
        print('None of python modules is enabled')

a1 = calcmodules()
time.sleep(2)
a2 = calcmodules()
runsmonth = 60 / cron_interval * 60 * 24 * 30

o = (a2 * runsmonth * u_p)
deq = (o / 100 * 2) + 0.3
u = o + deq
print(bcolors.OKBLUE + 'Monthly approximate price for this host is ' + bcolors.WARNING + '{:.2f}'.format(o) +
      bcolors.OKBLUE + ' OddEye units, which is ' + bcolors.WARNING + '{:.2f}'.format(u) + '$')

# print(bcolors.OKBLUE + 'Please write yes or no ' + bcolors.FAIL + 'jhasdasjh')
# print('{:.2f}'.format(deq))
# print(a1, a2)
