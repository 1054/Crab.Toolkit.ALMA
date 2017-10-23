#!/bin/bash
# 

# check host
if [[ $(uname -a) != *"ISAAC"* ]] && [[ " $@ " != *" test "* ]]; then
    echo "This code can only be ran on ISAAC machine!"
    exit
fi

source ~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP
source ~/Cloud/Github/Crab.Toolkit.CAAP/SETUP.bash


image_names=( \
    "2015.1.00379.S_SB1_GB1_MB1_VUDS5170072382_sci.spw0_1_2_3" \
)

echo "\${#image_names[@]} = ${#image_names[@]}"

for (( i=0; i<${#image_names[@]}; i++ )); do
    
    echo "${image_names[i]} ($((i+1))/${#image_names[@]})"
    
    cd "Recovered/${image_names[i]}/"
    
    caap-prior-extraction-simulation-analyze-statistics # -repetition-number 84 -overwrite
    
    cd "../../"
    
    #break
    
done







