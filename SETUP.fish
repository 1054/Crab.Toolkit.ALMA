#!/usr/bin/fish
# 
# CURRENT DIR
set -gx CRABTOOLKITCAAP (dirname (perl -MCwd -e 'print Cwd::abs_path shift' (status --current-filename)))
if [ x"$CRABTOOLKITCAAP" = x"" ]
    echo "Failed to source "(status --current-filename)"!"; exit
end
#
# PATH
if not contains "$CRABTOOLKITCAAP/bin" $PATH
    set -gx PATH "$CRABTOOLKITCAAP/bin" $PATH
end
#
# LIST
set -x CRABTOOLKITCMD "alma-sky-coverage" "fits-image-to-coverage-polyogn" "caap-analyze-fits-image-pixel-histogram" "caap-generate-PSF-Gaussian-2D" "caap-highz-galaxy-crossmatcher" "caap-highz-galaxy-crossmatcher-read-results"
# 
# CHECK
# -- 20160427 only for interactive shell
# -- http://stackoverflow.com/questions/12440287/scp-doesnt-work-when-echo-in-bashrc
if status --is-interactive
  for TEMPTOOLKITCMD in {$CRABTOOLKITCMD}
    type $TEMPTOOLKITCMD
  end
end


