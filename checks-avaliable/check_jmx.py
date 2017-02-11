# Requires jpype, Please install it (apt-get install python-jpype)
import os, sys
import ConfigParser
import datetime
import socket

import jpype
from jpype import java
from jpype import javax

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/java.ini')

HOST= config.get('JMX', 'host')
PORT= config.get('JMX', 'port')
USER= config.get('JMX', 'user')
PASS= config.get('JMX', 'pass')
TYPE= config.get('JMX', 'gctype')
JAVA= config.get('JMX', 'java_home')
URL = 'service:jmx:rmi:///jndi/rmi://'+HOST+':'+PORT+'/jmxrmi'

hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'jmx'

if TYPE == 'G1':
    CMS=False
    G1=True
if TYPE == 'CMS':
    CMS=True
    G1=False

os.environ['JAVA_HOME'] = JAVA

JAVA = config.get('JMX', 'java_home')


def init_jvm(jvmpath=None):
    if jpype.isJVMStarted():
        return
    else:
        jpype.startJVM(jpype.getDefaultJVMPath())
    if not jpype.isThreadAttachedToJVM():
        jpype.attachThreadToJVM()

init_jvm()


def try_connection():
    try:
        os.environ['JAVA_HOME'] = JAVA
        jhash = java.util.HashMap()
        jarray = jpype.JArray(java.lang.String)([USER, PASS])
        jhash.put(javax.management.remote.JMXConnector.CREDENTIALS, jarray);
        jmxurl = javax.management.remote.JMXServiceURL(URL)
        jmxsoc = javax.management.remote.JMXConnectorFactory.connect(jmxurl, jhash)
        global connection
        connection = jmxsoc.getMBeanServerConnection();
    except Exception as e:
        pass
        connection = None
        push = __import__('pushdata')
        push.print_error(__name__, (e))
try_connection()

def run_jmx():
    def run_all(connection):
        try:
            sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
            push = __import__('pushdata')
            value_rate= __import__('record_rate')
            rate=value_rate.ValueRate()
            jsondata=push.JonSon()
            jsondata.create_data()
            timestamp = int(datetime.datetime.now().strftime("%s"))

            object = 'java.lang:type=Memory'
            attribute = 'HeapMemoryUsage'
            attr = connection.getAttribute(javax.management.ObjectName(object), attribute)

            heap_attributes=('used', 'committed', 'init', 'max')
            for heap in heap_attributes:
                value = str(attr.contents.get(heap))
                jsondata.gen_data('jmx_heap_'+ heap, timestamp, value, push.hostname, check_type, cluster_name)

            threads_bean = 'java.lang:type=Threading'
            threads_mbeans=('PeakThreadCount', 'DaemonThreadCount', 'ThreadCount')
            for mbean in threads_mbeans:
                value = str(connection.getAttribute(javax.management.ObjectName(threads_bean), mbean))
                jsondata.gen_data('jmx_'+ mbean, timestamp, value, push.hostname, check_type, cluster_name)

            if CMS is True:
                object = 'java.lang:type=GarbageCollector,name=ConcurrentMarkSweep'
                GcCount = 'CollectionCount'
                ColCount = str(connection.getAttribute(javax.management.ObjectName(object), GcCount))
                jsondata.gen_data('jmx_CMSGcCount', timestamp, ColCount, push.hostname, check_type, cluster_name)

                GcTime = 'CollectionTime'
                ColTime = connection.getAttribute(javax.management.ObjectName(object), GcTime)

                GcTime_rate = rate.record_value_rate('jmx_CMSGcTime', ColTime.value, timestamp)
                jsondata.gen_data('jmx_CMSGcTime', timestamp, GcTime_rate, push.hostname, check_type, cluster_name)
                try:
                    object = 'java.lang:type=GarbageCollector,name=ParNew'
                    PnGcCount = 'CollectionCount'
                    PnColCount = connection.getAttribute(javax.management.ObjectName(object), PnGcCount)

                    PnGcTime = 'CollectionTime'
                    PnColTime = connection.getAttribute(javax.management.ObjectName(object), PnGcTime)
                    PnColTime_value=str(PnColTime.value)
                    strPnColCount=str(PnColCount)
                    jsondata.gen_data('jmx_' + 'ParNewGcCount', timestamp, strPnColCount, push.hostname, check_type, cluster_name)
                    GcTime_rate = rate.record_value_rate('jmx_ParNewGcTime', PnColTime_value, timestamp)
                    jsondata.gen_data('jmx_ParNewGcTime', timestamp, GcTime_rate, push.hostname, check_type, cluster_name, 0, 'Rate')

                except Exception as e:
                    push = __import__('pushdata')
                    push.print_error(__name__, (e))

            if G1 is True:
                object = 'java.lang:type=GarbageCollector,name=G1 Old Generation'
                OldGcCount = 'CollectionCount'
                OldColCount = str(connection.getAttribute(javax.management.ObjectName(object), OldGcCount))

                OldGcTime = 'CollectionTime'
                OldColTime = connection.getAttribute(javax.management.ObjectName(object), OldGcTime)

                jsondata.gen_data('jmx_G1_' + 'OldGcCount', timestamp, OldColCount, push.hostname, check_type, cluster_name)
                OldGcTime_rate = rate.record_value_rate('jmx_G1_OldGcTime', OldColTime.value, timestamp)
                jsondata.gen_data('jmx_G1_OldGcTime', timestamp, str(OldGcTime_rate), push.hostname, check_type, cluster_name, 0, 'Rate')

                object = 'java.lang:type=GarbageCollector,name=G1 Young Generation'
                YoungGcCount = 'CollectionCount'
                YoungColCount = connection.getAttribute(javax.management.ObjectName(object), YoungGcCount)

                YoungGcTime = 'CollectionTime'
                YoungColTime = connection.getAttribute(javax.management.ObjectName(object), YoungGcTime)

                jsondata.gen_data('jmx_G1_' + 'YoungGcCount', timestamp, str(YoungColCount), push.hostname, check_type, cluster_name)
                YoungColTime_rate = rate.record_value_rate('jmx_G1_YoungColTime', YoungColTime.value, timestamp)
                jsondata.gen_data('jmx_G1_YoungGcTime', timestamp, YoungColTime_rate, push.hostname, check_type, cluster_name, 0, 'Rate')

            jsondata.put_json()
            jsondata.truncate_data()
        except Exception as e:
            push = __import__('pushdata')
            push.print_error(__name__, (e, java.rmi.ConnectException))
            try_connection()
            pass
    run_all(connection)

