import datetime
import psutil, os, sys
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'system'
alert_level = -3
warn_percent = 80

def run_disk():
    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
    push = __import__('pushdata')
    value_rate= __import__('record_rate')
    jsondata=push.JonSon()
    jsondata.create_data()
    rate=value_rate.ValueRate()
    timestamp = int(datetime.datetime.now().strftime("%s"))
    try:
        partitions = psutil.disk_partitions()
        for index in range(0, len(partitions)):
            disk=tuple(partitions[index])[1]
            if disk == '/':
                diskname='_root'
                roottuple=tuple(psutil.disk_usage(disk))
                jsondata.gen_data('drive'+diskname+'_used_bytes', timestamp, roottuple[1], push.hostname, check_type, cluster_name, alert_level)
                jsondata.gen_data('drive'+diskname+'_free_bytes', timestamp, roottuple[2], push.hostname, check_type, cluster_name, alert_level)
                jsondata.gen_data('drive'+diskname+'_pecent', timestamp, roottuple[3], push.hostname, check_type, cluster_name, warn_percent)
            else:
                diskname=disk.replace("/", "_")
                disktuple=tuple(psutil.disk_usage(disk))
                jsondata.gen_data('drive'+diskname+'_used_bytes', timestamp, disktuple[1], push.hostname, check_type, cluster_name, alert_level)
                jsondata.gen_data('drive'+diskname+'_free_bytes', timestamp, disktuple[2], push.hostname, check_type, cluster_name, alert_level)
                jsondata.gen_data('drive'+diskname+'_pecent', timestamp, disktuple[3], push.hostname, check_type, cluster_name, alert_level)


        proc_stats=open('/proc/diskstats')
        for line in proc_stats:
            if "loop" not  in line:
                fields = line.strip().split()
                name='drive_'+(fields)[2]+'_percent'
                value=(fields)[12]
                reqrate=rate.record_value_rate(name, value, timestamp)
                if isinstance( reqrate, int ):
                    diskrate=reqrate/10
                    jsondata.gen_data(name, timestamp, diskrate, push.hostname, check_type, cluster_name, warn_percent)

        disks=psutil.disk_io_counters(perdisk=True)
        for key, value in disks.iteritems():
            tvalue=tuple(value)
            read_name='drive_'+key+'_read_bytes'
            write_name='drive_'+key+'_write_bytes'
            readrate=rate.record_value_rate(read_name, tvalue[2], timestamp)
            writerate=rate.record_value_rate(write_name, tvalue[3], timestamp)
            jsondata.gen_data(read_name, timestamp, readrate, push.hostname, check_type, cluster_name, alert_level)
            jsondata.gen_data(write_name, timestamp, writerate, push.hostname, check_type, cluster_name, alert_level)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
