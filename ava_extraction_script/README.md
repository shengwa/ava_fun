# AVA extraction script 

## Prerequisites
1. SVG preview, which can be installed using `sudo pip install svgwrite` .
2. OpenCV.

## Usage
1. Change asset location variables in "extract_clips_frames_dset.py"
2. Run the script


## Script description
The script extracts:
- middle frames (spatially annotated frames in AVA)
- video clips. Default: clips last 3 seconds + 1 second (padding). The padding is added at video start and can be disabled.
- visu_jpg / visu_svg : middle frames with annotation boxes

---

## Some updates (12/27/2017)
0. Script was downloaded from AVA Google group.
1. The script was modified to support both Python 2 and 3.
2. All the file paths could be given as command-line arguments now.
3. Since the processing is very slow, the script was changed to allow process part of the dataset.

## Current usage (since 12/27/2017)
```bash
python extract_clips_frames_dset.py --video_dir=/PATH/TO/AVA/VIDEOS --output_dir=output --annot_file=../ava_train_v1.0.csv --actionlist_file=../ava_action_list_v1.0.pbtxt --partial_process=True --partial_start=10000 --partial_num=50000
```
