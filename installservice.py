#!/usr/bin/env python2

import ConfigParser
import os
import pwd
import grp
import sys
import subprocess

base_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(base_dir)

config = ConfigParser.RawConfigParser()
config_file = 'conf/config.ini'
systemd_file = '/lib/systemd/system/oe-agent.service'
config.read(config_file)

pid= config.get('SelfConfig', 'pid_file')
run_user = config.get('SelfConfig', 'run_user')
sparser = ConfigParser.RawConfigParser()
sparser.optionxform= str

service_file = '/lib/systemd/system/oe-agent.service'
sparser = ConfigParser.SafeConfigParser()
sparser.optionxform= str

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
sparser.set('Service', 'ExecStart', sys.executable + ' ' + base_dir + '/oddeye.py  start')
sparser.set('Service', 'PIDFile', pid)

with open(service_file, 'wb') as servicefile:
    sparser.write(servicefile)

subprocess.Popen('systemctl daemon-reload', stdout=subprocess.PIPE, shell=True).communicate()
subprocess.Popen('systemctl enable oe-agent.service', stdout=subprocess.PIPE, shell=True).communicate()
subprocess.Popen('systemctl start oe-agent', stdout=subprocess.PIPE, shell=True).communicate()
