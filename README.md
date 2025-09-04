# Hailo-8 License Plate Detection (LPD)

This project enables real-time **license plate detection on vehicle videos** using the powerful **Hailo-8 AI accelerator**.

Whether you want to run fast inference directly from the terminal or explore a user-friendly GUI, this repository provides everything you need to get started.

---

## 🚀 LPD Library

### Build & Install the LPD Library

First, make sure you have **ninja-build** installed:

```bash
sudo apt install ninja-build
```

Then, build and install the library from the `lpd_lib` directory (located in the root of this repository):

```bash
cd lpd_lib
meson setup builddir --prefix /opt/hailo/tappas/
ninja -C builddir
sudo ninja -C builddir install
```

---

### Run Inference on an MP4 Video (Terminal)

From the root of the repository, you can apply license plate detection to any video with:

```bash
# ./bin/apply_lpd_to_video <tappas_workspace_dir> <install_dir> <input_video> <output_video>
./bin/apply_lpd_to_video /local/workspace/tappas /local/workspace/rr-lpr-app /local/workspace/hailo8-LPD/lpd_app/gui/assets/video_example.mp4 output.mp4
```

This will process the input video and generate a new MP4 file with license plate detection results.

---

## 💻 LPD App (GUI)

For a more interactive experience, use the **Python-based GUI application**.

### Installation

Install the Python dependencies and the app itself:

```bash
pip3 install -r requirements.txt
pip3 install .
```

---

### Launch the GUI

Start the application with:

```bash
./bin/run_gui
```

You’ll get a simple and intuitive interface to apply license plate detection to your videos.