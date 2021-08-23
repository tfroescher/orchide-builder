#!/bin/bash

help(){
cat << EOF

 Usage: $0 [OPTION] [COMMAND]

 Wrapper script to create definition files of Ansible modules to use with IntelliJ plugin OrchidE.

 Options:
   -h                               display this help text
   -i                               build built-in variant for OrchidE including custom collections
   -a                               Ansible version to build collections for
   -d                               Disable backward collections (currently community.kubernetes) (required for e.g Ansible 4.4.0, kubernetes collections < 2.0.0)

 Commands:
   build-all                        Builds the definition package (clean, download collections, create definitions, pack jar)
   build-4release                   Builds the definition package for a specific Ansible version (clean, download collections, create definitions, pack jar)


EOF
}


TOOLDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
ANTLIB="${TOOLDIR}/lib"
BUILDFILE=$TOOLDIR/build.xml
LIB="-lib $ANTLIB"

ARGS=""
JVM_ARGS=""
PARAMS=""
ANSIBLE_VERSION=""
WITHOUT_PATCHES=""

if [ $# == 0 ]; then
    help
    exit 1
fi

params=( $* )

for (( i=0; i<$# ; i++ )) ; do
    case ${params[i]} in
        -h )
            help
            exit 1
            ;;
        -i )
            JVM_ARGS="$JVM_ARGS -Dcustom_modules=false"
            ;;
        -p )
            ARGS="$ARGS -p"
            ;;
        -v )
            ARGS="$ARGS -v"
            ;;
        -q )
            ARGS="$ARGS -q"
            ;;
        -f )
            BUILDFILE="${params[i+1]}"
            unset params[i+1]
            ;;
        -a )
            ANSIBLE_VERSION=-Dtarget_ansible_version=${params[i+1]}
            unset params[i+1]
            ;;
        -d )
            WITHOUT_PATCHES="-Dcreate-static-patches.disabled=true"
            ;;
        * )
            if [[ "${params[i]}" =~ .*"-D".* ]] ; then
                JVM_ARGS="${JVM_ARGS} ${params[i]}"
            else
                PARAMS="$PARAMS ${params[i]}"
            fi
            ;;
    esac
done

if [ -n $ANSIBLE_VERSION ]; then

echo ant $LIB -Dbasedir=$TOOLDIR -Dtooldir=$TOOLDIR -f $BUILDFILE $ANSIBLE_VERSION $JVM_ARGS $WITHOUT_PATCHES $ARGS $PARAMS
ant $LIB -Dbasedir=$TOOLDIR -Dtooldir=$TOOLDIR -f $BUILDFILE  $ANSIBLE_VERSION $JVM_ARGS $WITHOUT_PATCHES -Denable.completePackage=true $ARGS $PARAMS

else

echo ant $LIB -Dbasedir=$TOOLDIR -Dtooldir=$TOOLDIR -f $BUILDFILE $JVM_ARGS $ARGS $PARAMS
ant $LIB -Dbasedir=$TOOLDIR -Dtooldir=$TOOLDIR -f $BUILDFILE $JVM_ARGS $ARGS $PARAMS

fi



