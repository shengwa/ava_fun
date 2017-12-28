"""Script to download youtube videos of AVA dataset.
"""
import argparse
import glob
import os
import pathlib
import re
import subprocess
import sys
import requests

import pafy

BASE_URL = 'https://www.youtube.com/watch?v='
UNAVAILABLE_VIDEOS_LINK = 'http://pascal.inrialpes.fr/data2/ava_cache/cache/'
YOUTUBE_FILE_PATTERN = r'[\w]{11}.[\w]{3,6}'

def parse_args():
    """Parse input arguments.
    """
    parser = argparse.ArgumentParser(description='AVA videos download script.')
    parser.add_argument('--download_train', type=bool, default=False,
                        help='If to download the training videos.')
    parser.add_argument('--download_test', type=bool, default=False,
                        help='If to download the testing videos.')
    parser.add_argument('--download_unavailable', type=bool, default=False,
                        help='If to download unavailable videos from website.')
    parser.add_argument('--train_file', type=str,
                        default='ava_ytids_train_v1.0.txt',
                        help='The file of training video IDs.')
    parser.add_argument('--test_file', type=str,
                        default='ava_ytids_test_v1.0.txt',
                        help='The file of testing video IDs.')
    parser.add_argument('--user_name', type=str, default=None,
                        help='The user name and password to download the \
                             unavailable videos from \
                             http://thoth.inrialpes.fr/ava/requestaccess.php')
    parser.add_argument('--password', type=str, default=None,
                        help='The user name and password to download the \
                             unavailable videos from \
                             http://thoth.inrialpes.fr/ava/requestaccess.php')
    parser.add_argument('--output_path', type=str, default='ava_videos')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()

def video_download_from_id(video_id, output_path):
    """Download a Youtube video with its id.
    """
    # Check if video has been downloaded.
    videos = glob.glob(os.path.join(output_path, '*' + video_id + '.*'))
    if len(videos) > 0:
        print('Video file exists, skipping download.')
        return
    # Download when video is not there.
    print('Starting download video with id %s' % video_id)
    url = BASE_URL + video_id
    try:
        pafy.new(url)
    except IOError:
        print('Downloading video with id %s failed.' % video_id)
        return
    video = pafy.new(url)
    print('Video Title: ', video.title)
    best = video.getbest()
    output_name = video_id + '.' + best.extension
    best.download(filepath=os.path.join(output_path, output_name))

def get_video_ids_from_file(video_id_file):
    """Get all the video id from a file.
    """
    with open(video_id_file) as file_reader:
        id_list = file_reader.readlines()
    id_list = [x.strip() for x in id_list]
    return id_list

def download_videos(video_id_file, output_path):
    """Download all the videos from a video ids file.
    """
    id_list = get_video_ids_from_file(video_id_file)
    for video_id in id_list:
        video_download_from_id(video_id, output_path)

def download_video_from_link(video_link, output_path, user, password):
    """Download a video link with credentials.
    """
    video_file = video_link.split('/')[-1]
    subprocess.check_call('wget %s -O %s --user %s --password %s' % (
        video_link,
        os.path.join(output_path, video_file),
        user, password), shell=True)

def download_unavailable_videos(user, password, output_path):
    """Download unavailable videos from
       http://pascal.inrialpes.fr/data2/ava_cache/cache/ .
    """
    # Get video files from web page.
    html_text = requests.get(UNAVAILABLE_VIDEOS_LINK,
                             auth=(user, password)).text
    video_files = list(set(re.findall(YOUTUBE_FILE_PATTERN, html_text)))
    video_files.sort()
    for video_file in video_files:
        video_id = video_file.split('.')[0]
        videos = videos = glob.glob(os.path.join(output_path,
                                                 '*' + video_id + '.*'))
        if len(videos) > 0:
            print('Video id %s exists, skipping download.' % video_id)
            continue
        video_url = os.path.join(UNAVAILABLE_VIDEOS_LINK, video_file)
        download_video_from_link(video_url, output_path, user, password)

if __name__ == '__main__':
    FLAGS = parse_args()
    if FLAGS.output_path:
        pathlib.Path(FLAGS.output_path).mkdir(parents=True, exist_ok=True)
    if FLAGS.download_train:
        # Download training videos.
        download_videos(FLAGS.train_file, FLAGS.output_path)
    if FLAGS.download_test:
        # Download testing videos.
        download_videos(FLAGS.test_file, FLAGS.output_path)
    if FLAGS.download_unavailable:
        # Download unavailable videos.
        assert FLAGS.user_name and FLAGS.password, \
        'Username and Password must be provided.'
        download_unavailable_videos(FLAGS.user_name, FLAGS.password,
                                    FLAGS.output_path)
