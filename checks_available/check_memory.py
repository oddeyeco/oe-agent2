import re
import datetime
import lib.getconfig
import lib.pushdata
import lib.record_rate


cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
reaction = 0
check_type = 'system'


def runcheck():
    local_vars = []
    timestamp = int(datetime.datetime.now().strftime("%s"))
    try:
        memory_stats = ('MemTotal:', 'MemAvailable:', 'Buffers:', 'Cached:', 'Active:', 'Inactive:')
        memorytimes = {}

        read_memorystats = open("/proc/meminfo", "r")
        raw_memorystats = "\n".join(read_memorystats.read().split('\n'))

        for i in raw_memorystats.split("\n"):
            for stat in memory_stats:
                if stat in i:
                    u=re.sub(' +', ' ', i).split(" ")
                    if len(u) > 1:
                        memorytimes['mem_'+u[0].replace(':','').replace('Mem','').lower()] = 1024*int(u[1])

        for key, value in list(memorytimes.items()):
            local_vars.append({'name': key, 'timestamp': timestamp, 'value': value, 'reaction': reaction})
        if 'mem_available' in memorytimes:
            mem_used_percent = 100 - ((memorytimes['mem_available'] * 100) / memorytimes['mem_total'])
            local_vars.append({'name': 'mem_used_percent', 'timestamp': timestamp, 'value': mem_used_percent, 'chart_type': 'Percent'})

        read_memorystats.close()
        return local_vars
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

