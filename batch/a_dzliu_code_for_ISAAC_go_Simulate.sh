#!/bin/bash
# 

# check host
if [[ $(uname -a) != *"Linux isaac"* ]] && [[ " $@ " != *" test "* ]]; then
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
Input_Galaxy_Modelling_Dir="$HOME/Work/AlmaCosmos/Simulation/Cosmological_Galaxy_Modelling_for_COSMOS"
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
    mkdir "Input_images"
fi

for FitsName in ${FitsNames[@]}; do
    
    # check previous output
    if [[ -f "Simulated/$FitsName/done" ]]; then
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
    
    #<TODO><DBEUG># 
    #break
    
done

