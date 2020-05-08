#! /bin/bash

################################################################################
#
#   NGINXRAY BUILD SCRIP
#
#   builds:
#	- nginxray
#	- docs
#
#   uploads:
#	- nginxray
#	- docs
#
################################################################################

function build_and_deploy_binary {
	echo '#### FRESH BUILD ####'

	pyinstaller nginxray.py -p ~/.virtualenvs/nginxray/lib/python3.7/site-packages --onefile --name nginxray.mac

	sha_val=$( shasum -a 256 dist/nginxray.mac | cut -d ' ' -f 1 )
	echo $sha_val > mac-sha256

	aws s3 cp ./dist/nginxray.mac s3://nginxray/ --acl public-read
	aws s3 cp ./mac-sha256 s3://nginxray/ --acl public-read
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
