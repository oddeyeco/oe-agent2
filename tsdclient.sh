#!/usr/bin/env bash
### BEGIN INIT INFO
# Provides: tsdclient.sh
# Required-Start: $local_fs $network
# Should-Start: ypbind nscd ldap ntpd xntpd
# Required-Stop: $network
# Default-Start:  2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: start and stop TSD Client
# Description: TSD Client
### END INIT INFO#

SCRIPT_DIR="$(cd $(dirname $0) && pwd)"
PYTHON=`which python`
cd $SCRIPT_DIR

    case "$1" in

    start)
    $PYTHON start.py start
    ;;

    stop)
    $PYTHON start.py stop
    ;;

    restart)
    $PYTHON start.py restart
    ;;
    *)
    echo "Usage: `basename $0` start | stop | restart"
    ;;

    esac
