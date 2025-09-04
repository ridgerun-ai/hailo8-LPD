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

WATERMARK_PATH = 'web_model_server/assets/rr_watermark.png'

class WatermarkProcessor:

    def __init__(self, img_width, img_height):

        # Load watermark image with all the channels
        self.watermark = cv2.imread(WATERMARK_PATH, cv2.IMREAD_UNCHANGED)

        # Get dimensions of the watermark
        wm_height, wm_width = self.watermark.shape[:2]

        # Calculate aspect ratio
        aspect_ratio = wm_width / wm_height

        # Calculate new dimensions maintaining aspect ratio
        if img_width / img_height > aspect_ratio:
            new_width = img_width
            new_height = int(new_width // aspect_ratio)
        else:
            new_height = img_height
            new_width = int(new_height * aspect_ratio)

        # Resize watermark
        self.watermark = cv2.resize(
            self.watermark, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Crop watermark if it's larger than the image dimensions
        if new_height > img_height or new_width > img_width:
            self.watermark = self.watermark[:img_height, :img_width]

        # Prepare alpha masks for blending the watermark with the image
        # Extract the alpha channel and normalize it to the range [0, 1]
        self.alpha_mask = self.watermark[:, :, 3] / 255.0
        
        # Create the inverse of the alpha mask
        self.alpha_image = 1.0 - self.alpha_mask

    def apply_watermark_to_image(self, image):
        
        # Add watermark to cover the entire image (applying the transparency)
        for c in range(0, 3):
            image[:, :, c] = (
                self.alpha_mask * self.watermark[:, :, c] +
                self.alpha_image * image[:, :, c]
            )
        return image
