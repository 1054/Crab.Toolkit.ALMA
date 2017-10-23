#!/bin/bash
# 

# check host
if [[ $(uname -a) != "Linux isaac"* ]] && [[ " $@ " != *" test "* ]]; then
    echo "This code can only be ran on ISAAC machine!"
    exit
fi

source ~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP
source ~/Cloud/Github/Crab.Toolkit.CAAP/SETUP.bash

if [[ ! -d "Simulated" ]]; then
    echo "Error! \"Simulated\" was not found under current directory!"
    exit
fi

if [[ ! -d "Recovered" ]]; then
    echo "Error! \"Recovered\" was not found under current directory!"
    exit
fi

if [[ ! -f "list_projects.txt" ]]; then
    echo "Error! \"list_projects.txt\" was not found under current directory!"
    exit
fi



IFS=$'\n' read -d '' -r -a FitsNames < "list_projects.txt"
if [[ " $@ " == *" test "* ]]; then
FitsNames=( \
    "2015.1.00379.S_SB1_GB1_MB1_VUDS5170072382_sci.spw0_1_2_3" \
)
fi



echo "\${#FitsNames[@]} = ${#FitsNames[@]}"

for (( i=0; i<${#FitsNames[@]}; i++ )); do
    
    echo "${FitsNames[i]} ($((i+1))/${#FitsNames[@]})"
    
    if [[ ! -d "Recovered/${FitsNames[i]}/" ]]; then
        echo "Error! \"Recovered/${FitsNames[i]}/\" was not found under current directory!"
        exit
    fi
    
    cd "Recovered/${FitsNames[i]}/"
    
    caap-prior-extraction-simulation-analyze-statistics # -repetition-number 84 -overwrite
    
    cd "../../"
    
    #break
    
done







