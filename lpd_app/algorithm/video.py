# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

import subprocess

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
        Applies License Plate Detection to video.

        Parameters:
            video_path (str): Path from input video.
            output_path (str): Path to output video.
        """

        pipeline = [
            "gst-launch-1.0",
            "filesrc", f"location={video_path}",
            "!", "decodebin",
            "!", "videoflip", "method=rotate-180",
            "!", "x264enc", "tune=zerolatency", "speed-preset=ultrafast",
            "!", "mp4mux",
            "!", f"filesink location={output_path}"
        ]

        try:
            subprocess.run(" ".join(pipeline), shell=True, check=True)
        except subprocess.CalledProcessError as e:
            return None

        return output_path