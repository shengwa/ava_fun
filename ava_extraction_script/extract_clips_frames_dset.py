from __future__ import print_function

import argparse
import os
import subprocess
import sys

import cv2
import svgwrite

parser = argparse.ArgumentParser()
parser.add_argument("--video_dir", default="../videos/", help="Videos path.")
parser.add_argument("--annot_file", default="../ava_train_v1.0.csv", help="Anotation file path.")
parser.add_argument("--actionlist_file", default="../ava_action_list_v1.0.pbtxt", help="Action list file path.")
parser.add_argument("--output_dir", default="out", help="Output path.")
parser.add_argument("--partial_process", type=bool, default=False, help="If setting to true then process only part of the annotations.")
parser.add_argument("--partial_start", type=int, default=0, help="Partial process starting index.")
parser.add_argument("--partial_num", type=int, default=0, help="Partial process number.")

FLAGS = parser.parse_args()

videodir = FLAGS.video_dir
annotfile = FLAGS.annot_file
actionlistfile = FLAGS.actionlist_file
outdir = FLAGS.output_dir

outdir_clips = os.path.join(outdir, "clips")
outdir_midframe = os.path.join(outdir, "midframes")

clip_length = 3 # seconds
clip_time_padding = 1.0 # seconds

# util
def hou_min_sec(millis):
    millis = int(millis)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60))
    return ("%d:%d:%d" % (hours, minutes, seconds))

def _supermakedirs(path, mode):
    if not path or os.path.exists(path):
        return []
    (head, tail) = os.path.split(path)
    res = _supermakedirs(head, mode)
    os.mkdir(path)
    os.chmod(path, mode)
    res += [path]
    return res

def mkdir_p(path):
    try:
        _supermakedirs(path, 0o775) # Supporting Python 2 & 3
    except OSError as exc: # Python >2.5
        pass


"""
label {
  name: "bend/bow (at the waist)"
  label_id: 1
  label_type: PERSON_MOVEMENT
}
"""
label_dict = {}
# parse action names
with open(actionlistfile) as f:
	while True:
		line1 = f.readline()
		if line1 == '': break # EOF
		
		line2 = f.readline()
		line3 = f.readline()
		line4 = f.readline()
		line5 = f.readline()
		
		label_name = ':'.join(line2.split(':')[1:]).strip()[1:-1]
		label_id = line3.split(':')[1].strip()
		label_type = line4.split(':')[1].strip()
		
		label_dict[label_id] = [label_type, label_name]

# extract all clips and middle frames
with open(annotfile) as f:
	annots = f.read().splitlines()

#The format of a row is the following: video_id, middle_frame_timestamp, person_box, action_id
#-5KQ66BBWC4,0904,0.217,0.008,0.982,0.966,12

if FLAGS.partial_process:
	assert FLAGS.partial_num > 0, "Partial process number should be positive."
	assert FLAGS.partial_start < len(annots), "Start index is larger than annotation number!"
	annot_range = range(FLAGS.partial_start, min(FLAGS.partial_start + FLAGS.partial_num, len(annots)))
else:
	annot_range = range(len(annots))

for annot_number in annot_range:
	# PARSE ANNOTATION STRING
	ann = annots[annot_number]
	seg = ann.split(',')
	
	video_id = seg[0]
	middle_frame_timestamp = int(seg[1]) # in seconds
	left_bbox = float(seg[2]) # from 0 to 1
	top_bbox = float(seg[3])
	right_bbox = float(seg[4])
	bottom_bbox = float(seg[5])
	action_id = seg[6]
	
	
	videofile_noext = os.path.join(videodir, video_id)
	videofile = subprocess.check_output('ls %s*' % videofile_noext, shell=True)
	videofile = videofile.split()[0]
	
	if sys.version > '3.0':
		videofile = videofile.decode('utf-8')
	video_extension = videofile.split('.')[-1]
	
	# OPEN VIDEO FOR INFORMATION IF NECESSARY
	vcap = cv2.VideoCapture(videofile) # 0=camera
	if vcap.isOpened():
		# get vcap property 
		if cv2.__version__ < '3.0':
			vidwidth = vcap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)   # float
			vidheight = vcap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT) # float
		else:
			vidwidth = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)	# float
			vidheight = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)	# float
		# or
		# vidwidth = vcap.get(3)  # float
		# vidheight = vcap.get(4) # float
	else:
		exit(1)
	
	# EXTRACT KEYFRAME WITH FFMPEG
	
	print(middle_frame_timestamp)
	
	outdir_keyframe = os.path.join(outdir_midframe, video_id)
	mkdir_p(outdir_keyframe)
	
	outpath = os.path.join(outdir_keyframe, '%d.jpg' % (int(middle_frame_timestamp)))
	ffmpeg_command = 'rm %(outpath)s; ffmpeg -ss %(timestamp)f -i %(videopath)s -frames:v 1 %(outpath)s' % {
		'timestamp': float(middle_frame_timestamp),
		'videopath': videofile,
		'outpath': outpath
		}
	
	subprocess.call(ffmpeg_command, shell=True)
	#subprocess.call('eog %(outpath)s &' % {'outpath': outpath}, shell=True)
	
	# EXTRACT CLIPS WITH FFMPEG
	
	print(middle_frame_timestamp)
	
	outdir_clip = os.path.join(outdir_clips, video_id)
	mkdir_p(outdir_clip)
	
	# ffmpeg -i a.mp4 -force_key_frames 00:00:09,00:00:12 out.mp4
	# ffmpeg -ss 00:00:09 -i out.mp4 -t 00:00:03 -vcodec copy -acodec copy -y final.mp4
	
	clip_start = middle_frame_timestamp - clip_time_padding - float(clip_length) / 2
	if clip_start < 0:
		clip_start = 0
	clip_end = middle_frame_timestamp + float(clip_length) / 2
	
	outpath_clip = os.path.join(outdir_clip, '%d.%s' % (int(middle_frame_timestamp), video_extension))
	#outpath_clip_tmp = outpath + '_tmp.%s' % video_extension
	
	ffmpeg_command = 'rm %(outpath)s; ffmpeg -ss %(start_timestamp)s -i %(videopath)s -g 1 -force_key_frames 0 -t %(clip_length)d %(outpath)s' % {
		'start_timestamp': hou_min_sec(clip_start * 1000),
		'end_timestamp': hou_min_sec(clip_end * 1000),
		'clip_length': clip_length + clip_time_padding,
		'videopath': videofile,
		'outpath': outpath_clip
		}
	
	subprocess.call(ffmpeg_command, shell=True)
	#subprocess.call('eog %(outpath)s &' % {'outpath': outpath}, shell=True)
	
	
	
	
	
	# LOAD GENERATED JPG, CREATE SVG, OVERLAY BOUNDING BOX
	outdir_keyframe_svg = os.path.join(outdir, 'visu_svg', video_id)
	mkdir_p(outdir_keyframe_svg)
	
	outpath_svg = os.path.join(outdir_keyframe_svg, '%d_%s_%d.svg' % (int(middle_frame_timestamp), action_id, annot_number))

	svg_document = svgwrite.Drawing(filename = outpath_svg,
	                                size = ("%dpx" % vidwidth, "%dpx" % vidheight))
	
	svg_document.add(svg_document.image(outpath))
	
	# ADD BBOX
	insert_left = vidwidth * left_bbox
	insert_top = vidheight * top_bbox
	bbox_width = vidwidth * (right_bbox - left_bbox)
	bbox_height = vidheight * (bottom_bbox - top_bbox)
	
	svg_document.add(svg_document.rect(insert = (insert_left, insert_top),
		size = ("%dpx" % bbox_width, "%dpx" % bbox_height),
		stroke_width = "5",
		stroke = "rgb(255,100,100)",
		fill = "rgb(255,100,100)",
		fill_opacity=0.0)
	)
	
	# ADD ACTION CAPTION
	actioncaption = ''
	label_type_and_name = label_dict.get(action_id)
	if label_type_and_name != None:
		svg_document.add(svg_document.text("%s" % (label_type_and_name[0]),
			insert = (10, 20),
			fill = "rgb(255,30,30)",
			font_size = "22px")
		)
		svg_document.add(svg_document.text("%s" % (label_type_and_name[1]),
			insert = (10, 40),
			fill = "rgb(255,30,30)",
			font_size = "22px",
			font_weight = "bold")
		)
	
	print(svg_document.tostring())
	svg_document.save()
	
	outdir_visu_jpg = os.path.join(outdir, 'visu_jpg', video_id)
	mkdir_p(outdir_visu_jpg)
	outpath_visu_jpg = os.path.join(outdir_visu_jpg, '%d_%s_%d.jpg' % (int(middle_frame_timestamp), action_id, annot_number))
	
	subprocess.call('convert -- "%s" "%s"' % (outpath_svg, outpath_visu_jpg), shell=True)
	
	
	print("")
	print("ffmpeg_command:", ffmpeg_command)
	print("middle_frame_timestamp:", middle_frame_timestamp)
	print("time:", hou_min_sec(middle_frame_timestamp))
	print("action_id:", action_id)




