**PuyPuy**
---------
PuyPuy is python2 metrics collection daemon, which works with KairosDB, OpenTSDB, Graphite and InfluxDB, For InfluxDB, KairosDB and OpenTSDB it uses REST interface, for Graphite Pickle.

Main idea behind PuyPuy is simplicity and less as possible dependencies, it is tested on Debian and Ubuntu systems, but should work on any Linux system.   

To install PuyPuy just clone our repository, make sure that you have few python dependency modules (pycurl, psutil v1+, daemon) for base program.
On Debian/Ubuntu systems following will do the trick 

	apt-get install python-psutil python-daemon python-pycurl 

Special note for Debian 7 users: psutil in Debian 7 is very old, please uses pip to install psutils or get it from our repository: 

http://apt.netangels.net/pool/main/p/python-psutil/python-psutil_2.1.1-1_amd64.deb

If you use specific checks like check_mysql, MySQLdb should also be installed.
Make your changes if needed in config.ini and run 

    ./puypuy.sh start
     
Python daemon process will start, run all python scripts from checks_avaliable directory as well as all check_* files scripts_available directory. 

**Create own python module :**

Create file in checks_enabled directory with namecheck_checkname.py, inside script you should have function with name run_checkname(Here you actual check should live). 
Your check should contain some  minimal imports in order to talk to main program: 

	hostname = socket.getfqdn()
	cluster_name = config.get('SelfConfig', 'cluster_name')
	check_type = 'test'

	def run_checkname()
	    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
	    push = __import__('pushdata')
	    jsondata=push.JonSon()
	    jsondata.create_data()
	    timestamp = int(datetime.datetime.now().strftime("%s"))
		name='CheckName'
	    value=10

This will import needed libs to generate and send to time series server needed json files, so you do not have to deal with generating and pushing it manually. 

After grabbing needed metrics, send it to uploader (pushdata.py) by calling 
			
	jsondata.gen_data(name, timestamp, value, push.hostname, check_type,cluster_name)

Next push data to TSDB and truncate local copy: 

	jsondata.put_json()
	jsondata.truncate_data()

**Create scripts which calculates value rates :** 

	def run_checkname_rate()
	    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
	    push = __import__('pushdata')
	    value_rate= __import__('record_rate')
	    rate=value_rate.ValueRate()
	    jsondata=push.JonSon()
	    jsondata.create_data()
	    name='some_metric'
	    value=10 # Values needed for calculations rate 
	    timestamp = int(datetime.datetime.now().strftime("%s"))
	    value_rate=rate.record_value_rate(key, value, timestamp)
		jsondata.gen_data(key, timestamp, value_rate, push.hostname, check_type, cluster_name)
	jsondata.put_json()
	jsondata.truncate_data()

**Create any scripts:**

To run custom script  like Bash, Perl etc.. Create scripts in format *check_name.extension* in folder scripts_enabled. 
All is needed from custom is to system out values in right order, Below is sample Bash scripts, which generates random number and send to collector for graphing:

	#!/bin/bash
		
	myvalue=$RANDOM
	mytype=random_gen
	check_type=my_bash_random
	check_style=stack
	
	myvalue2=$RANDOM
	mytype2=random_gen2
	check_type2=my_bash_random2
	check_style2=rate
	
	echo $mytype $myvalue $check_type $check_style
	echo -n $mytype2 $myvalue2 $check_type2 $check_style2

**Configuration:**

PuyPuy uses single ini file for self and metrics specific configurations. Configs are splitted into sections. 
Section [SelfConfig] contains base config parameters like checks interval, log/pid file location as well as some basic tags. 

    [SelfConfig]
    check_period_seconds: 5
    log_file: /tmp/testdaemon.log
    pid_file: /tmp/tsdclient.pid
    cluster_name: netangels
    host_group: testing

cluster_name and host_group are placeholders for tags for better manageability. Like if you need to tag web-servers of put web-servers in separate folder in Carbon. 

In section [TSDB] you should set correct backend and uri. 

OpenTSDB: Enable chunked requests in OpenTSDB 

opentsdb.conf

	tsd.http.request.enable_chunked = true

config.ini

	[TSDB]
	address: http://opentsdb_address:4242
	datapoints: /api/put
	user: netangels
	pass: bololo
	auth: False
	tsdtype: OpenTSDB

KairosDB : Enable or disable auth: in accordance to your KairosDB setup 

	[TSDB]
	address: http://kairosdb_address:8088
	datapoints: /api/v1/datapoints
	user: netangels
	pass: bololo
	auth: True
	tsdtype: KairosDB

Graphite Carbon: (PuyPuy uses Carbon pickle, default port is 2004)

	[TSDB]
	address: carbon_host:2004
	user: netangels
	pass: bololo
	auth: false
	tsdtype: Carbon

InfluxDB: (Authentication is not supported yet, You must create database manually before sending to it metrics)

	[TSDB]
	user: netangels
	pass: bololo
	auth: False
	address: http://influxdb_host:8086
	database: netangels
	tsdtype: InfluxDB
