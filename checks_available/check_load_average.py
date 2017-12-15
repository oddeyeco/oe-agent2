import lib.getconfig
import lib.pushdata
import lib.basecheck

warn_level = int(lib.getconfig.getparam('System Thresholds', 'load_high'))
crit_level = int(lib.getconfig.getparam('System Thresholds', 'load_severe'))
check_type = 'system'
reaction = -3


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        cpucount = 0
        procstats = open("/proc/stat", "r")
        for line in procstats:
            if 'cpu' in line:
                cpucount += 1
        cpucount -= 1
        procstats.close()

        try:
            loadavg = open("/proc/loadavg", "r")
            proc_loadavg = loadavg.readline().split()
            curr_level = float(proc_loadavg[0]) * 100 / cpucount
            if curr_level < warn_level:
                health_value = 0
                err_type = 'OK'
                health_message = err_type + ': System Load average is at ' + str(curr_level) + ' percent of available  resources'
                self.jsondata.send_special("Load-Average", self.timestamp, health_value, health_message, err_type)
            if warn_level <= curr_level < crit_level:
                health_value = 8
                err_type = 'WARNING'
                health_message = err_type + ': System Load average is at ' + str(curr_level) + ' percent of available  resources'
                self.jsondata.send_special("Load-Average", self.timestamp, health_value, health_message, err_type)
            if curr_level >= crit_level:
                health_value = 16
                err_type = 'ERROR'
                health_message = err_type + ': System Load average is at ' + str(curr_level) + ' percent of available  resources'
                self.jsondata.send_special("Load-Average", self.timestamp, health_value, health_message, err_type)

            self.local_vars.append({'name': 'sys_load_1', 'timestamp': self.timestamp, 'value': proc_loadavg[0]})
            self.local_vars.append({'name': 'sys_load_5', 'timestamp': self.timestamp, 'value': proc_loadavg[1], 'reaction': reaction})
            self.local_vars.append({'name': 'sys_load_15', 'timestamp': self.timestamp, 'value': proc_loadavg[2], 'reaction': reaction})

            loadavg.close()
        except Exception as e:
            lib.pushdata.print_error(__name__ , (e))
            pass