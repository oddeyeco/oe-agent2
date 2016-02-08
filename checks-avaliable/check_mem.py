import psutil, os, sys
import datetime

import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')



def run_mem():
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    raw_memstats = str(psutil.phymem_usage())
    split_memstats = raw_memstats.split('(')[-1].split(')')[0]
    check_type = 'system'
    mem_list = [x.strip() for x in split_memstats.split(',')]
    jsondata=push.JonSon()
    jsondata.create_data()
    try:
        for index in range(0, len(mem_list)):
            timestamp = int(datetime.datetime.now().strftime("%s"))
            mytype = mem_list[index].split('=')[0]
            myvalue = mem_list[index].split('=')[1].rstrip('L')
            jsondata.gen_data('mem_'+mytype, timestamp, myvalue, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
