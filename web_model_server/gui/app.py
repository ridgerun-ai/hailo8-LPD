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

from web_model_server.algorithm.video import VideoProcessor
from web_model_server.algorithm.image import ImageProcessor
from web_model_server.utils import media_utils
from web_model_server.database.analytics_db import AnalyticsDB

# The name that will be seen in the browser tab
TITLE_NAME = "TAB NAME"

# Load HTML, CSS and JS code
PRODUCT_INFO_HTML = open('web_model_server/gui/assets/product_info.html').read()
JS_CODE = open('web_model_server/gui/assets/disable_download.js').read()
CSS_CODE = open('web_model_server/gui/assets/product_info.css').read()

INVALID_EMAIL_HTML_TEXT = """
<span class="email">Invalid email address. Please enter a valid email.</span>
"""
EMPTY_EMAIL_HTML_TEXT = """
<span class="email">Please enter an email to enable the processing buttons.</span>
"""

MAX_FILE_SIZE_MB = 30
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1000000  # 30 Mb
MAX_VIDEO_LENGHT = 30  # Seconds
SUPPORTED_VIDEO_FORMATS = ['.mp4']
SUPPORTED_IMAGE_FORMATS = ['.jpeg', '.jpg', '.png']
SUPPORTED_FILES = SUPPORTED_VIDEO_FORMATS + SUPPORTED_IMAGE_FORMATS

EXAMPLE_IMAGE1 = ['web_model_server/gui/assets/image_example.jpg']
EXAMPLE_VIDEO1 = ['web_model_server/gui/assets/video_example.mp4']
EXAMPLES = [EXAMPLE_IMAGE1, EXAMPLE_VIDEO1]

class App:

    def __init__(self):
        self.video_processor = VideoProcessor()
        self.image_processor = ImageProcessor()
        self.analytics_db = AnalyticsDB()

    def apply_to_video(self, input_video_path, output_video_path, email):
        
        self.video_processor.apply(input_video_path, output_video_path)
        self.analytics_db.log_request(email, 'GenerateVideo')

        return gr.Video(value=output_video_path, visible=True)

    def apply_to_image(self, input_image_path, output_image_path, email):

        self.image_processor.apply(input_image_path, output_image_path)
        self.analytics_db.log_request(email, 'GenerateImage')

        return gr.Image(value=output_image_path, visible=True)

    def apply(self, file, email):

        if not file:
            raise gr.Error(f"Error, no file uploaded.")
        
        if not media_utils.is_valid_email(email):
            raise gr.Error("Invalid email address. Please enter a valid email.")

        file_name, file_extension = os.path.splitext(os.path.basename(file))
        output_dir = os.path.dirname(file)
        output_file_path = f"{output_dir}/{file_name}_blurred{file_extension}"

        if not file_extension.lower() in SUPPORTED_FILES:
            raise gr.Error(
                f"File extension {file_extension} not supported.\
                    Please upload {' '.join(SUPPORTED_FILES)} file.")

        file_size = os.path.getsize(file)

        if file_size > MAX_FILE_SIZE:
            raise gr.Error(
                f"File size exceeds the {MAX_FILE_SIZE_MB} MB limit.\
                    Please upload a smaller file.")

        if file_extension.lower() in SUPPORTED_VIDEO_FORMATS:
            
            if media_utils.get_video_duration(file) > MAX_VIDEO_LENGHT:
                raise gr.Error(
                    f"File size exceeds the {MAX_VIDEO_LENGHT} \
                        seconds length limit. Please upload a smaller file.")
            
            return self.apply_to_video(file, output_file_path, email), \
                gr.Image(visible=False)
        else:
            return gr.Video(visible=False), \
                self.apply_to_image(file, output_file_path, email)

    def clear_output(self, output):
        return gr.File(value=None, visible=True), \
            gr.Video(visible=False), \
            gr.Image(value=None, visible=True)
    
    def update_email(self, input):
        if input:
            return gr.Button(interactive=True)
        else:
            return gr.Button(interactive=False)
        
    def input_file_uploaded(self, input_path):
        
        if not input_path:
            return gr.File(), gr.Video(visible=False), gr.Image(visible=False)
        
        _, file_extension = \
            os.path.splitext(os.path.basename(input_path))
        
        if not file_extension.lower() in SUPPORTED_FILES:
            raise gr.Error(
                f"File extension {file_extension} not supported.\
                    Please upload {' '.join(SUPPORTED_FILES)} file.")
        
        if file_extension.lower() in SUPPORTED_VIDEO_FORMATS:
            return gr.File(visible=False), \
                gr.Video(input_path,
                        visible=True), \
                gr.Image(visible=False)
        else:
            return gr.File(visible=False), gr.Video(visible=False), \
                gr.Image(input_path, visible=True)

    def run(self):

        with gr.Blocks(css=CSS_CODE, title=TITLE_NAME) as demo:
            with gr.Column():

                gr.HTML(PRODUCT_INFO_HTML, show_label=False)

                with gr.Row():
                    with gr.Column():
                        
                        email_input = gr.Textbox(label="Email (required)", 
                                                 type='email', 
                                                 placeholder=
                                                 'Enter your email')
                         
                        @gr.render(inputs=email_input)
                        def show_warning(email):
                            if not email:
                                gr.HTML(EMPTY_EMAIL_HTML_TEXT)
                            elif not media_utils.is_valid_email(email):
                                gr.HTML(INVALID_EMAIL_HTML_TEXT)
                            else:
                                gr.HTML(render=False, visible=False)

                        input_file = gr.File(
                            label="Video or Image", 
                            file_types=SUPPORTED_FILES, scale=2)
                        
                        image_preview = gr.Image(visible=False, 
                                                 label="Preview Image", 
                                                 show_download_button=False)
                        video_preview = gr.Video(visible=False, 
                                                 label="Preview Video",
                                                 interactive=False,
                                                 show_download_button=False)
                        
                        with gr.Row():
                            button_process = gr.Button("Process", interactive=False)
                            button_clear = gr.Button("Clear")

                    with gr.Column():
                        with gr.Row():
                            video_output = gr.Video(visible=False, 
                                                    label="Output Video",
                                                    interactive=False,
                                                    show_download_button=False,
                                                    include_audio=True)
                            image_output = gr.Image(
                                visible=True, interactive=False)
                            
            examples = gr.Examples(examples=EXAMPLES,inputs=[input_file])
            
            input_file.change(self.input_file_uploaded, inputs=input_file, 
                              outputs=[input_file,
                                       video_preview, 
                                       image_preview])
            email_input.change(self.update_email, inputs=email_input, 
                               outputs=button_process)
            button_process.click(self.apply, 
                                 inputs=[input_file, email_input], 
                                 outputs=[video_output, 
                                          image_output])
            button_clear.click(self.clear_output, inputs=input_file, outputs=[
                               input_file, video_output, image_output])
            input_file.clear(self.clear_output, inputs=image_output, outputs=[
                             input_file, video_output, image_output])

            demo.load(js=JS_CODE)
            demo.queue()
            demo.launch(show_api=False,
                        max_file_size=f"{MAX_FILE_SIZE_MB}mb",
                        favicon_path="web_model_server/gui/assets/icon.png",
                        allowed_paths=[
                            "web_model_server/gui/assets/dark_diagram.png", 
                            "web_model_server/gui/assets/light_diagram.png",
                            "web_model_server/gui/assets/dark_logo.png",
                            "web_model_server/gui/assets/light_logo.png"
                        ])