#!/bin/sh
#
#

TOOLDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
BASEDIR=${TOOLDIR}/..

BASE=_build/references/external
BUILD=$BASEDIR/_build
PARSERS=$BASE/module/parsers
MODULES=$BASE/module/modules
PLUGINS=$BASE/plugins
TMP=$BUILD/tmp
CORE_COUNTER=8

export ANSIBLE_CONFIG=${BASEDIR}/ansible.cfg

help(){
cat << EOF

 Usage: $0 [OPTION] [COMMAND]

 Create definition files of Ansible modules to use with IntelliJ plugin OrchidE.

 Options:
   -h                               display this help text
   -c                               disable download of collections
   -m                               disable creation of module definitions
   -p                               disable creation of plugin definitions
   -a                               version snippet of requirements file name
   -o <n>                           spwan n background processes
                                       default: 8
EOF
}



if [ $# == 0 ]; then
    help
    exit 1
fi

params=( $* )

DOWNLOAD_COLLECTIONS="true"
CREATE_MODULES="true"
CREATE_PLUGINS="true"

for (( i=0; i<$# ; i++ )) ; do
    case ${params[i]} in
        -h )
            help
            exit 1
            ;;
        -c )
            DOWNLOAD_COLLECTIONS="false"
            ;;
        -m )
            CREATE_MODULES="false"
            ;;
        -p )
            CREATE_PLUGINS="false"
            ;;
        -f )
            BUILDFILE="${params[i+1]}"
            unset "params[i+1]"
            ;;
        -a )
            ANSIBLE_VERSION=${params[i+1]}
            unset "params[i+1]"
            ;;
        -o )
            CORE_COUNTER=${params[i+1]}
            unset "params[i+1]"
            ;;
        * )
            PARAMS="$PARAMS ${params[i]}"
            ;;
    esac
done


mkdir -p $MODULES
mkdir -p $PARSERS
mkdir -p $PLUGINS
mkdir -p $TMP
mkdir -p $BUILD/META-INF



export ANSIBLE_CFG=./ansible.cfg

PLUGINS_DEFINTION=$TMP/plugins-dump.json
INPUT_COLLECTIONS=res/requirements-ans${ANSIBLE_VERSION}.txt


downloadCollections(){
  if [ ${DOWNLOAD_COLLECTIONS} == "true" ]; then
    while IFS= read -r collectionDescriptor; do
      # Ignore lines that start with #
      if echo "${collectionDescriptor}" | grep -qE '^\s*#'; then
        continue
      fi

      # Process the line (for example, print it or use it in a command)
      collection=${collectionDescriptor%%:*}
      if( [ $collection != "ansible.builtin" ] ); then
        echo "Installing collection $collectionDescriptor" | tee -a orchide-builder.log
        ansible-galaxy collection install -f $collectionDescriptor &
        if [ $DL_COUNTER -lt 4 ]; then
          ((DL_COUNTER++))
        else
          wait
          DL_COUNTER=0
        fi
      fi
    done < "$INPUT_COLLECTIONS"
  fi
}

createDefinition(){
    local col=$1
    echo "Creating modules for collection $col" | tee -a orchide-builder.log
    sleep 0.2
    ansible-doc -t module $col --metadata-dump | jq .all.module | \
      jq 'to_entries | map({(.key): (if .value.doc.deprecated != null then {deprecated: (.value.doc.deprecated + {state: true})} else {} +{ deprecated: {state: false }} end +{"short_description": (.value.doc.short_description)} ) }) | add' \
      >  $PARSERS/${col}/_list_of_all_modules.json


    ansible-doc -t module $col --metadata-dump | jq .all.module | jq -r 'to_entries' | jq -c '.[]' | while read -r col_module; do
      fqcn=$(echo "$col_module" | jq -r '.key')
      name=${fqcn##*.}
      echo "$col_module" | jq '{(.key): .value} | walk(if type == "object" then del(.filename) else . end)' >  ${MODULES}/${col}/${name}.json
    done

}

createAnsibleBuiltinModules(){
  if [ "${CREATE_MODULES}" == "true" ]; then
    ANSIBLE_BUILTIN=$(ansible --version | grep -o -e '/.*site-packages.*')
    ANSIBLE_BVERSION=$(ansible --version | grep -o -e 'core [0-9\.]*')
    ANSIBLE_BVERSION=${ANSIBLE_BVERSION##* }
    mkdir -p _build/collections/ansible_collections/ansible/builtin
    cp -r $ANSIBLE_BUILTIN/* _build/collections/ansible_collections/ansible/builtin
    collection="ansible.builtin"
    mkdir -p $MODULES/$collection
    mkdir -p $PARSERS/$collection

    echo "
    {
        \"collection_info\": {
          \"namespace\": \"ansible\",
          \"name\": \"builtin\",
          \"version\": \"${ANSIBLE_BVERSION}\",
          \"dependencies\": {}
        }
    }
    " > _build/collections/ansible_collections/ansible/builtin/MANIFEST.json

    createDefinition $collection
  fi
}


wait_for_slot() {
    while [ $(jobs -r | wc -l) -ge $CORE_COUNTER ]; do
        sleep 1
    done
}

createModuleDefinitions(){
  if [ ${CREATE_MODULES} == "true" ]; then
    echo '{}' > $BASE/collections.json
    echo "# OrchidE definition update ${ANSIBLE_VERSION}" > $BUILD/changelog-template.md
    echo "## Included collections" >> $BUILD/changelog-template.md

    DL_COUNTER=0
    while IFS= read -r collectionDescriptor; do
      # Ignore lines that start with #
      if echo "${collectionDescriptor}" | grep -qE '^\s*#'; then
        echo "Ignoring commented collection $collectionDescriptor"
        continue
      fi
      echo "Processing collection $collectionDescriptor" | tee -a orchide-builder.log
      collection=${collectionDescriptor%%:*}

      echo "Creating collection $collection" | tee -a orchide-builder.log
      mkdir -p $MODULES/$collection
      mkdir -p $PARSERS/$collection

      # Update collections.json
      collectionDefinition=$(ansible-galaxy collection list --format json ${collection} | jq -c 'to_entries | .[].value ')
      jq ". += ${collectionDefinition}" $BASE/collections.json > $BUILD/collections-tmp.json
      mv $BUILD/collections-tmp.json $BASE/collections.json

      updateVersionReferences $collection "$collectionDefinition"

      wait_for_slot
      sleep 0.2
      createDefinition $collection &

    done < "$INPUT_COLLECTIONS"
    # Sort collections
    jq 'to_entries | sort_by(.key)| from_entries' $BASE/collections.json > $BUILD/collections-tmp.json
    mv $BUILD/collections-tmp.json $BASE/collections.json
  fi
}
updateVersionReferences(){
   local col=$1
   local colDefinition=$2

   echo "$colDefinition"
   colNewVersion=$(echo "$colDefinition" | jq -r 'to_entries[0].value.version')
   echo "Creating version $colNewVersion" | tee -a orchide-builder.log
   echo "$col=$colNewVersion" >> $BUILD/version_references.properties

   colOldVersion=$(cat $BASEDIR/version_references.properties | grep $col | sed 's/.*=//g' )
   updated=""
   # ignore removed collections
   if [ "$colOldVersion" != "$colOldVersion" ] ; then
     if [ "$colOldVersion" != "$colNewVersion" ] ; then
        updated=" (updated from $colOldVersion)"
     fi
   fi
   echo "- $col ${colNewVersion}${updated}" >> $BUILD/changelog-template.md
}

dumpPluginDoc(){
  for TYPE in "${plugins[@]}" ; do
    echo Dump plugin ${TYPE} ... | tee -a orchide-builder.log
    cat ${PLUGINS_DEFINTION} | jq ".all.${TYPE}" > $TMP/plugin-${TYPE}-raw.json
    cat $TMP/plugin-${TYPE}-raw.json | jq 'walk(if type == "object" then del(.filename) else . end)' > $PLUGINS/${TYPE}.json
  done
}

createPlugins(){
  if [ ${CREATE_PLUGINS} == "true" ]; then
    echo Creating definitions for plugins ... | tee -a orchide-builder.log
    ansible-doc -j --metadata-dump  --no-fail-on-errors  > ${PLUGINS_DEFINTION}
    plugins=(
    "become"
    "connection"
    "filter"
    "keyword"
    "lookup"
    "strategy"
    "test"
    )
    dumpPluginDoc
  fi
}

addResources(){
  cp -r $BASEDIR/src/main/resources/static/references/ansible-defaults $BASE/
  cp -r $BASEDIR/src/main/resources/static/references/inspections $BASE/
  cp -r $BASEDIR/src/main/resources/static/schemas $BUILD/
  sed "s/CONTENT-VERSION/${ANSIBLE_VERSION}/g" $BASEDIR/src/main/resources/static/META-INF/orchide-builder-version.properties > $BUILD/META-INF/orchide-builder-version.properties
}

createJar(){
  echo "Creating jar ..." | tee -a orchide-builder.log
  jar --create --file $BUILD/orchide-definitions.jar -C $BUILD META-INF -C $BUILD references -C $BUILD schemas
}

echo "Starting ..." | tee orchide-builder.log

DL_COUNTER=0

downloadCollections
createAnsibleBuiltinModules


createModuleDefinitions
wait

createPlugins

addResources

createJar
