import glob, os, sys, datetime
import time
import ConfigParser
import subprocess
import pushdata
import puylogger
import lib.record_rate


sh_home=os.path.split(os.path.dirname(__file__))[0]+'/scripts_enabled'
shell_scripts=glob.glob(sh_home+"/check_*")

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')
log_file = config.get('SelfConfig', 'log_file')


def run_shell_scripts():
    try:
        if len(shell_scripts) is 0:
            pass
        else:
            jsondata=pushdata.JonSon()
            jsondata.prepare_data()
            rate=lib.record_rate.ValueRate()
            for shell_script in shell_scripts:
                start_time = time.time()
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
                        jsondata.gen_data(mytype, timestamp, myvalue, pushdata.hostname, check_type, cluster_name)
                    elif check_style == 'rate':
                        sh_rate=rate.record_value_rate(mytype, myvalue, timestamp)
                        jsondata.gen_data(mytype, timestamp, sh_rate, pushdata.hostname, check_type, cluster_name)
                    else:
                        print 'lololololo'
                time_elapsed = "{:.9f}".format(time.time() - start_time) + " seconds"
                shell_script_name = shell_script.rsplit('/')[-1]
                message = time_elapsed +' ' + str(shell_script_name)
                puylogger.print_message(message)
            jsondata.put_json()

    except Exception as e:
        pushdata.print_error(__name__, (e))
        pass
