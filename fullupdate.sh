#!/bin/bash 
# download latest rmc dataset
# and install
# this assumes that you have the keys and coordinates for the data stored in an
echo -n "rmc "
source update.sh
update rmc-ff-download rmc

eval "$(conda shell.bash hook)"
cd ${release}
conda activate standard
echo "starting load `pwd`"
date
time python -u ../RMCLoader/readrmcfiles.py
../../fix-perms
