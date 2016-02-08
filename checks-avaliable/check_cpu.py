import psutil, os, sys
import datetime
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')


def run_cpu():
    raw_cpustats = str(psutil.cpu_times_percent(percpu=False))
    split_cpustats = raw_cpustats.split('(')[-1].split(')')[0]
    check_type = 'system'

    cpu_list = [x.strip() for x in split_cpustats.split(',')]
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    jsondata=push.JonSon()
    jsondata.create_data()
    try:
        for index in range(0, len(cpu_list)):
            timestamp = int(datetime.datetime.now().strftime("%s"))
            mytype = cpu_list[index].split('=')[0]
            myvalue = cpu_list[index].split('=')[1]
            jsondata.gen_data('cpu_'+mytype, timestamp, myvalue, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
