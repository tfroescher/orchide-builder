#!/bin/sh
#
#
mkdir -p _build/plugins
mkdir -p _build/dist/references/external/plugins

INPUT=_build/dump.json
export ANSIBLE_CFG=./ansible.cfg

ansible-doc -j --metadata-dump  --no-fail-on-errors > ${INPUT}

plugins=(
"become"
"connection"
"filter"
"keyword"
"lookup"
"strategy"
"test"
)

dumpPluginDoc(){
  for TYPE in "${plugins[@]}" ; do
    echo Dump plugin ${TYPE} ...
    cat ${INPUT} | jq ".all.${TYPE}" > _build/plugins/${TYPE}-raw.json
    cat _build/plugins/${TYPE}-raw.json | jq 'walk(if type == "object" then del(.filename) else . end)' > _build/dist/references/external/plugins/${TYPE}.json
  done
}

dumpPluginDoc

