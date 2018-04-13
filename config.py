#!/usr/bin/env python2

from ConfigParser import SafeConfigParser
import os
import pwd
import getpass
import grp
import sys
import subprocess

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

print(bcolors.OKGREEN + "Please give me some information to configure OddEye agent" + bcolors.OKGREEN)
print(bcolors.ENDC + " " + bcolors.ENDC)

url = 'https://api.oddeye.co/oddeye-barlus/put/tsdb'
sandbox = 'False'
error_handler = 2
tsdtype = 'OddEye'
check_period = 10
debug_log = 'False'
max_cache = 50000


uuid = raw_input("Please enter your UID: ")
run_user = raw_input("unprivileged system account for Agent (defaults to current running user): ")
input_base_dir = raw_input("Please input directory name for storing runtime files (defaults to current working directory):")

if input_base_dir == '':
    input_base_dir = os.getcwd()

base_dir = input_base_dir.rstrip('/')
os.mkdir(base_dir + '/var')
log_file = base_dir + '/var/oddeye.log'
pid_file = base_dir + '/var/oddeye.pid'
tmpdir = base_dir + '/var/oddeye_tmp'
location = raw_input("Your servers location(Aka : us-east-1): ")
cluster_name = raw_input("Friendly name of your cluster: ")
host_group = raw_input("Grouping TAG of hosts: ")
os.mkdir(tmpdir)

if run_user == '':
    uid = os.getuid()
    gid = os.getgid()
    run_user = getpass.getuser()
else:
    uid = pwd.getpwnam(run_user).pw_uid
    gid = pwd.getpwnam(run_user).pw_gid

for root, dirs, files in os.walk(base_dir, topdown=False):
    for name in files:
        os.chown((os.path.join(root, name)), uid, gid)
    for name in dirs:
        os.chown((os.path.join(root, name)), uid, gid)

conf_system_checks = raw_input("Do you want me to enable basic system checks (yes/no): ")
systemd_service = raw_input("Do you want to run OddEye agent at system boot (yes/no): ")

while conf_system_checks not in ['yes', 'no']:
    print(bcolors.FAIL + 'Please write yes or no ' + bcolors.FAIL)
    conf_system_checks = raw_input("Do you want me to enable basic system checks (yes/no): ")

parser = SafeConfigParser()
config_file = 'conf/config.ini'
service_file = '/lib/systemd/system/oe-agent.service'
sparser = SafeConfigParser()
sparser.optionxform= str

parser.read(config_file)
parser.remove_section('TSDB')
parser.remove_section('SelfConfig')
parser.add_section('SelfConfig')
parser.add_section('TSDB')
parser.set('TSDB', 'url', url)
parser.set('TSDB', 'uuid', uuid)
parser.set('TSDB', 'sandbox', 'False')
parser.set('TSDB', 'tsdtype', 'OddEye')
parser.set('SelfConfig', 'error_handler', '2')
parser.set('SelfConfig','check_period_seconds', str(check_period))
parser.set('SelfConfig', 'pid_file', pid_file)
parser.set('SelfConfig', 'tmpdir', tmpdir)
parser.set('SelfConfig', 'log_file', log_file)
parser.set('SelfConfig', 'log_rotate_seconds', str(3600))
parser.set('SelfConfig', 'log_rotate_backups', str(24))
parser.set('SelfConfig', 'cluster_name', cluster_name)
parser.set('SelfConfig', 'host_group', host_group)
parser.set('SelfConfig', 'debug_log', 'False')
parser.set('SelfConfig', 'run_user', run_user)
parser.set('SelfConfig', 'max_cache', '50000')
parser.set('SelfConfig', 'location', location)

sparser.add_section('Unit')
sparser.add_section('Install')
sparser.add_section('Service')

sparser.set('Unit', 'Description', 'OddEye Agent Service')
sparser.set('Unit', 'After', 'syslog.target')
sparser.set('Install', 'WantedBy', 'multi-user.target')

groups = [g.gr_name for g in grp.getgrall() if run_user in g.gr_mem]
gid = pwd.getpwnam(run_user).pw_gid
group = grp.getgrgid(gid).gr_name

sparser.set('Service', 'Type', 'simple')
sparser.set('Service', 'User', run_user)
sparser.set('Service', 'Group', group)
sparser.set('Service', 'WorkingDirectory', base_dir + '/')
sparser.set('Service', 'ExecStart', sys.executable + ' ' + base_dir + '/oddeye.py systemd')
sparser.set('Service', 'PIDFile', pid_file)
sparser.set('Service', 'Restart', 'on-failure')

with open(service_file, 'wb') as servicefile:
 sparser.write(servicefile)

with open(config_file, 'wb') as configfile:
 parser.write(configfile)

src = (os.path.dirname(os.path.realpath("__file__"))+'/checks_available')
dst = (os.path.dirname(os.path.realpath("__file__"))+'/checks_enabled')
os.chdir(dst)

syschecks = ('check_cpustats.py', 'check_disks.py', 'check_load_average.py', 'check_memory.py', 'check_network_bytes.py', 'check_oddeye.py')

if conf_system_checks == 'yes':
    for syscheck in syschecks:
        os.symlink('../checks_available/' + syscheck, './' + syscheck)
    print(bcolors.OKGREEN + 'System checks are configured, please restart agent to enable' + bcolors.OKGREEN)
elif conf_system_checks == 'no':
    print(bcolors.OKGREEN + ' ' + bcolors.OKGREEN)
    print(bcolors.OKGREEN + 'Done, please do not forget to configure and enable checks suitable for you system' + bcolors.OKGREEN)
else:
    print(bcolors.FAIL + ' ' + bcolors.FAIL)
    print(bcolors.FAIL + 'Failed to enable systems checks, please enable it manually' + bcolors.FAIL)

if systemd_service == 'yes':
    subprocess.Popen('systemctl daemon-reload', stdout=subprocess.PIPE, shell=True).communicate()
    subprocess.Popen('systemctl enable oe-agent.service', stdout=subprocess.PIPE, shell=True).communicate()
    subprocess.Popen('systemctl start oe-agent', stdout=subprocess.PIPE, shell=True).communicate()
    print(bcolors.OKGREEN + 'Autostart of oe-agent is enabled' + bcolors.OKGREEN)
elif conf_system_checks == 'no':
    print(bcolors.OKGREEN + ' ' + bcolors.OKGREEN)
    print(bcolors.OKGREEN + 'Will not run oe-agent on boot, please manually start it' + bcolors.OKGREEN)
else:
    print(bcolors.FAIL + ' ' + bcolors.FAIL)
    print(bcolors.FAIL + 'Failed to add oe-agent to autostart' + bcolors.FAIL)
