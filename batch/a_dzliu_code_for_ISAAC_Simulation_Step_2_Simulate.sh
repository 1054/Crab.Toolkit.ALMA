#!/bin/bash
#SBATCH --mail-user=dzliu@mpia-hd.mpg.de
#SBATCH --mail-type=FAIL # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --time=24:00:00
#SBATCH --mem=4000
#SBATCH --cpus-per-task=1
#SBATCH --output=log_job_array_TASK_ID_%a_JOB_ID_%A.out

# 
# to run this script in Slurm job array mode
# sbatch --array=1-1%1 -N1 ~/Cloud/Github/Crab.Toolkit.CAAP/batch/a_dzliu_code_for_ISAAC_Simulation_Step_2_Simulate.sh
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
Input_Galaxy_Modelling_Dir="$HOME/Work/AlmaCosmos/Simulation/Cosmological_Galaxy_Modelling_for_COSMOS"
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
    mkdir "Input_images"
fi

for (( i=0; i<${#FitsNames[@]}; i++ )); do
    
    FitsName="${FitsNames[i]}"
    
    # check parallel
    if [[ $SLURM_ARRAY_TASK_ID -ne $((i+1)) ]]; then
        continue
    fi
    
    # check previous output
    if [[ -f "Simulated/$FitsName/done" ]]; then
        echo "Found \"Simulated/$FitsName/done\"! Skip and continue!"
        continue
    fi
    
    # check non-COSMOS fields
    if [[ "$FitsName" == *"2011.0.00539.S_SB1_GB1_MB1_ECDFS02_field3_sci.spw0_1_2_3"* ]] || \
        [[ "$FitsName" == *"2011.0.00539.S_SB1_GB1_MB2_ELS01_field2_sci.spw0_1_2_3"* ]] || \; then
        echo "Warning! \"$FitsName\" is a non-COSMOS field! Skip and continue!"
        continue
    fi
    
    # check input image
    for file_to_download in \
        "Photometry/ALMA_full_archive/Blind_Extraction_by_Benjamin/20170930/Output_Residual_Images/$FitsName.cont.I.residual.fits" \
        "Data/ALMA_full_archive/Calibrated_Images_by_Benjamin/v20170604/fits_cont_I_image/$FitsName.cont.I.image.fits" \
        "Data/ALMA_full_archive/Calibrated_Images_by_Benjamin/v20170604/fits_cont_I_image_pixel_histograms/$FitsName.cont.I.image.fits.pixel.statistics.txt" \
        "Data/ALMA_full_archive/Calibrated_Images_by_Benjamin/v20170604/fits_cont_I_clean-beam/$FitsName.cont.I.clean-beam.fits"
        do
        if [[ ! -f "Input_images/$(basename $file_to_download)" ]]; then
            cd "Input_images/"
            "$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py" "$file_to_download"
            cd "../"
        fi
        if [[ ! -f "Input_images/$(basename $file_to_download)" ]]; then
            echo "Error! Failed to get the image file \"$file_to_download\" from Google Drive! Please re-try!"
            exit
        fi
    done
    
    # check BUNIT in fits header
    fits_header_BUNIT=$(gethead "Input_images/$FitsName.cont.I.residual.fits" BUNIT)
    if [[ "$fits_header_BUNIT"x == ""x ]]; then
        echo "Warning! No BUNIT in the fits header of the input fits file \"Input_images/$FitsName.cont.I.image.fits\"!"
        echo "Adding BUNIT=\"Jy/beam\""
        sethead "Input_images/$FitsName.cont.I.residual.fits" BUNIT="Jy/beam"
    fi
    
    # get wavelength from fits header
    obsfreq=$(gethead "Input_images/$FitsName.cont.I.image.fits" CRVAL3)
    obswave=$(awk "BEGIN {print 2.99792458e5/($obsfreq/1e9);}")
    if [[ "$obswave"x == ""x ]]; then
        echo "Error! Failed to get observation frequency/wavelength from the fits header keyword CRVAL3 of input fits file \"Input_images/$FitsName.cont.I.image.fits\"!"
        exit 1
    fi
    
    # backup simulated data table
    if [[ -f "Simulated/$FitsName/datatable_Simulated.txt" ]]; then
        if [[ -f "Simulated/$FitsName/datatable_Simulated.txt.backup" ]]; then
            mv "Simulated/$FitsName/datatable_Simulated.txt.backup" "Simulated/$FitsName/datatable_Simulated.txt.backup.backup"
        fi
        mv "Simulated/$FitsName/datatable_Simulated.txt" "Simulated/$FitsName/datatable_Simulated.txt.backup"
    fi
    
    # loop
    for i_w in "${obswave}"; do
        for i_z in "${Input_z[@]}"; do
            for i_lgMstar in "${Input_lgMstar[@]}"; do
                for i_Type_SED in "${Input_Type_SED[@]}"; do
                    
                    if [[ ! -f "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/image_sim.fits" ]]; then
                        
                        echo "caap-full-galaxy-modelling-map-maker \\"
                        echo "    -w \"$i_w\" -z \"${i_z}\" -lgMstar \"${i_lgMstar}\" -Type-SED \"${i_Type_SED}\""
                        
                        caap-full-galaxy-modelling-map-maker \
                            -sci "Input_images/$FitsName.cont.I.image.fits" \
                            -psf "Input_images/$FitsName.cont.I.clean-beam.fits" \
                            -res "Input_images/$FitsName.cont.I.residual.fits" \
                            -gal "$Input_Galaxy_Modelling_Dir" \
                            -w "$i_w" -z "${i_z}" -lgMstar "${i_lgMstar}" -Type-SED "${i_Type_SED}" \
                            -out "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}"
                        
                        if [[ ! -d "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" ]]; then
                            echo "Error! Failed to run \"caap-full-galaxy-modelling-map-maker\" and create \"Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}\" directory!"
                            exit 1
                        fi
                        
                        cd "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/"
                        cp */galaxy_model_*.txt ./
                        cp */image_sim.fits ./
                        cd "../../../"
                        
                        if [[ ! -f "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/image_sim.fits" ]]; then
                            echo "Error! Failed to run \"caap-full-galaxy-modelling-map-maker\" and create \"Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/image_sim.fits\" file!"
                            exit 1
                        fi
                        
                        # clean
                        rm -rf "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/$FitsName."*
                        
                    else
                        
                        echo "Found existing \"Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/image_sim.fits\", skip and continue!"
                        
                    fi
                    
                    # do bug fix - apply image_sci_mask to image_sim
                    #if [[ 1 == 1 ]]; then
                    #    cd "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/$FitsName.cont.I.image/"
                    #    echo CrabFitsImageArithmetic "image_res.fits" "adds" "image_mod.fits" "image_sim_nonan.fits" ">" "image_sim_nonan.log"
                    #         CrabFitsImageArithmetic "image_res.fits" "adds" "image_mod.fits" "image_sim_nonan.fits"  >  "image_sim_nonan.log"
                    #    echo CrabFitsImageArithmetic "image_sci.fits" "times" "0" "image_sci_maskzero.fits" ">" "image_sci_maskzero.log"
                    #         CrabFitsImageArithmetic "image_sci.fits" "times" "0" "image_sci_maskzero.fits"  >  "image_sci_maskzero.log"
                    #    echo CrabFitsImageArithmetic "image_sci_maskzero.fits" "adds" "1" "image_sci_mask.fits" ">" "image_sci_mask.log"
                    #         CrabFitsImageArithmetic "image_sci_maskzero.fits" "adds" "1" "image_sci_mask.fits"  >  "image_sci_mask.log"
                    #    echo CrabFitsImageArithmetic "image_sim_nonan.fits" "times" "image_sci_mask.fits" "image_sim.fits" ">" "image_sim.log"
                    #         CrabFitsImageArithmetic "image_sim_nonan.fits" "times" "image_sci_mask.fits" "image_sim.fits"  >  "image_sim.log"
                    #    #rm image_sci_maskzero.fits image_sim_nonan.fits
                    #    #rm ../*.log
                    #    cp image_sim.fits ../
                    #    cd "../../../../"
                    #fi
                    
                    
                    # Concat simulated datatable
                    if [[ -f "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/galaxy_model_id_ra_dec_flux.txt" ]]; then
                        
                        if [[ $(uname) == Darwin ]]; then
                            xargs_command="gxargs"
                        else
                            xargs_command="xargs"
                        fi
                        
                        if [[ ! -f "Simulated/$FitsName/datatable_Simulated.txt" ]]; then
                            head -n 1 "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/galaxy_model_id_ra_dec_flux.txt" | $xargs_command -d '\n' -I {} printf "%s  %15s   %s\n" {} "wavelength_um" "sim_dir_str" \
                                    > "Simulated/$FitsName/datatable_Simulated.txt"
                        fi
                        cat "Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/galaxy_model_id_ra_dec_flux.txt" | tail -n +3 | $xargs_command -d '\n' -I {} printf "%s  %15.6f   %s\n" {} "$i_w" "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" \
                                    >> "Simulated/$FitsName/datatable_Simulated.txt"
                        
                        echo "Reading \"Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/galaxy_model_id_ra_dec_flux.txt\""
                    else
                        echo "Warning! \"Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/galaxy_model_id_ra_dec_flux.txt\" was not found! ******"
                    fi
                    
                done
            done
        done
    done
    
    # Done
    date +"%Y-%m-%d %H:%M:%S %Z" > "Simulated/$FitsName/done"
    
    #<TODO><DBEUG># 
    #break
    
done

