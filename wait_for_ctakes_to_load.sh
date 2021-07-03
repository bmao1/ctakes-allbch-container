#!/bin/bash

while true; do
    ready=`docker logs $1 2>&1 | grep -c "org.apache.catalina.startup.Catalina.start Server startup"`
    if [ "$ready" -eq "1" ]; then
        break
    fi
    sleep 2
done

