import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
host_group = config.get('SelfConfig', 'host_group')
host = config.get('ElasticSearch', 'host')
stats = config.get('ElasticSearch', 'stats')
elastic_url = host + stats
check_type = 'elasticsearch'
reaction = -3

def run_elasticsearch():
    try:
        elastic_stats = urllib2.urlopen(elastic_url, timeout=5).read()
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        value_rate= __import__('record_rate')
        rate=value_rate.ValueRate()
        jsondata=push.JonSon()
        jsondata.create_data()
        stats_json = json.loads(elastic_stats)
        node_keys = stats_json['nodes'].keys()[0]
        data = {}
        rated_stats = {}
        timestamp = int(datetime.datetime.now().strftime("%s"))

        # -------------------------------------------------------------------------------------------------------------------- #
        def send_special():
            eshealth_status = host + '/_cluster/health'
            eshealth_stat = urllib2.urlopen(eshealth_status, timeout=2)
            eshealth_stats = eshealth_stat.read()
            eshealth_json = json.loads(eshealth_stats)

            status_code = eshealth_stat.getcode()
            if status_code != 200:
                eshealth_message = "Something is very bad, exited with status:", status_code
                health_value = 16
            else:
                status = eshealth_json['status']
                active_shards = eshealth_json['active_shards']
                relocating_shards = eshealth_json['relocating_shards']
                initializing_shards = eshealth_json['initializing_shards']
                cluster_name = eshealth_json['cluster_name']

                eshealth_message = 'Cluster: ' + cluster_name + ', Status: ' + status + ', Shards Active: ' + str(active_shards) + ', Relocating: ' + str(relocating_shards) + ', Initializing: ' + str(initializing_shards)

                if status == 'green':
                    health_value = 0
                    err_type = 'OK'
                elif status == 'yellow':
                    health_value = 8
                    err_type = 'WARNING'
                else:
                    health_value = 16
                    err_type = 'ERROR'
            jsondata.send_special("ElasticSearch-Health", timestamp, health_value, eshealth_message, err_type)
        send_special()
        # -------------------------------------------------------------------------------------------------------------------- #

        rated_stats.update({''
                    'search_total':stats_json['nodes'][node_keys]['indices']['search']['query_total'],
                    'index_total':stats_json['nodes'][node_keys]['indices']['indexing']['index_total'],
                    'refresh_total':stats_json['nodes'][node_keys]['indices']['refresh']['total'],
                    'get_total':stats_json['nodes'][node_keys]['indices']['get']['total'],
                    'fetch_total':stats_json['nodes'][node_keys]['indices']['search']['fetch_total'],
                    'fetch_time':stats_json['nodes'][node_keys]['indices']['search']['fetch_time_in_millis'],
                    'index_time':stats_json['nodes'][node_keys]['indices']['indexing']['index_time_in_millis'],
                    'search_search_time':stats_json['nodes'][node_keys]['indices']['search']['query_time_in_millis'],
                    'merge_time':stats_json['nodes'][node_keys]['indices']['merges']['total_time_in_millis'],
                    'merge_docs':stats_json['nodes'][node_keys]['indices']['merges']['total_docs'],
                    'merge_size':stats_json['nodes'][node_keys]['indices']['merges']['total_size_in_bytes'],
                    'refresh_time':stats_json['nodes'][node_keys]['indices']['refresh']['total_time_in_millis'],
                    'filter_cache_evictions':stats_json['nodes'][node_keys]['indices']['filter_cache']['evictions'],
                    'get_time':stats_json['nodes'][node_keys]['indices']['get']['time_in_millis'],
                    'gc_young_time_ms':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['young']['collection_time_in_millis'],
                    'gc_old_time_ms':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['old']['collection_time_in_millis'],
                    'gc_young_count':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['young']['collection_count'],
                    'gc_old_count':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['old']['collection_count']
                            })

        for key, value in rated_stats.iteritems():
            reqrate=rate.record_value_rate('es_'+key, value, timestamp)
            if reqrate >=0:
                data.update({'elasticsearch_'+key: reqrate})

        data.update({''
                    'elasticsearch_heap_committed':stats_json['nodes'][node_keys]['jvm']['mem']['heap_committed_in_bytes'],
                    'elasticsearch_heap_used':stats_json['nodes'][node_keys]['jvm']['mem']['heap_used_in_bytes'],
                    'elasticsearch_non_heap_committed':stats_json['nodes'][node_keys]['jvm']['mem']['non_heap_committed_in_bytes'],
                    'elasticsearch_non_heap_used':stats_json['nodes'][node_keys]['jvm']['mem']['non_heap_used_in_bytes'],
                    'elasticsearch_open_files':stats_json['nodes'][node_keys]['process']['open_file_descriptors'],
                    'elasticsearch_http_connections':stats_json['nodes'][node_keys]['http']['current_open']
                     })
        for key, value in data.iteritems():
            if key =='elasticsearch_non_heap_used' or key=='elasticsearch_heap_used' or key=='elasticsearch_non_heap_committed' or key=='elasticsearch_heap_committed':
                jsondata.gen_data(key, timestamp, value, push.hostname, check_type, cluster_name, reaction)
            else:
                jsondata.gen_data(key, timestamp, value, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
