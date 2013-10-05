#!/bin/sh
### BEGIN INIT INFO
# Provides:          darkice
# Required-Start:    icecast2
# Required-Stop:
# Default-Start:     3 5
# Default-Stop:      0 1 2 6
# Short-Description: Starts darkice
### END INIT INFO
#
# Runs darkice, plays whatever's in Line-in to the webstream
# init script written by Nick "P. Rex" Pegg
# Because a cronjob @reboot is just gay.

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
DAEMON=/usr/bin/darkice
NAME=darkice
DESC=darkice

test -x $DAEMON || exit 0

CONFIGFILE="/etc/darkice.cfg"
USERID=root
GROUPID=root

set -e

case "$1" in
  start)
	echo -n "Starting $DESC: "
	start-stop-daemon --start --background --quiet --chuid $USERID:$GROUPID \
                --exec $DAEMON -p /var/run/darkice.pid -m \
		-- -v 0 -c $CONFIGFILE &
	echo "$NAME";
	;;
  stop)
	echo -n "Stopping $DESC: "
        start-stop-daemon --stop --oknodo --quiet --exec $DAEMON
	echo > /var/run/darkice.pid
        echo "$NAME."
	;;
  reload|force-reload)
	echo "Reloading $DESC configuration files."
        start-stop-daemon --stop --signal 1 --quiet --exec $DAEMON
        ;;
  restart)
	echo -n "Restarting $DESC: "
	start-stop-daemon --stop --oknodo --quiet --exec $DAEMON
	sleep 1
	start-stop-daemon --start --background --quiet --chuid $USERID:$GROUPID \
                --exec $DAEMON --pidfile /var/run/darkice.pid -m \
		-- -v 0 -c $CONFIGFILE
	echo "$NAME"
	;;
  status)
	cat /var/run/darkice.pid
	;;
  *)
	echo "Usage: $0 {start|stop|restart|reload|force-reload}" >&2
        exit 1
        ;;
esac

exit 0
