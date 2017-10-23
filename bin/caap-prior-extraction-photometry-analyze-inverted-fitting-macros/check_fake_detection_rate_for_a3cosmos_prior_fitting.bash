#!/bin/bash
#

source ~/Cloud/Github/DeepFields.SuperDeblending/Softwares/SETUP


if [[ $(type topcat 2>/dev/null | wc -l) -eq 0 ]]; then
    echo "Error! topcat was not installed or not in the \$PATH!"
    exit
fi

topcat -stilts tmatchn \
               nin=2 \
               in1='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_fluxes_fit_2.txt' \
               ifmt1=ascii \
               values1="index" \
               in2='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_mask_buffer_fit_2.txt' \
               ifmt2=ascii \
               values2="index" \
               matcher=exact \
               ofmt=fits \
               out='tmp_1.fits'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tmatchn-usage.html

topcat -stilts tmatchn \
               nin=2 \
               in1='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_fluxes_fit_n2.txt' \
               ifmt1=ascii \
               values1="index" \
               in2='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_mask_buffer_fit_n2.txt' \
               ifmt2=ascii \
               values2="index" \
               matcher=exact \
               ofmt=fits \
               out='tmp_n1.fits'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tmatchn-usage.html

topcat -stilts tmatchn \
               nin=2 \
               in1='tmp_1.fits' \
               ifmt1=fits \
               values1="index" \
               in2='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_morphologies_fit_2.txt' \
               ifmt2=ascii \
               values2="index" \
               matcher=exact \
               ofmt=fits \
               out='tmp_2.fits'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tmatchn-usage.html

topcat -stilts tmatchn \
               nin=2 \
               in1='tmp_n1.fits' \
               ifmt1=fits \
               values1="index" \
               in2='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_morphologies_fit_n2.txt' \
               ifmt2=ascii \
               values2="index" \
               matcher=exact \
               ofmt=fits \
               out='tmp_n2.fits'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tmatchn-usage.html

topcat -stilts tmatchn \
               nin=2 \
               in1='tmp_2.fits' \
               ifmt1=fits \
               values1="index" \
               suffix1="" \
               in2='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_x_y_f_df_pix_scale_fit_2.txt' \
               ifmt2=ascii \
               values2="index" \
               suffix2="_x" \
               fixcols=all \
               matcher=exact \
               ofmt=fits \
               out='tmp_3.fits'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tmatchn-usage.html

topcat -stilts tmatchn \
               nin=2 \
               in1='tmp_n2.fits' \
               ifmt1=fits \
               values1="index" \
               suffix1="" \
               in2='../Read_Results_of_Prior_Extraction_with_Master_Catalog_v20170730/Read_Results_all_final_x_y_f_df_pix_scale_fit_n2.txt' \
               ifmt2=ascii \
               values2="index" \
               suffix2="_x" \
               fixcols=all \
               matcher=exact \
               ofmt=fits \
               out='tmp_n3.fits'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tmatchn-usage.html

topcat -stilts tpipe \
               in='tmp_3.fits' \
               ifmt=fits \
               omode=meta
               # meta



topcat -stilts tpipe \
               in='tmp_3.fits'\
               ifmt=fits \
               cmd='addcol "RA" "ra_fit_2_1"' \
               cmd='addcol "DEC" "dec_fit_2_1"' \
               cmd='addcol "Maj" "Maj_fit_2"' \
               cmd='addcol "Min" "Min_fit_2"' \
               cmd='addcol "snr_peak" "fpeak_fit_2/rms_fit_2"' \
               cmd='select "(mask_buffer==0 && pix_scale_x>0.05)"' \
               cmd='keepcols "RA DEC Maj Min pb_corr snr_peak image_file"' \
               ofmt=ascii \
               out='Input_photometry_on_original_image.txt'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tpipe.html

topcat -stilts tpipe \
               in='tmp_n3.fits'\
               ifmt=fits \
               cmd='addcol "RA" "ra_fit_n2_1"' \
               cmd='addcol "DEC" "dec_fit_n2_1"' \
               cmd='addcol "Maj" "Maj_fit_n2"' \
               cmd='addcol "Min" "Min_fit_n2"' \
               cmd='addcol "snr_peak" "fpeak_fit_n2/rms_fit_n2"' \
               cmd='select "(mask_buffer==0 && pix_scale_x>0.05 && snr_peak<20)"' \
               cmd='keepcols "RA DEC Maj Min pb_corr snr_peak image_file"' \
               ofmt=ascii \
               out='Input_photometry_on_inverted_image.txt'
               # http://www.star.bristol.ac.uk/~mbt/stilts/sun256/tpipe.html



if [[ -f "Plot_Fake_Detection_Rate.pdf" ]]; then
    cp "Plot_Fake_Detection_Rate.pdf" "Plot_Fake_Detection_Rate.pdf.backup"
fi

echo "macro read check_fake_detection_rate.sm check_fake_detection_rate" | sm

echo "Output to \"Plot_Fake_Detection_Rate.pdf\"!"

open "Plot_Fake_Detection_Rate.pdf"


