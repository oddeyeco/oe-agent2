import subprocess
import datetime
import lib.getconfig
import lib.puylogger
import lib.pushdata

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'system'
btrfsbinary = '/sbin/btrfs'
enable_special = True
warn_level = 2
crit_level = 5


def runcheck():
    local_vars = []
    try:
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()

        bfsvolumes = []
        timestamp = int(datetime.datetime.now().strftime("%s"))
        get_btrfs_volume = 'mount'
        g1 = subprocess.Popen(get_btrfs_volume, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        output, err = g1.communicate()
        for bfs in output.splitlines():
            if 'btrfs' in bfs:
                volume = bfs.split()[2]
                bfsvolumes.append(volume)
        g1.stdout.close()

        def send_special(value, key):
            if int(value) >= warn_level < crit_level:
                health_value = 8
                health_message = 'Warning : BTRFS may be corrupted with ' + str(value) + ' IO Errors on ' + key
                jsondata.send_special("BTRFS ", timestamp, health_value, health_message, 'WARNING')
            if int(value) >= crit_level:
                health_value = 16
                health_message = 'Critical : BTRFS is corrupted with ' + str(value) + ' IO Errors on ' + key
                jsondata.send_special("BTRFS ", timestamp, health_value, health_message, 'ERROR')

        for bfsvolume in bfsvolumes:
            get_btrfs_stats = btrfsbinary + ' device stats ' + bfsvolume
            g2 = subprocess.Popen(get_btrfs_stats, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output, err = g2.communicate()
            for out in output.splitlines():
                key = out.replace('.', '_').replace('/', '_').replace('[', '').replace(']', '').split()[0]
                value = out.replace('.', '_').replace('/', '_').replace('[', '').replace(']', '').split()[1]
                local_vars.append({'name': 'btrfs' + key, 'timestamp': timestamp, 'value': value, 'check_type': check_type})
                if enable_special is True:
                    send_special(value, key)
            g2.stdout.close()

        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

