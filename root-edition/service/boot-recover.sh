#!/bin/sh
set -eu
unset NODE_OPTIONS NODE_PATH
[ "$#" -le 1 ] || exit 2
case "${1-boot}" in
  boot) exec /usr/bin/node /var/lib/clean-your-tv-root/python_boot.js /var/lib/clean-your-tv-root /var/lib/clean-your-tv-root/runtime/cli.py boot ;;
  mark) exec /usr/bin/node /var/lib/clean-your-tv-root/python_boot.js /var/lib/clean-your-tv-root /var/lib/clean-your-tv-root/runtime/boot_gate.py mark ;;
  *) exit 2 ;;
esac
