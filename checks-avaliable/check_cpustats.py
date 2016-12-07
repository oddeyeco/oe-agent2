import os, sys
import datetime
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
rated = True

'''
0: user: normal processes executing in user mode
1: nice: niced processes executing in user mode
2: system: processes executing in kernel mode
3: idle: twiddling thumbs
4: iowait: waiting for I/O to complete
5: irq: servicing interrupts
6: softirq: servicing softirqs
'''

def run_cpustats():
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    value_rate= __import__('record_rate')
    check_type = 'system'
    jsondata=push.JonSon()
    jsondata.create_data()
    rate=value_rate.ValueRate()
    timestamp = int(datetime.datetime.now().strftime("%s"))
    raw_cpustats=" ".join(open("/proc/stat", "r").readline().split())
    cpu_stats = []

    cpucount = 0
    for line in open("/proc/stat", "r").xreadlines():
        if 'cpu' in line:
            cpucount += 1
    cpucount -=1

    for i in raw_cpustats.split(" "):
        cpu_stats.append(i)
    cpu_stats.remove('cpu')
    metrinames=['cpu_user', 'cpu_nice', 'cpu_system', 'cpu_idle', 'cpu_iowait', 'cpu_irq', 'cpu_softirq']
    try:
        for index in range(0, 7):
            name = metrinames[index]
            value = cpu_stats[index]
            if rated is True:
                values_rate = rate.record_value_rate(name, value, timestamp)/cpucount
                jsondata.gen_data(name, timestamp, values_rate, push.hostname, check_type, cluster_name)
            else:
                jsondata.gen_data(name, timestamp, int(value)/cpucount, push.hostname, check_type, cluster_name)


        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

