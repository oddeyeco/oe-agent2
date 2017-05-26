import subprocess
import json
import lib.getconfig
import datetime
import lib.pushdata


ceph_client = lib.getconfig.getparam('Ceph', 'client')
ceph_keyring = lib.getconfig.getparam('Ceph', 'keyring')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'ceph'


def runcheck():
    try:
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        command = 'ceph -n ' + ceph_client +' --keyring='+ ceph_keyring + ' pg stat -f json'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()
        stats = json.loads(output)
        jsondata.gen_data('ceph_num_bytes', timestamp, stats['num_bytes'], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_num_pgs', timestamp, stats['num_pgs'], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_raw_bytes', timestamp, stats['raw_bytes'], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_raw_bytes_avail', timestamp, stats['raw_bytes_avail'], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_raw_bytes_used', timestamp, stats['raw_bytes_used'], lib.pushdata.hostname, check_type, cluster_name)

        if 'io_sec' in  stats:
            jsondata.gen_data('ceph_io_sec', timestamp, stats['io_sec'], lib.pushdata.hostname, check_type, cluster_name)
        else:
            jsondata.gen_data('ceph_io_sec', timestamp, 0, lib.pushdata.hostname, check_type, cluster_name)
        if 'read_bytes_sec' in  stats:
            jsondata.gen_data('ceph_read_bytes_sec', timestamp, stats['read_bytes_sec'], lib.pushdata.hostname, check_type, cluster_name)
        else:
            jsondata.gen_data('ceph_read_bytes_sec', timestamp, 0, lib.pushdata.hostname, check_type, cluster_name)
        if 'write_bytes_sec' in  stats:
            jsondata.gen_data('ceph_write_bytes_sec', timestamp, stats['write_bytes_sec'], lib.pushdata.hostname, check_type, cluster_name)
        else:
            jsondata.gen_data('ceph_write_bytes_sec', timestamp, 0, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()
        p.stdout.close()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

