import subprocess
import json
import ConfigParser
import os, sys, datetime
import socket

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

ceph_client = config.get('Ceph', 'client')
ceph_keyring = config.get('Ceph', 'keyring')
cluster_name = config.get('SelfConfig', 'cluster_name')
hostname = socket.getfqdn()

check_type = 'ceph'


def run_ceph():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        jsondata=push.JonSon()
        jsondata.create_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        command='ceph -n ' + ceph_client +' --keyring='+ ceph_keyring + ' pg stat -f json'
        #command='cat' + ' /tmp/rados.json'

        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()
        stats=json.loads(output)


        jsondata.gen_data('ceph_num_bytes', timestamp, stats['num_bytes'], push.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_num_pgs', timestamp, stats['num_pgs'], push.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_raw_bytes', timestamp, stats['raw_bytes'], push.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_raw_bytes_avail', timestamp, stats['raw_bytes_avail'], push.hostname, check_type, cluster_name)
        jsondata.gen_data('ceph_raw_bytes_used', timestamp, stats['raw_bytes_used'], push.hostname, check_type, cluster_name)

        if 'io_sec' in  stats:
            jsondata.gen_data('ceph_io_sec', timestamp, stats['io_sec'], push.hostname, check_type, cluster_name)
        else:
            jsondata.gen_data('ceph_io_sec', timestamp, 0, push.hostname, check_type, cluster_name)
        if 'read_bytes_sec' in  stats:
            jsondata.gen_data('ceph_read_bytes_sec', timestamp, stats['read_bytes_sec'], push.hostname, check_type, cluster_name)
        else:
            jsondata.gen_data('ceph_read_bytes_sec', timestamp, 0, push.hostname, check_type, cluster_name)
        if 'write_bytes_sec' in  stats:
            jsondata.gen_data('ceph_write_bytes_sec', timestamp, stats['write_bytes_sec'], push.hostname, check_type, cluster_name)
        else:
            jsondata.gen_data('ceph_write_bytes_sec', timestamp, 0, push.hostname, check_type, cluster_name)

        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

