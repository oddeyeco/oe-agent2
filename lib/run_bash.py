import glob, os, sys, datetime
import time
import ConfigParser
import logging
from daemon import runner
import threading
import subprocess

sh_home=os.path.split(os.path.dirname(__file__))[0]+'/scripts-enabled'
#print sh_home

shell_scripts=glob.glob(sh_home+"/check_*")

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')

def run_shell_scripts():
    try:
        if len(shell_scripts) is 0:
            pass
        else:
            push = __import__('pushdata')
            value_rate= __import__('record_rate')
            jsondata=push.JonSon()
            jsondata.create_data()
            rate=value_rate.ValueRate()
            for shell_script in shell_scripts:
                timestamp = int(datetime.datetime.now().strftime("%s"))
                p = subprocess.Popen(shell_script, stdout=subprocess.PIPE, shell=True)
                output, err = p.communicate()
                bashvalues=output.split('\n')
                for index in range(0, len(bashvalues)):
                    new_split=bashvalues[index].split(' ')
                    mytype=new_split[0]
                    myvalue=new_split[1]
                    check_type=new_split[2]
                    check_style=new_split[3]
                    if check_style == 'stack':
                        jsondata.gen_data(mytype, timestamp, myvalue, push.hostname, check_type, cluster_name)
                    elif check_style == 'rate':
                        sh_rate=rate.record_value_rate(mytype, myvalue, timestamp)
                        jsondata.gen_data(mytype, timestamp, sh_rate, push.hostname, check_type, cluster_name)
                    else:
                        print 'lololololo'
            jsondata.put_json()
            jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(e)
        pass
