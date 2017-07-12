import subprocess
import json
import lib.getconfig
import datetime
import lib.puylogger

ceph_client = lib.getconfig.getparam('Ceph', 'client')
ceph_keyring = lib.getconfig.getparam('Ceph', 'keyring')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'ceph'


def runcheck():
    local_vars = []
    try:
        timestamp = int(datetime.datetime.now().strftime("%s"))
        command = 'ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' pg stat -f json'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        output, err = p.communicate()
        stats = json.loads(output)

        local_vars.append({'name': 'ceph_num_bytes', 'timestamp': timestamp, 'value': stats['num_bytes'], 'check_type': check_type})
        local_vars.append({'name': 'ceph_num_pgs', 'timestamp': timestamp, 'value': stats['num_pgs'], 'check_type': check_type})
        local_vars.append({'name': 'ceph_raw_bytes', 'timestamp': timestamp, 'value': stats['raw_bytes'], 'check_type': check_type})
        local_vars.append({'name': 'ceph_raw_bytes_avail', 'timestamp': timestamp, 'value': stats['raw_bytes_avail'], 'check_type': check_type})
        local_vars.append({'name': 'ceph_raw_bytes_used', 'timestamp': timestamp, 'value': stats['raw_bytes_used'], 'check_type': check_type})



        if 'io_sec' in stats:
            local_vars.append({'name': 'ceph_io_sec', 'timestamp': timestamp, 'value': stats['io_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
        else:
            local_vars.append({'name': 'ceph_io_sec', 'timestamp': timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
        if 'read_bytes_sec' in stats:
            local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': timestamp, 'value': stats['read_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
        else:
            local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
        if 'write_bytes_sec' in stats:
            local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': timestamp, 'value': stats['write_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
        else:
            local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})

        p.stdout.close()
        return  local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

