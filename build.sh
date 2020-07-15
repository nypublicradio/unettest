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
	echo $sha_val > unettest.mac-sha256

	aws s3 cp ./dist/unettest.mac s3://unettest/ --acl public-read
	aws s3 cp ./unettest.mac-sha256 s3://unettest/ --acl public-read
}

function build_and_deploy_docs {
	echo '#### DOCUMENTATION ####'

	sphinx-build -b html ./docs ./docs/build

	./rm_nav_header.sh

	aws s3 cp ./docs/build s3://unettest.net/ --recursive --acl public-read
}

if [ -z $1 ] ; then
	echo "going to do docs and binary!"
	build_and_deploy_binary
	build_and_deploy_docs
else

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
			echo "run ./build.sh with either \`docs\` or \`binary\`"
		;;
	esac
fi
