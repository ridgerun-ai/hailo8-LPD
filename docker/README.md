# Gradio Interface Product Evaluation

## Description

On this README you will find a Dockerfile template and a Dockerfile_example to create a container for a GUI service. Also you can follow the step-by-step of how to run your own application on a container.

## Folder Structure
```bash
├── Dockerfile
├── Dockerfile_example
└── README.md
```

## Setup

### Check Credentials

To build the container, you need to have the following credentials:

- **username**: An user with access to the repo you need to clone.
- **access_token**: An access token to the repo you need to clone.
    - Info Github: [Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
    - Info Gitlab: [How to create a personal access token in GitLab (5 steps)](https://www.merge.dev/blog/gitlab-access-token)

### Install Docker Engine

If your system does not have docker engine install, you can take a look to this blog: [Docker Tutorial](https://developer.ridgerun.com/wiki/index.php/Docker_Tutorial)

## Run Example Container

This example runs a docker container with a GUI that will be deploy on http://localhost:7860/, this will apply some transformation and watermark to the images or videos uploaded.

### Build Docker Image

```bash
docker build -f ./Dockerfile_example -t <image name> . --build-arg USERNAME=<your username> --build-arg ACCESS_TOKEN=<your access token> --build-arg BRANCH=<your branch>
```

For example the following command will create an image called gui_platform with the web-model-server in develop branch.

```bash
docker build -f ./Dockerfile_example -t gui_platform . --build-arg USERNAME=<your username> --build-arg ACCESS_TOKEN=<your access token> --build-arg BRANCH=develop
```

To check the image build:

```bash
docker images
```

Look for your image with the tag that you give it, the output should be something like this:

```bash
REPOSITORY                                   TAG                          IMAGE ID       CREATED             SIZE
gui_platform                                 latest                       e50a89abecd2   About an hour ago   1.54GB
```

### Run Container

```bash
docker run -it -p 7860:7860 --name <container name> <image name>
```

Continuing with the example, the following command will create a container named platform_test from the previously created image gui_platform.

```bash
docker run -it -p 7860:7860 --name platform_test gui_platform
```

To check the container you can look the containers running or going to http://localhost:7860/:

```bash
docker ps
```

Output should looks similar to:

```bash
CONTAINER ID   IMAGE          COMMAND                  CREATED       STATUS          PORTS           NAMES
4dd281958557   gui_platform   "./bin/run_gui"          1 day ago     Up 10 seconds   7860/tcp        platform_test
```

### Access Container

Once the container is running you can access it with the following command:

```bash
docker exec -it <container name> bash
```

Finishing the example

```bash
docker exec -t platform_test bash
```

## Instructions To Build Your Own Container

### Dockerfile

#### Description

The **Dockerfile** is a template, so you must modify this file for your requirements, change the placeholders with the format `<YOUR VALUE>` with your own values, for example `EXPOSE <YOUR PORT APP>` -> `EXPOSE 8080`. The next sections will guide you on how to modify this file.

#### Select The Base Image

Depending of your needs, you can select different base image, some examples are shown below:

 - **Ubuntu base:** ubuntu:18.04, ubuntu:20.04, ubuntu:22.04, etc.
 - **Ubuntu cuda base:** nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04, etc.

> **_NOTE:_**  For reproducibility we recommend always to used version instead of latest tag.


```bash
FROM ubuntu:20.04
```

<details close>
<summary>Issues running nvidia container?</summary>

If you failed on running gpu container, with the next error:
```bash
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]. 3
```
You need to install nvidia toolkit dependencies:
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey |sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
&& curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
&& sudo apt-get update
```
</details>

#### Expose Ports

Base on your application or micro-services, you have to expose ports that will communicate outside the docker. No need for internal communications.

```bash
EXPOSE 7860
```

#### Define Enviroment Variables - Optional

Create all the env variables need to create your container, could be dependencies versions, install variables needs, app IP_Host, etc. This is optional depending of your aplications needs.

```bash
ENV CMAKE_VERSION=3.27.1
ENV GRADIO_SERVER_NAME="0.0.0.0"
```

> **_WARNING:_**  Never use credentials on your enviroment variables.

#### Define Arguments

Define the arguments that you need to give to your container on builder time, depending of your application more args would be needed. Tipical use on API tokens, passwords or credentials.

```bash
ARG USERNAME
ARG ACCESS_TOKEN
...
```
#### Install Your Dependencies

Install all the dependencies for your application, the way you installe depends of your OS base, for debian base will be with apt. For install dependencies that needs interaction use DEBIAN_FRONTEND noninteractive.

```bash
# Install Dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    build-essential \
    vim \
    <your dependencies> ...\
    && rm -rf /var/lib/apt/lists/*
```

> **_NOTE:_**  If no needed dependecies build files, cleaned with ```rm -rf /var/lib/apt/lists/*```.

> **_WARNING:_**  Remember always to put the version needed for your depedencies, if not this could create problems on your application version compatibility.

#### Cloning Repos Into The Container

To clone private repositories, your need your credentials o access token, depending on this the command will change a little bit.

```bash
WORKDIR /workspace

RUN git clone -b <branch> https://${USERNAME}:${ACCESS_TOKEN}@gitlab.<repo>.git
```

#### Custom Installations Or Configurations

Some applications would need a specific way to build, on this cases you can run it by bash commands.

```bash
# Set the working directory
WORKDIR /workspace

# Build CMake from source
RUN wget https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.sh \
    && chmod +x cmake-${CMAKE_VERSION}-linux-x86_64.sh \
    && ./cmake-${CMAKE_VERSION}-linux-x86_64.sh --skip-license --exclude-subdir --prefix=/usr/local\
    && rm -rf cmake-${CMAKE_VERSION}*
```

<details close>
<summary>Another example</summary>

```bash
# Set the working directory
WORKDIR /workspace
# Clone the ONNX Runtime repository
RUN git clone --recursive --branch v${ORT_VERSION} https://github.com/microsoft/onnxruntime

# Set the working directory to the ONNX Runtime source directory
WORKDIR /workspace/onnxruntime

# Build ONNX Runtime with CPU support
RUN ./build.sh --config Release --update --build --build_wheel --build_shared_lib --skip_tests --allow_running_as_root --parallel 3 \
    && cd build/Linux/Release \
    && make install \
    && cp /usr/local/lib/libonnxruntime.so.${ORT_VERSION} /usr/lib/
```
</details>

> **_NOTE:_**  Remember always work in the right directory you can achive this by ```WORKDIR <dir>/``` or moving by bash commands ```cd <dir>/```.

#### Install Your Applications

Once you have all the setup, you can install your application.

```bash
RUN pip3 install -r requirements.txt \
    && pip3 install -e . \
    && chmod +x ./bin/run_gui
```

#### Run Your Application

Finally, once your enviroment has been configured and working with all the dependencies needed. You can run your gradio interface.

```bash
# Run gui
CMD ["./bin/run_gui"]
```

### Build The Docker Image

```bash
docker build \
--build-arg USERNAME=<username> \
--build-arg ACCESS_TOKEN=<access_token> \
...
-t <image tag> .
```
### Run The Docker Container

This need to be run with the proper configuration for your application:

 - Ports Mapping
 - GPUs enable
 - Memory Limit
 - CPUs Cores

More info can be found [Docker Memory and CPU limit](https://phoenixnap.com/kb/docker-memory-and-cpu-limit).

```bash
docker run -d -p <host>:<container> <image tag> --name <container name>
```
> **_NOTE:_**  Some flags are really useful such as ```-d``` for detaching the console, more info [Docker Run documentation](https://docs.docker.com/engine/reference/run/).
