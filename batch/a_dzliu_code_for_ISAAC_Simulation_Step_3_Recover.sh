#!/bin/bash
#SBATCH --mail-user=dzliu@mpia-hd.mpg.de
#SBATCH --mail-type=FAIL # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --time=48:00:00
#SBATCH --mem=4000
#SBATCH --cpus-per-task=30
#SBATCH --output=log_job_array_Source_Recovery_TASK_ID_%a_JOB_ID_%A.out

# 
# to run this script in Slurm job array mode
# sbatch --array=1-120%5 -N1 ~/Cloud/Github/Crab.Toolkit.CAAP/batch/a_dzliu_code_for_ISAAC_Simulation_Step_3_Recover.sh
# 

echo "Hostname: "$(/bin/hostname)
echo "PWD: "$(/bin/pwd -P)
echo "SLURM_JOBID: "$SLURM_JOBID
echo "SLURM_JOB_NODELIST: "$SLURM_JOB_NODELIST
echo "SLURM_NNODES: "$SLURM_NNODES
echo "SLURM_ARRAY_TASK_ID: "$SLURM_ARRAY_TASK_ID
echo "SLURM_ARRAY_JOB_ID: "$SLURM_ARRAY_JOB_ID
echo "SLURMTMPDIR: "$SLURMTMPDIR
echo "SLURM_SUBMIT_DIR: "$SLURM_SUBMIT_DIR



# check host and other dependencies
if [[ $(uname -a) != "Linux isaac"* ]] && [[ " $@ " != *" test "* ]]; then
    echo "This code can only be ran on ISAAC machine!"
    exit 1
fi

if [[ ! -f ~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP ]]; then
    echo "Error! \"~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP\" was not found! Please clone to there from \"https://github.com/1054/DeepFields.SuperDeblending\"!"
    exit 1
fi

if [[ ! -f ~/Cloud/Github/Crab.Toolkit.CAAP/SETUP.bash ]]; then
    echo "Error! \"~/Cloud/Github/Crab.Toolkit.CAAP/SETUP.bash\" was not found! Please clone to there from \"https://github.com/1054/Crab.Toolkit.CAAP\"!"
    exit 1
fi

if [[ ! -d ~/Work/AlmaCosmos/Photometry/ALMA_full_archive/Simulation_by_Daizhong/ ]]; then
    echo "Error! \"~/Work/AlmaCosmos/Photometry/ALMA_full_archive/Simulation_by_Daizhong/\" was not found! Please create that directory then run this code again!"
    exit 1
fi

cd ~/Work/AlmaCosmos/Photometry/ALMA_full_archive/Simulation_by_Daizhong/
source ~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP
source ~/Cloud/Github/Crab.Toolkit.CAAP/SETUP.bash
script_dir=~/Cloud/Github/Crab.Toolkit.CAAP/batch

if [[ $(type getpix 2>/dev/null | wc -l) -eq 0 ]]; then
    echo "Error! WCSTOOLS was not installed or loaded?"
    exit 1
fi

if [[ $(type pip 2>/dev/null | wc -l) -eq 0 ]]; then
    module load anaconda
fi

if [[ ! -f "list_projects.txt" ]]; then
    echo "Error! \"list_projects.txt\" was not found under current directory!"
    exit 1
fi

if [[ ! -f "$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py" ]]; then
    echo "Error! \"$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py\" was not found!"
    exit 1
fi



# prepare physical parameter grid
#Input_Galaxy_Modelling_Dir="$HOME/Work/AlmaCosmos/Simulation/Cosmological_Galaxy_Modelling_for_COSMOS"
Input_z=("1.000" "2.000" "3.000" "4.000" "5.000" "6.000")
Input_lgMstar=("09.00" "09.50" "10.00" "10.50" "11.00" "11.50" "12.00")
Input_Type_SED=("MS" "SB")
IFS=$'\n' read -d '' -r -a FitsNames < "list_projects.txt"
if [[ " $@ " == *" test "* ]]; then
Input_z=("5.000")
Input_lgMstar=("11.00")
Input_Type_SED=("MS")
FitsNames=( \
    "2015.1.00379.S_SB1_GB1_MB1_VUDS5170072382_sci.spw0_1_2_3" \
)
fi






#echo "FitsNames = ${FitsNames[@]}"

if [[ ! -d "Input_images" ]]; then
    echo "Error! Input_images was not found! Please run \"a_dzliu_code_for_ISAAC_go_Simulate.sh\" first!"
fi

for (( i=0; i<${#FitsNames[@]}; i++ )); do
    
    FitsName="${FitsNames[i]}"
    
    # check parallel
    if [[ $SLURM_ARRAY_TASK_ID -ne $((i+1)) ]]; then
        continue
    fi
    
    # check non-COSMOS fields
    if [[ "$FitsName" == *"2011.0.00539.S_SB1_GB1_MB1_ECDFS02_field3_sci.spw0_1_2_3"* ]] || \
        [[ "$FitsName" == *"2011.0.00539.S_SB1_GB1_MB2_ELS01_field2_sci.spw0_1_2_3"* ]] ; then
        echo "Warning! \"$FitsName\" is a non-COSMOS field! Skip and continue!"
        continue
    fi
    
    # check input image
    if [[ ! -f "Input_images/$FitsName.cont.I.image.fits" ]]; then
        echo "\"Input_images/$FitsName.cont.I.image.fits\" was not found!"
        exit 1
    fi
    
    # get wavelength from fits header
    obsfreq=$(gethead "Input_images/$FitsName.cont.I.image.fits" CRVAL3)
    obswave=$(awk "BEGIN {print 2.99792458e5/($obsfreq/1e9);}")
    if [[ "$obswave"x == ""x ]]; then
        echo "Error! Failed to get observation frequency/wavelength from the fits header keyword CRVAL3 of input fits file \"Input_images/$FitsName.cont.I.image.fits\"!"
        exit 1
    fi
    
    # check simulated directory
    if [[ ! -d "Simulated/$FitsName" ]]; then
        echo "\"Simulated/$FitsName\" was not found!"
        exit 1
    fi
    
    # make recovered directory
    if [[ ! -d "Recovered/$FitsName" ]]; then
        mkdir -p "Recovered/$FitsName"
    fi
    
    # cd recovered directory
    cd "Recovered/$FitsName/"
    
    # backup final data table
    if [[ -f "datatable_Recovered_getpix.txt" ]]; then
        if [[ -f "datatable_Recovered_getpix.txt.backup" ]]; then
            mv "datatable_Recovered_getpix.txt.backup" "datatable_Recovered_getpix.txt.backup.backup"
        fi
        mv "datatable_Recovered_getpix.txt" "datatable_Recovered_getpix.txt.backup"
    fi
    if [[ -f "datatable_Recovered_galfit.txt" ]]; then
        if [[ -f "datatable_Recovered_galfit.txt.backup" ]]; then
            mv "datatable_Recovered_galfit.txt.backup" "datatable_Recovered_galfit.txt.backup.backup"
        fi
        mv "datatable_Recovered_galfit.txt" "datatable_Recovered_galfit.txt.backup"
    fi
    
    # loop
    for i_w in "${obswave}"; do
        for i_z in "${Input_z[@]}"; do
            for i_lgMstar in "${Input_lgMstar[@]}"; do
                for i_Type_SED in "${Input_Type_SED[@]}"; do
                    
                    # Check output directory, delete failed runs
                    if [[ -d "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" ]]; then
                        if [[ ! -f "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/List_of_Input_Sci_Images.txt" ]]; then
                            echo ""
                            echo "rm -r \"w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}\""
                            echo ""
                            rm -r "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}"
                            echo ""
                            echo "rm -r \"Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}\" 2>/dev/null"
                            echo ""
                            rm -r "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" 2>/dev/null
                        fi
                    fi
                    
                    # Run caap-prior-extraction-photometry
                    if [[ ! -d "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" ]]; then
                        # 
                        echo "caap-prior-extraction-photometry \\"
                        echo "    -out \"w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}\" \\"
                        echo "    >> \"log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log\""
                        # 
                        echo ""                                              >> "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log"
                        echo ""                                              >> "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log"
                        echo ""                                              >> "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log"
                        echo "Current Time: "$(date +"%Y-%m-%d %H:%M:%S %Z") >> "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log"
                        echo ""                                              >> "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log"
                        echo ""                                              >> "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log"
                        echo ""                                              >> "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log"
                        # 
                        if [[ ! -d "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" ]]; then
                            caap-prior-extraction-photometry \
                                -cat "../../Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/galaxy_model_id_ra_dec.txt" \
                                -sci "../../Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/image_sim.fits" \
                                -out                           "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" \
                                >>                         "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log" \
                                &
                        else
                            caap-prior-extraction-photometry \
                                -out                           "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" \
                                >>                         "log_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}.log" \
                                &
                        fi
                        sleep 5
                    fi
                done
            done
            
            wait
            
        done
    done
    
    cd "../../"
    #break
done





