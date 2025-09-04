# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.

# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

import numpy as np
import ffmpeg
import re

def get_media_info(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        return probe
    except ffmpeg.Error as e:
        print(f"Error: {e.stderr.decode('utf8')}")
        return None

def is_video(media_info):
    for stream in media_info.get('streams', []):
        if stream.get('codec_type') == 'video':
            return True
    return False

def get_video_duration(file_path):
    media_info = get_media_info(file_path)
    
    if media_info and is_video(media_info):
        duration = float(media_info['format']['duration'])
        return duration
    else:
        return None

def extract_frames_rgb(video_path):
    process = (
        ffmpeg
        .input(video_path)
        .output('pipe:', format='rawvideo', pix_fmt='rgb24')
        .run_async(pipe_stdout=True)
    )
    
    input_width, input_height, _ = get_video_dimensions_and_fps(video_path)
    
    while True:
        in_bytes = process.stdout.read(input_width * input_height * 3)
        if not in_bytes:
            break
        frame = np.copy(np.frombuffer(in_bytes, np.uint8).reshape(input_height, input_width, 3))
        yield frame

    process.stdout.close()
    process.wait()

def get_video_dimensions_and_fps(video_path):
    probe = ffmpeg.probe(video_path)
    video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    width = int(video_info['width'])
    height = int(video_info['height'])
    r_frame_rate = video_info['r_frame_rate']
    num, denom = map(int, r_frame_rate.split('/'))
    fps = num / denom
    return width, height, fps

def video_has_audio(video_path):
    return any(
        stream.get('codec_type') == 'audio'
        for stream in ffmpeg.probe(video_path)['streams']
        )
    
def get_blurring_level(faces, width, height):
    if not faces:
        return 0

    faces_size = []
    for face in faces:
        # Remove the square brackets and split the string by commas
        face = str(face).strip('[]')
        face_rect_list_str = face.split(',')

        # Convert the string elements to floats
        face_rect_list = [float(element) for element in face_rect_list_str]
        faces_size.append((face_rect_list[2] * width, face_rect_list[3] * height))
    
    largest_face = max(max(faces_size, key=lambda t: max(t)))
    
    blur_level = largest_face // 2
    
    if blur_level % 2 == 0:
        blur_level += 1
        
    return blur_level

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)
