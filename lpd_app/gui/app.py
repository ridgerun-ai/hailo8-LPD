# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.

# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

import gradio as gr
import os

from lpd_app.algorithm.video import VideoProcessor

# The name that will be seen in the browser tab
TITLE_NAME = "TAB NAME"

# Load HTML, CSS and JS code
PRODUCT_INFO_HTML = open("lpd_app/gui/assets/product_info.html").read()
JS_CODE = open("lpd_app/gui/assets/disable_download.js").read()
CSS_CODE = open("lpd_app/gui/assets/product_info.css").read()

SUPPORTED_VIDEO_FORMATS = [".mp4"]
SUPPORTED_FILES = SUPPORTED_VIDEO_FORMATS

EXAMPLE_VIDEO1 = ["lpd_app/gui/assets/video_example.mp4"]
EXAMPLES = [EXAMPLE_VIDEO1]


class App:

    def __init__(self):
        self.video_processor = VideoProcessor()

    def apply_to_video(self, input_video_path, output_video_path):

        self.video_processor.apply(input_video_path, output_video_path)

        return gr.Video(value=output_video_path, visible=True)

    def apply(self, file):

        if not file:
            raise gr.Error("Error, no file uploaded.")

        file_name, file_extension = os.path.splitext(os.path.basename(file))
        output_dir = os.path.dirname(file)
        output_file_path = f"{output_dir}/{file_name}_lpd{file_extension}"

        if file_extension.lower() not in SUPPORTED_FILES:
            raise gr.Error(
                f"File extension {file_extension} not supported.\
                    Please upload {' '.join(SUPPORTED_FILES)} file."
            )

        return self.apply_to_video(file, output_file_path)

    def clear_output(self, _):
        return (
            gr.File(value=None, visible=True),
            gr.Video(value=None),
            gr.Video(value=None, visible=False),
        )

    def input_file_uploaded(self, input_path):

        if not input_path:
            return gr.File(), gr.Video(visible=False)

        _, file_extension = os.path.splitext(os.path.basename(input_path))

        if file_extension.lower() not in SUPPORTED_FILES:
            raise gr.Error(
                f"File extension {file_extension} not supported.\
                    Please upload {' '.join(SUPPORTED_FILES)} file."
            )

        return gr.File(visible=False), gr.Video(input_path, visible=True)

    def run(self):

        with gr.Blocks(css=CSS_CODE, title=TITLE_NAME) as demo:
            with gr.Column():

                gr.HTML(PRODUCT_INFO_HTML, show_label=False)

                with gr.Row():
                    with gr.Column():

                        input_file = gr.File(
                            label="Video", file_types=SUPPORTED_FILES, scale=2
                        )

                        video_preview = gr.Video(
                            visible=False, label="Preview Video", interactive=False
                        )

                        with gr.Row():
                            button_process = gr.Button("Process")
                            button_clear = gr.Button("Clear")

                    with gr.Column():
                        with gr.Row():
                            video_output = gr.Video(
                                label="Output Video", interactive=False
                            )

            gr.Examples(examples=EXAMPLES, inputs=[input_file])

            input_file.change(
                self.input_file_uploaded,
                inputs=input_file,
                outputs=[input_file, video_preview],
            )
            button_process.click(
                self.apply, inputs=[input_file], outputs=[video_output]
            )
            button_clear.click(
                self.clear_output,
                inputs=input_file,
                outputs=[input_file, video_output, video_preview],
            )
            input_file.clear(
                self.clear_output,
                inputs=video_output,
                outputs=[input_file, video_output],
            )

            demo.load(js=JS_CODE)
            demo.queue()
            demo.launch(
                share=True,
                show_api=False,
                favicon_path="lpd_app/gui/assets/icon.png",
                allowed_paths=[
                    "lpd_app/gui/assets/dark_diagram.png",
                    "lpd_app/gui/assets/light_diagram.png",
                    "lpd_app/gui/assets/dark_logo.png",
                    "lpd_app/gui/assets/light_logo.png",
                ],
            )
