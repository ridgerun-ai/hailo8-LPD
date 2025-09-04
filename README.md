# Hailo 8 License Plate Detection

## LPD Library

### Build and install the LPD library

To build and install the library go to the lpd_lib directory (located in the root of this repository) and run the following commands:

```bash
cd lpd_lib
meson setup builddir -Dtappas_dir=/local/workspace/tappas -Dinstall_dir=/local/workspace/rr-lpr-app
ninja -C builddir
ninja -C builddir install
```

### Apply inference to an MP4 video using the terminal

Go to the root of the repository and run the following command command:

```bash
# ./bin/apply_lpd_to_video <tappas_workspace_dir> <install_dir> <input_video> <output_video>
./bin/apply_lpd_to_video /local/workspace/tappas /local/workspace/rr-lpr-app /local/workspace/hailo8-LPD/lpd_app/gui/assets/video_example.mp4 output.mp4
```

## LPD App

### Installing the project

Install the python project and the python required dependencies.

```bash
pip3 install -r requirements.txt
pip3 install .
```

Run the app:

```bash
./bin/run_gui
```