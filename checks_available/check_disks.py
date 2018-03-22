import lib.getconfig
import lib.pushdata
import lib.record_rate
import lib.puylogger
import lib.basecheck
import os
import re

check_type = 'system'

reaction = -3
warn_percent = float(lib.getconfig.getparam('Disk Stats', 'high'))
crit_percent = float(lib.getconfig.getparam('Disk Stats', 'severe'))
static_alerts = lib.getconfig.getparam('Disk Stats', 'static_enabled')
rated = True

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        rate = lib.record_rate.ValueRate()
        devices_blocks = {}
        try:
            for device in os.listdir('/sys/block'):
                if 'ram' not in device and 'loop' not in device:
                    devblk = open('/sys/block/'+device+'/queue/hw_sector_size', 'r')
                    devices_blocks[device] = devblk.readline().rstrip('\n')
                    devblk.close()
    
            for key, value in list(devices_blocks.items()):
                statsfile = open('/sys/block/' + key + '/stat', 'r')
                stats = statsfile.readline().split()
                read_bytes = int(stats[2]) * int(value)
                write_bytes = int(stats[6]) * int(value)
                if rated is True:
                    read_rate = rate.record_value_rate('drive_reads_' + key, read_bytes, self.timestamp)
                    write_rate = rate.record_value_rate('drive_writes_' + key, write_bytes, self.timestamp)
                    self.local_vars.append({'name': 'drive_reads', 'timestamp': self.timestamp, 'value': read_rate, 'reaction': reaction, 'extra_tag':{'drive': key}})
                    self.local_vars.append({'name': 'drive_writes', 'timestamp': self.timestamp, 'value': write_rate, 'reaction': reaction, 'extra_tag':{'drive': key}})

                else:
                    self.local_vars.append({'name': 'drive_reads', 'timestamp': self.timestamp, 'value': read_bytes, 'reaction': reaction, 'extra_tag':{'drive': key}})
                    self.local_vars.append({'name': 'drive_writes', 'timestamp': self.timestamp, 'value': write_bytes, 'reaction': reaction, 'extra_tag':{'drive': key}})

                statsfile.close()

            d = []
            mount = open('/proc/mounts', 'r')

            for l in mount:
                olo = l.split()
                if '/' in olo[0]:
                    d.append(olo[1])

            mount.close()

            def disk_usage(path):
                st = os.statvfs(path)
                free = st.f_bavail * st.f_frsize
                total = st.f_blocks * st.f_frsize
                used = (st.f_blocks - st.f_bfree) * st.f_frsize
                du = '{:.2f}'.format(used * 100 / total)
                return total, used, free, du

            for u in d:
                mrtrics = disk_usage(u)
                if u == '/':
                    name = 'rootfs'
                else:
                    name = u.strip('/').replace('/', '_')
                if static_alerts:
                    if warn_percent <= float(mrtrics[3]) < crit_percent:
                        err_type = 'WARNING'
                        health_value = 8
                        health_message = err_type + ': Storage usage of ' + u + ' is at ' + str(mrtrics[3]) + ' percent of available  space'
                        self.jsondata.send_special("Disk-Usage-" + name, self.timestamp, health_value, health_message, err_type, -self.error_handler)
                    if float(mrtrics[3]) >= crit_percent:
                        err_type = 'ERROR'
                        health_value = 16
                        health_message = err_type + ': Storage usage of ' + u + ' is at ' + str(mrtrics[3]) + ' percent of available  space'
                        self.jsondata.send_special("Disk-Usage-" + name, self.timestamp, health_value, health_message, err_type, -self.error_handler)

                self.local_vars.append({'name': 'drive_bytes_used', 'timestamp': self.timestamp, 'value': mrtrics[1], 'reaction': reaction , 'extra_tag':{'mountpoint': name}})
                self.local_vars.append({'name': 'drive_bytes_available', 'timestamp': self.timestamp, 'value': mrtrics[2], 'reaction': reaction, 'extra_tag': {'mountpoint': name}})
                self.local_vars.append({'name': 'drive_percent_used','timestamp': self.timestamp, 'value': mrtrics[3], 'chart_type': 'Percent', 'extra_tag': {'mountpoint': name}})


            proc_stats = open('/proc/diskstats')
            for line in proc_stats:
                if "loop" not in line:
                    fields = line.strip().split()
                    name = 'drive_'+fields[2]+'_io_percent'
                    regexp = re.compile(r'\d')
                    if regexp.search(name) is None:
                        value = fields[12]
                        reqrate = rate.record_value_rate(name, value, self.timestamp)
                        diskrate = '{:.2f}'.format(reqrate/10)
                        self.local_vars.append({'name': 'drive_io_percent_used', 'timestamp': self.timestamp, 'value': diskrate,  'chart_type': 'Percent', 'extra_tag': {'drive': fields[2]}})
            proc_stats.close()
        except Exception as e:
            lib.pushdata.print_error(__name__ , (e))
            pass
