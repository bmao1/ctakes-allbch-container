#!/bin/bash

for container in $@
do
    while [[ $container == ctakes-allbch-container_ctakes* ]]; do
        ready=`docker logs $container 2>&1 | grep -c "org.apache.catalina.startup.Catalina.start Server startup"`
        if [ "$ready" -eq "1" ]; then
            break
        fi
        sleep 2
    done
done
