#!/bin/bash
case "$1" in
  start)
    podman start myapp
    ;;
  stop)
    podman stop myapp
    ;;
  restart)
    podman restart myapp
    ;;
  logs)
    podman logs -f myapp
    ;;
  status)
    podman ps -a | grep myapp
    ;;
  *)
    echo "用法: $0 {start|stop|restart|logs|status}"
    exit 1
esac
