#!/bin/bash


source ./setenv.sh

if [ -z "${ICQBOT_VERSION}" ]
then
	export ICQBOT_VERSION=$(git describe --tags --abbrev=0)
fi


docker build .  \
	--build-arg ICQBOT_NAME=${ICQBOT_NAME} \
	--build-arg ICQBOT_TOKEN=${ICQBOT_TOKEN} \
	--build-arg ICQBOT_OWNER=${ICQBOT_OWNER} \
	--build-arg ICQBOT_VERSION=${ICQBOT_VERSION} \
	-t ${ICQBOT_NAME}:${ICQBOT_VERSION}


docker run \
	--name ${ICQBOT_NAME} \
	-v $(pwd)/log/:/workdir/log/ \
	-v $(pwd)/db/:/workdir/db/ \
	--rm \
	-ti ${ICQBOT_NAME}:${ICQBOT_VERSION} 
