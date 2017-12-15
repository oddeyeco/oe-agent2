import datetime
import lib.getconfig
import lib.pushdata
import lib.record_rate
import lib.basecheck

# 0: user: normal processes executing in user mode
# 1: nice: niced processes executing in user mode
# 2: system: processes executing in kernel mode
# 3: idle: twiddling thumbs
# 4: iowait: waiting for I/O to complete
# 5: irq: servicing interrupts
# 6: softirq: servicing softirqs


class Check(lib.basecheck.CheckBase):

    def calcperraw(self,cpu_stats,rate,timestamp,local_vars,metrinames, device="all"):
        time = cpu_stats[0]+cpu_stats[1]+cpu_stats[2]+cpu_stats[3]
        rate_time = rate.record_value_delta("time"+device, time)
        if (rate_time==0):
            return
        rate_cpu_time = rate.record_value_delta("cpu_load"+device, cpu_stats[0] + cpu_stats[1] + cpu_stats[2])
        cpu_load = rate_cpu_time / rate_time * 100;
        local_vars.append(
            {'name': "cpu_load", 'timestamp': timestamp, 'value': cpu_load, 'chart_type': self.values_type, 'reaction': 0, 'extra_tag':{'device': device}})
        try:
            for index in range(0, len(metrinames)):
                name = metrinames[index]+device
                value = cpu_stats[index]
                if metrinames[index] == 'cpu_user' or metrinames[index] == 'cpu_iowait':
                    reaction = 0
                else:
                    reaction = -3

                values_rate = rate.record_value_delta(name, value)
                values_percent = (values_rate / rate_time *100)
                local_vars.append({'name': metrinames[index], 'timestamp': timestamp, 'value': values_percent, 'chart_type': self.values_type, 'reaction': reaction, 'check_type': self.check_type, 'extra_tag':{'device': device}})
        except Exception as e:
            lib.pushdata.print_error(__name__ , (e))
            pass

    def precheck(self):
        core_stats = []
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        with open("/proc/stat", "r") as crn:
            cpu_stats = [float(column) for column in crn.readline().strip().split()[1:]]
            for line in crn.readlines():
                if 'cpu' in line:
                    core_stats.append([float(column) for column in line.strip().split()[1:]])
        crn.close()

        self.metrics = ['cpu_user', 'cpu_nice', 'cpu_system', 'cpu_idle', 'cpu_iowait', 'cpu_irq', 'cpu_softirq']
        self.calcperraw(cpu_stats, rate, timestamp, self.local_vars, self.metrics)
        if self.per_cpu:
            for index in range(0, len(core_stats)):
                self.calcperraw(core_stats[index], rate, timestamp, self.local_vars, self.metrics,"core"+str(index))

        self.metrics.append("cpu_load");

    def __init__(self):
        self.check_type = 'system'
        self.values_type = 'Percent'
        self.static_alerts = lib.getconfig.getparam('CPU Stats', 'static_alerts')
        self.per_cpu = lib.getconfig.getparam('CPU Stats', 'per_cpu')
        self.warn_level = lib.getconfig.getparam('CPU Stats', 'warn_level')
        self.crit_level = lib.getconfig.getparam('CPU Stats', 'crit_level')