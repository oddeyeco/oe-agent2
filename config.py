from ConfigParser import SafeConfigParser
import os

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
err_handler = 2
tsdtype = 'OddEye'
check_period = 10
debug_log = 'False'
max_cache = 50000


uuid = raw_input("Please enter your UID: ")
run_user = raw_input("unprivileged system account for Agent: ")
log_file = raw_input("Full path for log file (Should be writable for Agent's system user): ")
pid_file = raw_input("Full path for pid file(Should be writable for Agent's system user): ")
tmpdir = raw_input("Full path for temp files(Should be writable for Agent's system user): ")
location = raw_input("Your servers location(Aka : us-east-1): ")
cluster_name = raw_input("Friendly name of your cluster: ")
host_group = raw_input("Grouping TAG of hosts: ")


conf_system_checks = raw_input("Do you want me to enable basic system checks (yes/no): ")
while conf_system_checks not in ['yes', 'no']:
    print(bcolors.FAIL + 'Please write yes or no ' + bcolors.FAIL)
    conf_system_checks = raw_input("Do you want me to enable basic system checks (yes/no): ")

parser = SafeConfigParser()
config_file = 'conf/config.ini'

parser.read(config_file)
parser.remove_section('TSDB')
parser.remove_section('SelfConfig')
parser.add_section('SelfConfig')
parser.add_section('TSDB')
parser.set('TSDB', 'url', url)
parser.set('TSDB', 'uuid', uuid)
parser.set('TSDB', 'sandbox', 'False')
parser.set('TSDB', 'err_handler', '2')
parser.set('TSDB', 'tsdtype', 'OddEye')
parser.set('SelfConfig','check_period_seconds', str(check_period))
parser.set('SelfConfig', 'log_file', log_file)
parser.set('SelfConfig', 'pid_file', pid_file)
parser.set('SelfConfig', 'cluster_name', cluster_name)
parser.set('SelfConfig', 'host_group', host_group)
parser.set('SelfConfig', 'tmpdir', tmpdir)
parser.set('SelfConfig', 'debug_log', 'False')
parser.set('SelfConfig', 'run_user', run_user)
parser.set('SelfConfig', 'max_cache', '50000')
parser.set('SelfConfig', 'location', location)


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