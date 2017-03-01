import datetime
import os, sys, re
import ConfigParser
import subprocess
import lib.pushdata
import lib.record_rate


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'system'

# ------------------------ #
reaction = -3
warn_percent = 80
rated = True
io_warning_percent = 40
# ------------------------ #

def run_disks():
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    jsondata=lib.pushdata.JonSon()
    jsondata.prepare_data()
    rate=lib.record_rate.ValueRate()
    timestamp = int(datetime.datetime.now().strftime("%s"))
    devices_blocks={}
    try:
        for device in os.listdir('/sys/block'):
            if 'ram' not in device and 'loop' not in device:
                devices_blocks[device] = open('/sys/block/'+device+'/queue/hw_sector_size', 'r').readline().rstrip('\n')

        for key, value in devices_blocks.iteritems():
            stats=open('/sys/block/' + key + '/stat', 'r').readline().split()
            read_bytes=int(stats[2]) * int(value)
            write_bytes = int(stats[6]) * int(value)
            if rated is True:
                reads='drive_'+key+'_bytes_read'
                writes='drive_'+key+'_bytes_write'
                read_rate = rate.record_value_rate(reads, read_bytes, timestamp)
                write_rate = rate.record_value_rate(writes, write_bytes, timestamp)

                jsondata.gen_data(reads,  timestamp, read_rate, lib.pushdata.hostname, check_type, cluster_name, reaction)
                jsondata.gen_data(writes, timestamp, write_rate, lib.pushdata.hostname, check_type, cluster_name, reaction)
            else:
                jsondata.gen_data(reads,  timestamp, read_bytes, lib.pushdata.hostname, check_type, cluster_name, reaction)
                jsondata.gen_data(writes, timestamp, write_bytes, lib.pushdata.hostname, check_type, cluster_name, reaction)

        command = 'df'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()
        for i in output.split("\n"):
            if i.startswith('/'):
                u = re.sub(' +', ' ', i).split(" ")
                jsondata.gen_data('drive' + u[0].replace('/dev/', '_') + '_bytes_used', timestamp, u[2], lib.pushdata.hostname, check_type, cluster_name, reaction)
                jsondata.gen_data('drive' + u[0].replace('/dev/', '_') + '_bytes_available', timestamp, u[3], lib.pushdata.hostname, check_type, cluster_name, reaction)
                jsondata.gen_data('drive' + u[0].replace('/dev/', '_') + '_percent_used', timestamp, u[4].replace('%', ''), lib.pushdata.hostname, check_type, cluster_name, warn_percent, 'Percent')

        proc_stats=open('/proc/diskstats')
        for line in proc_stats:
            if "loop" not  in line:
                fields = line.strip().split()
                name='drive_'+(fields)[2]+'_io_percent'
                regexp = re.compile(r'\d')
                if regexp.search(name) is None:
                    value=(fields)[12]
                    reqrate=rate.record_value_rate(name, value, timestamp)
                    if isinstance( reqrate, int ):
                        diskrate=reqrate/10
                        jsondata.gen_data(name, timestamp, diskrate, lib.pushdata.hostname, check_type, cluster_name,0 ,'Percent')

        jsondata.put_json()

    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass