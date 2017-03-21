#!/bin/bash
#
# CURRENT DIR
export CRABTOOLKITCAAP=$(dirname $(perl -MCwd -e 'print Cwd::abs_path shift' "${BASH_SOURCE[0]}"))
if [[ x"$CRABTOOLKITCAAP" = x"" ]]; then
    echo "Failed to source ${BASH_SOURCE[0]}!"; exit 1
fi
#
# PATH
if [[ $PATH != *"$CRABTOOLKITCAAP/bin"* ]]; then
    export PATH="$CRABTOOLKITCAAP/bin":$PATH
fi
#
# LIST
CRABTOOLKITCMD=("alma-sky-coverage" "fits-image-to-coverage-polyogn" "caap-analyze-fits-image-pixel-histogram" "caap-generate-PSF-Gaussian-2D" "caap-highz-galaxy-crossmatcher" "caap-highz-galaxy-crossmatcher-read-results")
# 
# CHECK
# -- 20160427 only for interactive shell
# -- http://stackoverflow.com/questions/12440287/scp-doesnt-work-when-echo-in-bashrc
if [[ $- =~ "i" ]]; then 
  for TEMPTOOLKITCMD in ${CRABTOOLKITCMD[@]}; do
    type $TEMPTOOLKITCMD
  done
fi


