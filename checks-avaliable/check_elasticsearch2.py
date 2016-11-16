import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

elastic_url = config.get('ElasticSearch', 'stats')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'elasticsearch'
alert_level = -3

def run_elasticsearch2():
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
        #gc_young_time_ms=stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['young']['collection_time_in_millis']
        #gc_old_time_ms=stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['old']['collection_time_in_millis']
        timestamp = int(datetime.datetime.now().strftime("%s"))

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
                    'query_cache_evictions':stats_json['nodes'][node_keys]['indices']['query_cache']['evictions'],
                    'get_time':stats_json['nodes'][node_keys]['indices']['get']['time_in_millis'],
                    'gc_young_time_ms':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['young']['collection_time_in_millis'],
                    'gc_old_time_ms':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['old']['collection_time_in_millis'],
                    'gc_old_count':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['old']['collection_count'],
                    'gc_young_count':stats_json['nodes'][node_keys]['jvm']['gc']['collectors']['young']['collection_count'],
                    })
        #print rated_stats

        for key, value in rated_stats.iteritems():
            #jsondata.gen_data('es_'+key, timestamp, value, push.hostname, check_type, cluster_name)
            reqrate=rate.record_value_rate('es_'+key, value, timestamp)
            if reqrate >=0:
                data.update({'elasticsearch_'+key: reqrate})

        data.update({''
                    'elasticsearch_heap_commited':stats_json['nodes'][node_keys]['jvm']['mem']['heap_committed_in_bytes'],
                    'elasticsearch_heap_used':stats_json['nodes'][node_keys]['jvm']['mem']['heap_used_in_bytes'],
                    'elasticsearch_non_heap_commited':stats_json['nodes'][node_keys]['jvm']['mem']['non_heap_committed_in_bytes'],
                    'elasticsearch_non_heap_used':stats_json['nodes'][node_keys]['jvm']['mem']['non_heap_used_in_bytes'],
                    'elasticsearch_open_files':stats_json['nodes'][node_keys]['process']['open_file_descriptors'],
                    'elasticsearch_http_connections':stats_json['nodes'][node_keys]['http']['current_open']
                     })
        for key, value in data.iteritems():
            if key == 'elasticsearch_non_heap_used' or key == 'elasticsearch_heap_used' or key == 'elasticsearch_non_heap_committed' or key == 'elasticsearch_heap_committed':
                jsondata.gen_data(key, timestamp, value, push.hostname, check_type, cluster_name, alert_level)
            else:
                jsondata.gen_data(key, timestamp, value, push.hostname, check_type, cluster_name)
                #timestamp = int(datetime.datetime.now().strftime("%s"))
                #jsondata.gen_data(key, timestamp, value, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
