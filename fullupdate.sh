#!/bin/bash 
# download latest rmc dataset
# and install
# this assumes that you have the keys and coordinates for the data stored in an
echo -n "rmc "

loader="rmcloader"

source update.sh
source ./${loader}/credentials.py

update ${download} ${dataset} 

if [ "${success}" = "no" ]; then
	echo "loading ended"
	exit 1
fi

eval "$(conda shell.bash hook)"
cd ${release}
conda activate standard
echo "starting load `pwd`"
date
time python -u ../${loader}/readrmcfiles.py

cd ..

del() {
  shift
  for d in $*; do
	if [ ! "${d}" == "${release}" ]; then
          echo 'removing dataset' $d
          rm -r "${d}"
	fi
  done

}

dirs=`ls -dc 2[0-9]*`
del ${dirs}

