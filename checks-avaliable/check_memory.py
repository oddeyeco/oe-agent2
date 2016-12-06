import os, sys, re
import datetime
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
alert_level = 0


def run_memory():
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    check_type = 'system'
    jsondata=push.JonSon()
    jsondata.create_data()
    timestamp = int(datetime.datetime.now().strftime("%s"))
    memory_stats = ('MemTotal:', 'MemAvailable:', 'Buffers:', 'Cached:', 'Active:', 'Inactive:')
    memorytimes = {}
    try:
        raw_memorystats="\n".join(open("/proc/meminfo", "r").read().split('\n'))
        for i in raw_memorystats.split("\n"):
            for stat in memory_stats:
                if stat in i:
                    u=re.sub(' +', ' ', i).split(" ")
                    if len(u) > 1:
                        memorytimes['mem_'+u[0].replace(':','').replace('Mem','').lower()] = 1024*int(u[1])

        for key, value in memorytimes.iteritems():
            jsondata.gen_data(key, timestamp, value, push.hostname, check_type, cluster_name, alert_level)

        mem_used_percent = 100 - ((memorytimes['mem_available'] * 100) / memorytimes['mem_total'])
        jsondata.gen_data('mem_used_percent', timestamp, mem_used_percent, push.hostname, check_type, cluster_name)

        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

