# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

import numpy as np
import cv2

from web_model_server.utils.watermark import WatermarkProcessor


class ImageProcessor:
    """
    This class process the images that will be display on gui.
    """
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ImageProcessor, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not hasattr(self, 'is_initialized'):
            self.is_initialized = True

    def apply(self, input_image_path, output_image_path):
        """
        Applies watermark and grayscale to image.

        Parameters:
            input_image_path (str): Path from input image.
            output_image_path (str): Path to output image.
        """

        # Load image
        input_image = cv2.cvtColor(cv2.imread(input_image_path), cv2.COLOR_BGR2RGB)
        
        # Get resolution
        input_height, input_width, _ = input_image.shape
        
        # Create the watermark processor
        self.watermarkProcessor = WatermarkProcessor(input_width, input_height)

        # Add watermark to the image
        processed_frame = self.watermarkProcessor.apply_watermark_to_image(input_image)

        # Save processed grayscale image
        cv2.imwrite(output_image_path, cv2.cvtColor(processed_frame, cv2.COLOR_RGB2GRAY))
