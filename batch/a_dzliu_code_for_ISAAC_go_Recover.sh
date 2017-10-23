#!/bin/bash
# 

# check host
if [[ $(uname -a) != *"ISAAC"* ]] && [[ " $@ " != *" test "* ]]; then
    echo "This code can only be ran on ISAAC machine!"
    exit
fi

source ~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP
source ~/Cloud/Github/Crab.Toolkit.CAAP/SETUP.bash

if [[ $(type getpix 2>/dev/null | wc -l) -eq 0 ]]; then
    echo "Error! WCSTOOLS was not installed or loaded?"
    exit
fi

if [[ $(type pip 2>/dev/null | wc -l) -eq 0 ]]; then
    module load anaconda
fi

script_dir=$(bash -c "cd $(dirname ${BASH_SOURCE[0]}); pwd -P")

if [[ ! -f "$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py" ]]; then
    echo "Error! \"$script_dir/a_dzliu_code_for_Google_Drive_download_Data.py\" was not found!"
    exit
fi



# prepare physical parameter grid
Input_z=("1.000" "2.000" "3.000" "4.000" "5.000" "6.000")
Input_lgMstar=("09.00" "09.50" "10.00" "10.50" "11.00" "11.50" "12.00")
Input_Type_SED=("MS" "SB")
Input_Galaxy_Modelling_Dir='$HOME/Work/AlmaCosmos/Simulation/Cosmological_Galaxy_Modelling_for_COSMOS/'
if [[ " $@ " == *" test "* ]]; then
Input_z=("5.000")
Input_lgMstar=("11.00")
Input_Type_SED=("MS")
fi



FitsNames=( \
    "2015.1.00379.S_SB1_GB1_MB1_VUDS5170072382_sci.spw0_1_2_3" \
)



#echo "FitsNames = ${FitsNames[@]}"

if [[ ! -d "Input_images" ]]; then
    echo "Error! Input_images was not found! Please run \"a_dzliu_code_for_ISAAC_go_Simulate.sh\" first!"
fi

for FitsName in ${FitsNames[@]}; do
    
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
                    if [[ ! -d "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" ]]; then
                        # 
                        echo "caap-prior-extraction-photometry \\"
                        echo "    -out \"w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}\""
                        # 
                        if [[ ! -d "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" ]]; then
                            caap-prior-extraction-photometry \
                                -cat "../../Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/galaxy_model_id_ra_dec.txt" \
                                -sci "../../Simulated/$FitsName/w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/image_sim.fits" \
                                -out                           "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}"
                        else
                            caap-prior-extraction-photometry \
                                -out                           "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}"
                        fi
                    fi
                    
                    # Read results, output files are "Read_Results_of_XXX/{Output_getpix.txt,Output_galfit_Gaussian.txt}"
                    if [[ ! -d "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" ]] || \
                       [[ ! -f "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_getpix.txt" ]]; then
                        caap-prior-extraction-photometry-read-results \
                                                           "w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}"
                    fi
                    
                    # Concat results, output files are "Read_Results_of_XXX/{Output_getpix.txt,Output_galfit_Gaussian.txt}"
                    if [[ -f "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_getpix.txt" ]]; then
                        if [[ $(uname) == Darwin ]]; then
                            xargs_command="gxargs"
                        else
                            xargs_command="xargs"
                        fi
                        if [[ ! -f "datatable_Recovered_getpix.txt" ]]; then
                            head -n 1 "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_getpix.txt" \
                                | $xargs_command -d '\n' -I % echo "%        image_dir" \
                                > "datatable_Recovered_getpix.txt"
                        fi
                        echo "Reading \"Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_getpix.txt\""
                        tail -n +3 "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_getpix.txt" \
                            | $xargs_command -d '\n' -I % echo "%        w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" \
                            >> "datatable_Recovered_getpix.txt"
                    else
                        echo "Warning! \"Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_getpix.txt\" was not found! ******"
                    fi
                    if [[ -f "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_galfit_Gaussian.txt" ]]; then
                        if [[ ! -f "datatable_Recovered_galfit.txt" ]]; then
                            head -n 1 "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_galfit_Gaussian.txt" \
                                | $xargs_command -d '\n' -I % echo "%        image_dir" \
                                > "datatable_Recovered_galfit.txt"
                        fi
                        echo "Reading \"Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_galfit_Gaussian.txt\""
                        tail -n +3 "Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_galfit_Gaussian.txt" \
                            | $xargs_command -d '\n' -I % echo "%        w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}" \
                            >> "datatable_Recovered_galfit.txt"
                    else
                        echo "Warning! \"Read_Results_of_w_${i_w}_z_${i_z}_lgMstar_${i_lgMstar}_${i_Type_SED}/Output_galfit_Gaussian.txt\" was not found! ******"
                    fi
                done
            done
        done
    done
    
    cd "../../"
    #break
done

