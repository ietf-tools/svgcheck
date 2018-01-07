#!/bin/bash

echo $TRAVIS_OS_NAME
echo $TOXENV

if [[ $TRAVIS_OS_NAME == 'osx' ]]
then
    #  install some custom requirements on OSX
    #  e.g. brew install pyenv-virtualenv

    case "${TOXENV}" in
	py27)
	# default version w/ the OS
            brew upgrade python
	;;

	py36)
	    brew install python3
	    ;;

    esac
fi

    
