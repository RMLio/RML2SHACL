#!/usr/bin/env bash

echo "Make sure this script is located in the root folder of the 
BSBM project" 

for (( i = 1000; i < 10200; i+= 1000 )); do

    ./generate -pc $i

    mv dataset.nt  "${i}pc_dataset.nt"
    
done






