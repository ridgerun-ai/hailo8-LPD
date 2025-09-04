# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

import gi
import gradio as gr
import os

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

TAPPAS_WORKSPACE_DIR = os.getenv("TAPPAS_WORKSPACE", "/local/workspace/tappas")

# Vehicle detection yolov5m
VEHICLE_DETECTION_HEF_DIR = f"{TAPPAS_WORKSPACE_DIR}/apps/h8/gstreamer/general/license_plate_recognition/resources/yolov5m_vehicles.hef"
VEHICLE_DETECTION_CONFIG_DIR = f"{TAPPAS_WORKSPACE_DIR}/apps/h8/gstreamer/general/license_plate_recognition/resources/configs/yolov5_vehicle_detection.json"
VEHICLE_DETECTION_POSTPROCESS_LIB_DIR = f"{TAPPAS_WORKSPACE_DIR}/apps/h8/gstreamer/libs/post_processes/libyolo_hailortpp_post.so"
VEHICLE_DETECTION_POSTPROCESS_FUNCTION = "yolov5m_vehicles"

# Cropping Algorithm
VEHICLE_CROPPER_FUNCTION = "crop_vehicles"

# License Plate detection yolov4
PLATE_DETECTION_HEF_DIR = f"{TAPPAS_WORKSPACE_DIR}/apps/h8/gstreamer/resources/hef/tiny_yolov4_license_plates.hef"
PLATE_DETECTION_CONFIG_DIR = f"{TAPPAS_WORKSPACE_DIR}/apps/h8/gstreamer/general/license_plate_recognition/resources/configs/yolov4_license_plate.json"
PLATE_DETECTION_POSTPROCESS_LIB_DIR = (
    f"{TAPPAS_WORKSPACE_DIR}/apps/h8/gstreamer/libs/post_processes/libyolo_post.so"
)
PLATE_DETECTION_POSTPROCESS_FUNCTION = "tiny_yolov4_license_plates"

RR_LPR_POSTPROCESS = "/opt/hailo/tappas/lib/x86_64-linux-gnu/liblpr_postprocess.so"

Gst.init(None)


class VideoProcessor:
    def __init__(self):
        self.pipeline = None

    def apply(self, video_path, output_path):

        pipeline_str = f"""
            filesrc location={video_path} !
            decodebin !
            videoscale ! video/x-raw,pixel-aspect-ratio=1/1 !
            videoconvert !
            queue leaky=no max-size-buffers=30 max-size-bytes=0 max-size-time=0 !
            hailonet hef-path={VEHICLE_DETECTION_HEF_DIR}
                vdevice-group-id=1
                scheduling-algorithm=1
                scheduler-threshold=1
                scheduler-timeout-ms=100
                nms-score-threshold=0.3
                nms-iou-threshold=0.45
                output-format-type=HAILO_FORMAT_TYPE_FLOAT32 !
            queue !
            hailofilter
                so-path={VEHICLE_DETECTION_POSTPROCESS_LIB_DIR}
                function-name={VEHICLE_DETECTION_POSTPROCESS_FUNCTION}
                config-path={VEHICLE_DETECTION_CONFIG_DIR}
                qos=false !
            queue !
            hailotracker
                keep-past-metadata=true
                kalman-dist-thr=.5
                iou-thr=.6
                keep-tracked-frames=2
                keep-lost-frames=2 !
            queue !
            hailocropper
                so-path={RR_LPR_POSTPROCESS}
                function-name={VEHICLE_CROPPER_FUNCTION}
                internal-offset=true
                drop-uncropped-buffers=true
                name=cropper1
            hailoaggregator name=agg1
            cropper1. ! queue ! agg1.
            cropper1. ! video/x-raw,width=416,height=416 ! queue !
            hailonet hef-path={PLATE_DETECTION_HEF_DIR}
                vdevice-group-id=1
                scheduling-algorithm=1
                scheduler-threshold=5
                scheduler-timeout-ms=100 !
            queue !
            hailofilter
                so-path={PLATE_DETECTION_POSTPROCESS_LIB_DIR}
                config-path={PLATE_DETECTION_CONFIG_DIR}
                function-name={PLATE_DETECTION_POSTPROCESS_FUNCTION}
                qos=false !
            queue ! agg1.
            agg1. ! queue !
            hailofilter use-gst-buffer=true so-path={RR_LPR_POSTPROCESS} qos=false !
            hailooverlay line-thickness=1 font-thickness=1 qos=false !
            videoconvert ! avenc_mpeg4 ! mp4mux ! filesink location={output_path} sync=false
        """

        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
        except GLib.GError as e:
            raise gr.Error(
                f"An error ocurred while trying to process the video: {e.message}"
            )
        except Exception as e:
            raise gr.Error(f"An error ocurred while trying to process the video: {e}")

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()

        def on_message(bus, message):
            t = message.type
            if t == Gst.MessageType.ERROR:
                err, debug = message.parse_error()
                if debug:
                     raise gr.Error(f"An error ocurred while trying to process the video: {debug}")
                self.pipeline.set_state(Gst.State.NULL)
                loop.quit()
            elif t == Gst.MessageType.EOS:
                self.pipeline.set_state(Gst.State.NULL)
                loop.quit()

        bus.connect("message", on_message)

        loop = GLib.MainLoop()

        try:
            self.pipeline.set_state(Gst.State.PLAYING)
            loop.run()
        except Exception as e:
            self.pipeline.set_state(Gst.State.NULL)
            raise gr.Error(f"An error ocurred while trying to process the video: {e}")

        return output_path
