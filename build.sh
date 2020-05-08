#! /bin/bash

################################################################################
#
#   UNETTEST BUILD SCRIP
#
#   builds:
#	- UNETTEST
#	- docs
#
#   uploads:
#	- unettest
#	- docs
#
################################################################################

function build_and_deploy_binary {
	echo '#### FRESH BUILD ####'

	pyinstaller unettest.py -p ~/.virtualenvs/unettest/lib/python3.7/site-packages --onefile --name unettest.mac

	sha_val=$( shasum -a 256 dist/unettest.mac | cut -d ' ' -f 1 )
	echo $sha_val > mac-sha256

	aws s3 cp ./dist/unettest.mac s3://unettest/ --acl public-read
	aws s3 cp ./mac-sha256 s3://unettest/ --acl public-read
}

function build_and_deploy_docs {
	echo '#### DOCUMENTATION ####'

	sphinx-build -b html ./docs ./docs/build

	aws s3 cp ./docs s3://nypr-docs/nxr/ --recursive --acl public-read
}

case $1 in 
	"docs")
		echo "going to do docs!"
		build_and_deploy_docs
	;;
	
	"binary")
		echo "going to do binary!"
		build_and_deploy_binary
	;;

	*)
		echo "going to do docs and binary!"
		build_and_deploy_binary
		build_and_deploy_docs
	;;
esac