#!/bin/bash
#

source ~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP


if [[ $(type topcat 2>/dev/null | wc -l) -eq 0 ]]; then
    echo "Error! topcat was not installed or not in the \$PATH!"
    exit
fi

topcat -stilts tpipe \
               in='../../20170930/cat_pybdsm_concatenated_300917.fits'\
               ifmt=fits \
               cmd='addcol "Maj" "Maj_deconv"' \
               cmd='addcol "Min" "Min_deconv"' \
               cmd='addcol "pb_corr" "NULL_Pbcor? 9999 : Pbcor"' \
               cmd='addcol "snr_peak" "Peak_flux/E_Peak_flux"' \
               cmd='addcol "image_file" "image"' \
               cmd='keepcols "RA DEC Maj Min PA pb_corr snr_peak image_file"' \
               ofmt=ascii \
               out='Input_photometry_on_original_image.txt'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tpipe.html

topcat -stilts tpipe \
               in='../cat_pybdsm_concatenated_negative_061117.fits'\
               ifmt=fits \
               cmd='addcol "Maj" "Maj_deconv"' \
               cmd='addcol "Min" "Min_deconv"' \
               cmd='addcol "pb_corr" "NULL_Pbcor? 9999 : Pbcor"' \
               cmd='addcol "snr_peak" "Peak_flux/E_Peak_flux"' \
               cmd='addcol "image_file" "image"' \
               cmd='keepcols "RA DEC Maj Min PA pb_corr snr_peak image_file"' \
               ofmt=ascii \
               out='Input_photometry_on_inverted_image.txt'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tpipe.html



if [[ -f "Plot_Fake_Detection_Rate.pdf" ]]; then
    cp "Plot_Fake_Detection_Rate.pdf" "Plot_Fake_Detection_Rate.pdf.backup"
fi

echo "macro read check_fake_detection_rate.sm check_fake_detection_rate" | sm

echo "Output to \"Plot_Fake_Detection_Rate.pdf\"!"

open "Plot_Fake_Detection_Rate.pdf"


