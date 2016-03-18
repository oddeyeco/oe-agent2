#!/usr/bin/env bash
### BEGIN INIT INFO
# Provides: puypuy.sh
# Required-Start: $local_fs $network
# Should-Start: ypbind nscd ldap ntpd xntpd
# Required-Stop: $network
# Default-Start:  2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: start and stop TSD Client
# Description: TSD Client
### END INIT INFO#

# apt-get install  python-setproctitle

SCRIPT_DIR="$(cd $(dirname $0) && pwd)"
PYTHON=`which python`
cd $SCRIPT_DIR
RUNUSER=nobody

    case "$1" in

    start)
    su $RUNUSER -s /bin/bash -c "$PYTHON puypuy.py start"
    ;;

    stop)
    su $RUNUSER -s /bin/bash -c "$PYTHON puypuy.py stop"
    rm -f checks-enabled/*.pyc
    ;;

    restart)
    su $RUNUSER -s /bin/bash -c "$PYTHON puypuy.py stop"
    sleep 1
    su $RUNUSER -s /bin/bash -c "$PYTHON puypuy.py start"
    ;;
    *)
    echo "Usage: `basename $0` start | stop | restart"
    ;;

    esac
