import urllib2
import os
import ConfigParser
import socket
import subprocess
import time

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0] + '/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0] + '/conf/java.ini')

hostname = socket.getfqdn()
jmxj_url = config.get('JMXJ', 'jmxj')

cluster_name = config.get('SelfConfig', 'cluster_name')

jarfile= os.path.dirname(os.path.realpath("__file__")) + '/../lib/agent.jar'

def do_joloikia(java,juser,jclass):
    def get_pid():
        ps = subprocess.Popen(['sudo', '-u', juser, java, '-jar', jarfile, 'list', '|', 'grep', jclass], stdout=subprocess.PIPE).communicate()[0]
        for item in ps.split('\n'):
            if not item.find("agent.jar") != -1:
                if len(item) > 0:
                    return item.split()[0]
    jpid = get_pid()
    def jolostart():
        os.system('sudo -u ' + juser + ' ' + java + ' -jar ' + jarfile + ' --port 7777  --agentContext /puypuy/ start ' + str(jpid) +  ' > /dev/null  2>&1')

    time.sleep(1)

    try:
        if urllib2.urlopen(jmxj_url).getcode() is not 200:
            jolostart()
    except:
        jolostart()
