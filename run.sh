#!/bin/bash


WORKDIR=$(pwd)

mkdir -p ${WORKDIR}/db ${WORKDIR}/log ${WORKDIR}/tmp 


docker build . 


docker run \
	--name ${ICQBOT_NAME} \
	--mount type=bind,source=${WORKDIR}/log/,target=/work/log/ \
	--mount type=bind,source=${WORKDIR}/db/,target=/work/db/ \
	--mount type=bind,source=${WORKDIR}/tmp/,target=/work/tmp/ \
	--rm \
	-ti ${ICQBOT_NAME}:${ICQBOT_VERSION} 
