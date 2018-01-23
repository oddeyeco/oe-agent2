import glob
import os
import datetime
import time
import subprocess
import lib.pushdata
import lib.puylogger
import lib.record_rate
import lib.getconfig


sh_home=os.path.split(os.path.dirname(__file__))[0]+'/scripts_enabled'
shell_scripts=glob.glob(sh_home+"/check_*")

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
log_file = lib.getconfig.getparam('SelfConfig', 'log_file')


def run_shell_scripts(runscripts=True):
    local_vars = []
    try:
        if len(shell_scripts) is 0:
            pass
        else:
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
                    check_style=new_split[3]
                    if check_style == 'stack':
                        local_vars.append({'name': mytype, 'timestamp': timestamp, 'value': myvalue, 'host': lib.pushdata.hostname})
                    elif check_style == 'rate':
                        sh_rate=rate.record_value_rate(mytype, myvalue, timestamp)
                        local_vars.append({'name': mytype, 'timestamp': timestamp, 'value': sh_rate, 'host': lib.pushdata.hostname})
                    else:
                        print('lololololo')
                time_elapsed = "{:.9f}".format(time.time() - start_time) + " seconds"
                shell_script_name = shell_script.rsplit('/')[-1]
                message = time_elapsed +' ' + str(shell_script_name)
                lib.puylogger.print_message(message)
        return local_vars
    except Exception as e:
        lib.pushdata.print_error(__name__, (e))
        pass
