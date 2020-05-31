#!/bin/bash


WORKDIR=$(pwd)

if [ -z "${ICQBOT_VERSION}" ]
then
	export ICQBOT_VERSION=$(git describe --tags --abbrev=0)
fi

mkdir -p ${WORKDIR}/db ${WORKDIR}/log ${WORKDIR}/tmp 


docker build .  \
	--build-arg ICQBOT_NAME=${ICQBOT_NAME} \
	--build-arg ICQBOT_TOKEN=${ICQBOT_TOKEN} \
	--build-arg ICQBOT_OWNER=${ICQBOT_OWNER} \
	--build-arg ICQBOT_VERSION=${ICQBOT_VERSION} \
	-t ${ICQBOT_NAME}:${ICQBOT_VERSION}


docker run \
	--name ${ICQBOT_NAME} \
	--mount type=bind,source=${WORKDIR}/log/,target=/work/log/ \
	--mount type=bind,source=${WORKDIR}/db/,target=/work/db/ \
	--mount type=bind,source=${WORKDIR}/tmp/,target=/work/tmp/ \
	--rm \
	-ti ${ICQBOT_NAME}:${ICQBOT_VERSION} 
