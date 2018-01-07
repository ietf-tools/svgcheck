#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]
then
    #  install some custom requirements on OSX
    #  e.g. brew install pyenv-virtualenv

    case "${TOXENV}" in
	py27)
	    # default version w/ the OS
	;;

	py36)
	    brew install python3
	    ;;

    esac
else
    # Custom stuff for Linux
fi

    
