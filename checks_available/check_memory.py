import re
import lib.getconfig
import lib.pushdata
import lib.record_rate
import lib.puylogger
import lib.basecheck

warn_percent = float(lib.getconfig.getparam('Memory Stats', 'high'))
crit_percent = float(lib.getconfig.getparam('Memory Stats', 'severe'))
static_alerts = lib.getconfig.getparam('Memory Stats', 'static_enabled')
check_type = 'system'

'''
[Memory Stats]
static_enabled: True
high : 2
severe : 3
'''

class Check(lib.basecheck.CheckBase):

    def precheck(self):
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
                if key == 'mem_buffers':
                    reaction = -3
                else:
                    reaction = 0
                self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': value, 'reaction': reaction})
            if 'mem_available' in memorytimes:
                mem_used_percent = 100 - ((memorytimes['mem_available'] * 100) / memorytimes['mem_total'])
                self.local_vars.append({'name': 'mem_used_percent', 'timestamp': self.timestamp, 'value': mem_used_percent, 'chart_type': 'Percent'})
                if static_alerts:
                    # if mem_used_percent < warn_percent:
                    #     health_value = 0
                    #     err_type = 'OK'
                    #     health_message = err_type + ': Systems memory usage is ' + str("{0:.2f}".format(mem_used_percent)) + ' percent'
                    #     self.jsondata.send_special("Memory-Usage", self.timestamp, health_value, health_message, err_type, -self.error_handler)
                    if warn_percent <= mem_used_percent < crit_percent:
                        err_type = 'WARNING'
                        health_value = 8
                        health_message = err_type + ': Systems memory usage is ' + str("{0:.2f}".format(mem_used_percent)) + ' percent'
                        self.jsondata.send_special("Memory-Usage", self.timestamp, health_value, health_message, err_type, -self.error_handler)
                    if mem_used_percent >= crit_percent:
                        health_value = 16
                        err_type = 'ERROR'
                        health_message = err_type + ': Systems memory usage is ' + str("{0:.2f}".format(mem_used_percent)) + ' percent'
                        self.jsondata.send_special("Memory-Usage", self.timestamp, health_value, health_message, err_type, -self.error_handler)

            read_memorystats.close()
            # return local_vars
        except Exception as e:
            lib.pushdata.print_error(__name__ , (e))
            pass

