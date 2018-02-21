#!/bin/bash

schemas=($(curl -sL http://redfish.dmtf.org/schemas/v1/ | grep -Po '(?<=href=")[^"]*(?=")' | grep ".*\.json$"))
echo "GET Schemas"
#echo "$schemas"
for i in "${schemas[@]}"
do
    uri="http://redfish.dmtf.org/schemas/v1/$i"
    curl $uri -o ./../schemas/$i
done
