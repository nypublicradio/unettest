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

	mySys="$(uname -s)"

	case "${mySys}" in
	Darwin)
		BUILDTARGET="mac"
		;;
	Linux)
		BUILDTARGET="nix"
		;;
	esac
	pyinstaller unettest.py -p ~/.venvs/unettest/lib/python3.7/site-packages --onefile --name unettest.$BUILDTARGET

	sha_val=$( shasum -a 256 dist/unettest.$BUILDTARGET )
	echo $sha_val > unettest.$BUILDTARGET-sha256

	aws s3 cp ./dist/unettest.$BUILDTARGET s3://unettest/ --acl public-read
	aws s3 cp ./unettest.$BUILDTARGET-sha256 s3://unettest/ --acl public-read
}

function build_and_deploy_docs {
	echo '#### DOCUMENTATION ####'

	sphinx-build -b html ./docs ./docs/build

	./rm_nav_header.sh

	aws s3 cp ./docs/build s3://unettest.net/ --recursive --acl public-read
	aws s3 cp ./docs/blog s3://unettest.net/ --recursive --acl public-read
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
