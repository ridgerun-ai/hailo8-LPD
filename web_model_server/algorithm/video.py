# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

import cv2
import ffmpeg
from web_model_server.utils.watermark import WatermarkProcessor

WATHERMARK_PATH = 'web_model_server/.assets/rr_watermark.png'


class VideoProcessor:
    """
    This class process the videos that will be display on gui.
    """
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(VideoProcessor, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not hasattr(self, 'is_initialized'):
            self.is_initialized = True

    def apply(self, video_path, output_path):
        """
        Applies watermark and BGR to video.

        Parameters:
            video_path (str): Path from input video.
            output_path (str): Path to output video.
        """

        vid = cv2.VideoCapture(video_path)

        input_width  = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        input_height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        input_fps = vid.get(cv2.CAP_PROP_FPS)

        # Process to save video with ffmpeg due to issue with opencv videowriter
        # format compatibility with browser standards
        process = (
            ffmpeg
            .input('pipe:0', format='rawvideo', pix_fmt='bgr24',
                    s=f'{input_width}x{input_height}', r=input_fps)
            .output(output_path,
                    vcodec='libx264', video_bitrate='1500k', pix_fmt='gray16',
                    format='mp4')
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

        # Create the watermark processor
        self.watermarkProcessor = WatermarkProcessor(input_width, input_height)

        while(True):
            ret, frame = vid.read() 
            if ret==True: 
                processed_frame = self.watermarkProcessor.apply_watermark_to_image(frame)
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                process.stdin.write(bgr_frame.tobytes())
            else:
                break
        
        vid.release()
        process.stdin.close()
        process.wait()
