import lib.getconfig
import lib.pushdata
import lib.record_rate
import lib.puylogger
import datetime
import os
import re

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'system'

reaction = -3
warn_percent = float(lib.getconfig.getparam('System Thresholds', 'du_high'))
crit_percent = float(lib.getconfig.getparam('System Thresholds', 'du_severe'))
rated = True
# io_warning_percent = 40


def runcheck():
    local_vars = []
    jsondata = lib.pushdata.JonSon()
    jsondata.prepare_data()
    rate = lib.record_rate.ValueRate()
    timestamp = int(datetime.datetime.now().strftime("%s"))
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
            # reads = 'drive_' + key + '_bytes_read'
            # writes = 'drive_' + key + '_bytes_write'
            if rated is True:
                read_rate = rate.record_value_rate('drive_reads_' + key, read_bytes, timestamp)
                write_rate = rate.record_value_rate('drive_writes_' + key, write_bytes, timestamp)
                local_vars.append({'name': 'drive_reads', 'timestamp': timestamp, 'value': read_rate, 'reaction': reaction, 'extra_tag':{'device': key}})
                local_vars.append({'name': 'drive_writes', 'timestamp': timestamp, 'value': write_rate, 'reaction': reaction, 'extra_tag':{'device': key}})

            else:
                local_vars.append({'name': 'drive_reads', 'timestamp': timestamp, 'value': read_bytes, 'reaction': reaction, 'extra_tag':{'device': key}})
                local_vars.append({'name': 'drive_writes', 'timestamp': timestamp, 'value': write_bytes, 'reaction': reaction, 'extra_tag':{'device': key}})

            statsfile.close()

        d = []
        mount = open('/proc/mounts', 'r')

        for l in mount:
            if l[0] == '/':
                l = l.split()
                d.append(l[1])

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
                name = u.replace('/', '')
            if float(mrtrics[3]) < warn_percent:
                health_value = 0
                err_type = 'OK'
                # health_message = err_type + ': System Load average is at ' + str(curr_level) + ' percent of available  resources'
                health_message = err_type + ': Storage usage of ' + u + ' is at ' + str(mrtrics[3]) + ' percent of available  space'
                jsondata.send_special("Disk-Usage", timestamp, health_value, health_message, err_type)
            if warn_percent <= float(mrtrics[3]) < crit_percent:
                err_type = 'WARNING'
                health_value = 8
                health_message = err_type + ': Storage usage of ' + u + ' is at ' + str(mrtrics[3]) + ' percent of available  space'
                jsondata.send_special("Disk-Usage", timestamp, health_value, health_message, err_type)
            if float(mrtrics[3]) >= crit_percent:
                health_value = 16
                err_type = 'ERROR'
                health_message = err_type + ': Storage usage of ' + u + ' is at ' + str(mrtrics[3]) + ' percent of available  space'
                jsondata.send_special("Disk-Usage", timestamp, health_value, health_message, err_type)

            local_vars.append({'name': 'drive_bytes_used', 'timestamp': timestamp, 'value': mrtrics[1], 'reaction': reaction , 'extra_tag':{'device': name}})
            local_vars.append({'name': 'drive_bytes_available', 'timestamp': timestamp, 'value': mrtrics[2], 'reaction': reaction, 'extra_tag': {'device': name}})
            local_vars.append({'name': 'drive_percent_used','timestamp': timestamp, 'value': mrtrics[3], 'chart_type': 'Percent', 'extra_tag': {'device': name}})


        proc_stats = open('/proc/diskstats')
        for line in proc_stats:
            if "loop" not in line:
                fields = line.strip().split()
                name = 'drive_'+fields[2]+'_io_percent'
                regexp = re.compile(r'\d')
                if regexp.search(name) is None:
                    value = fields[12]
                    reqrate = rate.record_value_rate(name, value, timestamp)
                    # if isinstance(reqrate, int):
                    diskrate = reqrate/10
                    local_vars.append({'name': 'drive_io_percent_used', 'timestamp': timestamp, 'value': diskrate,  'chart_type': 'Percent', 'extra_tag': {'device': fields[2]}})
        proc_stats.close()
        return  local_vars
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass


