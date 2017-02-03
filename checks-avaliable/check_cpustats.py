import os, sys
import datetime
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
host_group = config.get('SelfConfig', 'host_group')

# ---------------------- #
rated = True
reaction = -3

warn_level = 90
crit_level = 100
# ---------------------- #

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

    cpucount = 0
    for line in open("/proc/stat", "r").xreadlines():
        if 'cpu' in line:
            cpucount += 1
    cpucount -=1

    metrinames=['cpu_user', 'cpu_nice', 'cpu_system', 'cpu_idle', 'cpu_iowait', 'cpu_irq', 'cpu_softirq']

    with open('/proc/stat') as f:
        cpu_stats = [float(column) for column in f.readline().strip().split()[1:]]

    if 'cpu_old_stats' not in globals():
        global cpu_old_stats
        cpu_old_stats = cpu_stats

    if not cpu_old_stats:
        print("List is empty")

    last_idle = cpu_old_stats[3]
    last_total = sum(cpu_old_stats)

    idle = cpu_stats[3]
    total = sum(cpu_stats)

    try:
        if idle - last_idle > 0 :
            idle_delta, total_delta = idle - last_idle, total - last_total
            utilisation = 100.0 * (1.0 - idle_delta / total_delta)
        else:
            utilisation = 0
    except Exception as e:
        #push = __import__('pushdata')
        push.print_error(__name__ , (e))



    try:
        def send_special():

            if utilisation < warn_level:
                health_value = 0
                err_type = 'OK'
            if utilisation >= warn_level < crit_level:
                health_value = 8
                err_type = 'WARNING'
            if utilisation >= crit_level:
                health_value = 16
                err_type = 'ERROR'

            d = round(utilisation, 2)

            health_message = err_type + ': CPU Usage is ' + str(d) + ' percent'
            jsondata.send_special("CPU-Percent", timestamp, health_value, health_message, err_type)
            jsondata.gen_data('cpu_percent', timestamp, d, push.hostname, check_type, cluster_name)
        send_special()
    except Exception as e:
        #push = __import__('pushdata')
        push.print_error(__name__, (e))



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
        #push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

