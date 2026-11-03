#!/bin/bash

if [ "$AUTOINSTALL" = "YES" ]; then
  find /home/bo/extra-addons -name 'requirements.txt' 2>/dev/null | while read -r file; do
    echo $file && pip3 install -r "$file"
  done
fi

exec "$@"

