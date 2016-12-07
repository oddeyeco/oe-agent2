import datetime
import socket
import os, sys
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')


def run_load_average():

    cpucount = 0
    for line in open("/proc/stat", "r").xreadlines():
        if 'cpu' in line:
            cpucount += 1
    cpucount -=1
    load_start_worry_about = format(float(cpucount)/3, '.3g')

    hostname = socket.getfqdn()
    check_type = 'system'
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    jsondata=push.JonSon()
    jsondata.create_data()
    timestamp = int(datetime.datetime.now().strftime("%s"))
    try:

        proc_loadavg=open("/proc/loadavg", "r").readline().split()

        if float(proc_loadavg[0]) < load_start_worry_about:
            alert_level = -3
        else:
            alert_level = 0

        jsondata.gen_data('sys_load_1', timestamp, proc_loadavg[0], hostname, check_type, cluster_name, alert_level)
        jsondata.gen_data('sys_load_5', timestamp, proc_loadavg[1], hostname, check_type, cluster_name, alert_level)
        jsondata.gen_data('sys_load_15', timestamp, proc_loadavg[2], hostname, check_type, cluster_name, alert_level)

        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass