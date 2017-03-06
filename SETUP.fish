#!/usr/bin/fish
# 
# 
# CRABTOOLKITCAAP
if contains "Linux" (uname)
    set -x CRABTOOLKITCAAP (dirname (readlink -f (status --current-filename)))
end
if contains "Darwin" (uname)
    set -x CRABTOOLKITCAAP (dirname (perl -MCwd -e 'print Cwd::abs_path shift' (status --current-filename)))
end
export CRABTOOLKITCAAP
#<DEBUG># echo "$CRABTOOLKITCAAP"
# 
# Check
if [ x"$CRABTOOLKITCAAP" = x"" ]
    exit
end
#
# PATH
if not contains "$CRABTOOLKITCAAP/bin" $PATH
    set -x PATH "$CRABTOOLKITCAAP/bin" $PATH
end
#
# LIST
set -x CRABTOOLKITCMD "alma-sky-coverage" "fits-image-to-coverage-polyogn" "caap-analyze-fits-image-pixel-histogram" "caap-generate-PSF-Gaussian-2D"
# 
# CHECK
# -- 20160427 only for interactive shell
# -- http://stackoverflow.com/questions/12440287/scp-doesnt-work-when-echo-in-bashrc
if status --is-interactive
  for TEMPTOOLKITCMD in {$CRABTOOLKITCMD}
    type $TEMPTOOLKITCMD
  end
end


