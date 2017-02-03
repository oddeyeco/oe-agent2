import urllib2, time
from threading import Thread
import threading
from Queue import Queue

# Set up global variables
num_threads = 5 #you can set it to any number of threads (although 1 would be enough)

queue = Queue()
url_list = [
    "http://google.com",
    "http://netangels.net"
]


def notify(i, q):
    url = q.get()
    print "Thread %d: notification sent for site: %s" % (i, url)
    q.task_done()


def thread_func(i, q):
    print "Thread %d: started" % i
    while True:
        notify(i, q)
    print "Thread %d: ending" % i

def make_requests():
    while True:
        for url in url_list:
            try:
                request = urllib2.urlopen(url)
                response_code = request.getcode()
                print response_code, threading.current_thread().name, threading.activeCount()
            except Exception as e:
                print "ERROR MAKING REQUEST TO %s - %s" % (url, e)
                queue.put(url)
        time.sleep(10)  # wait 10 seconds and start again


if __name__ == "__main__":
    # Set up some threads to fetch the enclosures
    for i in xrange(num_threads):
        worker = Thread(target=thread_func, args=(i, queue))
        worker.setDaemon(True)
        worker.start()

#    make_requests()