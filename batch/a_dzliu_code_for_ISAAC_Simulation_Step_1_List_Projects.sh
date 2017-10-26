#!/bin/bash
#SBATCH --mail-user=dzliu@mpia-hd.mpg.de
#SBATCH --mail-type=FAIL # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --time=24:00:00
#SBATCH --mem=4000
#SBATCH --cpus-per-task=1
#SBATCH --output=log_Step_1_TASK_ID_%a_JOB_ID_%A.out

# 
# to run this script in Slurm job array mode
# sbatch --array=1-1%1 -N1 ~/Cloud/Github/Crab.Toolkit.CAAP/batch/a_dzliu_code_for_ISAAC_Simulation_Step_1_List_Projects.sh
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

mkdir -p ~/Work/AlmaCosmos/Photometry/ALMA_full_archive/Simulation_by_Daizhong/
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

if [[ ! -f "$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py" ]]; then
    echo "Error! \"$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py\" was not found!"
    exit 1
fi



# 
# main code
# 

"$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py" "list_project_rms_for_v20170604.sort_V.image_file.txt"

cat "list_project_rms_for_v20170604.sort_V.image_file.txt" | grep -v '^#' | sed -e 's/^ *//g' | tr -s ' ' | cut -d ' ' -f 8 | grep -v '^2011.0.00064.S' > list_projects.txt

if [[ ! -f "list_projects.txt" ]]; then
    echo "Error! Failed to get \"list_project_rms_for_v20170604.sort_V.image_file.txt\" from Google Drive and create \"list_projects.txt\"!"
    exit 1
fi





