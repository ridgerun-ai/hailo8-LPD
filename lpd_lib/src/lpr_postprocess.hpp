/**
* Copyright (c) 2021-2022 Hailo Technologies Ltd. All rights reserved.
* Distributed under the LGPL license (https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt)
* Copyright (c) 2025 RidgeRun <support@ridgerun.ai>. All rights reserved.
**/
#include <gst/video/video.h>
#include <opencv2/opencv.hpp>
#include "hailo_objects.hpp"
#include "hailomat.hpp"

G_BEGIN_DECLS
void filter(HailoROIPtr roi, GstVideoFrame *frame);
std::vector<HailoROIPtr> crop_vehicles(std::shared_ptr<HailoMat> image, HailoROIPtr roi);
G_END_DECLS