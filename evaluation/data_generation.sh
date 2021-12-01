#!/usr/bin/env bash

echo "Make sure this script is located in the root folder of the 
BSBM project for data generation" 
read -p "Ready? y/n" -n 1 -r
echo    # (optional) move to a new line

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi



for (( i = 1000; i < 10200; i+= 1000 )); do

    ./generate -pc $i

    mv dataset.nt  "${i}pc_dataset.nt"
    
done






