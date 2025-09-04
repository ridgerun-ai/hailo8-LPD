# BASE DOCKER IMAGE
FROM ubuntu:20.04

########################################################################
# DOCKER BUILD ARGS
#
# In this section you pass in arguments to configure the build, such as
# GitLab/GitHub user names and API Tokens, etc...
########################################################################
ARG USERNAME
ARG ACCESS_TOKEN
ARG BRANCH="main"
ARG USERNAME_YOUR_REPO
ARG ACCESS_TOKEN_YOUR_REPO
ARG <YOUR ARGS>

########################################################################
# DOCKER BUILD ENVS
#
# In this section you define the enviroment variables to configure your
# dependencies.Enable DEBIAN_FRONTEND for non interactive interface.
#
# WARNING: Never add credentials, API tokens or any security data.
#########################################################################
ENV DEBIAN_FRONTEND=noninteractive
ENV ORT_VERSION=1.15.0
ENV CMAKE_VERSION=3.27.1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV <YOUR ENV VARIABLES>

########################################################################
# DOCKER PORTS EXPOSE
#
# In this section you can define the ports for comunicating your app 
# to the internet
#########################################################################
EXPOSE 7860
EXPOSE <YOUR PORT APP>

########################################################################
# INSTALLING DEPENDENCIES
#
# In this section you can install all the packages that your application
# needs, be sure of versions and to UPDATE your APT.
#########################################################################
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    <YOUR PACKAGES> \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install protobuf==3.20.1 wheel==0.35.1 numpy==1.24.4 packaging==22.0 meson==1.2.3 pybind11==2.13.1

########################################################################
# INSTALLING AND CONFIGURING PACKAGE (OPTIONAL)
#
# In this section you can install any package that can not be install
# with APT Package Manager and that need to be made manually.
# For example:
#   - Packages from source, such as OnnxRuntime, CMake
#   - RidgeRun Tools such as GSTCuda
#########################################################################
# Set the working directory
WORKDIR /workspace

# Build CMake from source
RUN wget https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.sh \
    && chmod +x cmake-${CMAKE_VERSION}-linux-x86_64.sh \
    && ./cmake-${CMAKE_VERSION}-linux-x86_64.sh --skip-license --exclude-subdir --prefix=/usr/local\
    && rm -rf cmake-${CMAKE_VERSION}*

RUN git clone --recursive --branch v${ORT_VERSION} https://github.com/microsoft/onnxruntime \
    && cd onnxruntime \
    && ./build.sh --config Release --update --build --build_wheel --build_shared_lib --skip_tests --allow_running_as_root --parallel 3 \
    && cd build/Linux/Release \
    && make install \
    && cp /usr/local/lib/libonnxruntime.so.${ORT_VERSION} /usr/lib/

########################################################################
# INSTALLING YOUR APPLICATION
#
# In this section you can install your application, for this you need to
# clone your app repo on the correct branch if needed. This can be achive
# by the arguments for your docker build.
#
# NOTE: Your app needs the wrappers with PYBIND11 and follow the structure
# define on the template.
#########################################################################
WORKDIR /workspace/app

# Cloning Repo for your application
RUN git clone -b <branch> https://${USERNAME_YOUR_REPO}:${ACCESS_TOKEN_YOUR_REPO}@<repo>.git

# Build Face Redaction Lib
WORKDIR /workspace/app/librrobjectredaction

RUN meson build --optimization 3 --prefix /usr -Dwerror=false -Ddocs=disabled -Ddeveloper-mode=false \
    -Denable-tests=disabled -Dgst=disabled -Dnvidia=disabled -Dpython=enabled \
    && ninja -C build install

########################################################################
# INSTALLING GRADIO PLATFORM
#
# In this section you can install the interface modified for your own
# application.
#########################################################################
# Cloning Repo for GUI
RUN git clone -b ${BRANCH} https://${USERNAME}:${ACCESS_TOKEN}@github.com/ridgerun-ai/web-model-server.git

WORKDIR /workspace/app/web-model-server

RUN pip3 install -r requirements.txt \
    && pip3 install -e . \
    && chmod +x ./bin/run_gui

########################################################################
# RUNNING SERVICE
#
# In this section you will run the gradio app.
#########################################################################
CMD ["./bin/run_gui"]
