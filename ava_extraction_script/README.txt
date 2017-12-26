# AVA extraction script 
#---------------------

# Prerequisites:
#  - SVG preview
  sudo pip install svgwrite

# Usage:
# 1) Change asset location variables in "extract_clips_frames_dset.py"
# 2) Run the script


# The script extracts:
#  - middle frames (spatially annotated frames in AVA)
#  - video clips. Default: clips last 3 seconds + 1 second (padding).
#    The padding is added at video start and can be disabled.
#  - visu_jpg / visu_svg : middle frames with annotation boxes

