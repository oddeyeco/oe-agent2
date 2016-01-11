import datetime
import socket
import os, sys
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')


def run_load():
    try:
        proc_loadavg=open('/proc/loadavg', "r")
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)

    hostname = socket.getfqdn()
    check_type = 'system'
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    jsondata=push.JonSon()
    jsondata.create_data()

    try:
        for line in proc_loadavg:
            timestamp = int(datetime.datetime.now().strftime("%s"))
            columns = line.split()
            for loadavg in range(0, 3):
                if loadavg is 0:
                    jsondata.gen_data('sys_load_1',timestamp, columns[loadavg], hostname, check_type, cluster_name)
                elif loadavg is 1:
                    jsondata.gen_data('sys_load_5',timestamp, columns[loadavg], hostname, check_type, cluster_name)
                elif loadavg is 2:
                    jsondata.gen_data('sys_load_15',timestamp, columns[loadavg], hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(e)
        pass
