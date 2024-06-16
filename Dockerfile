# Base CUDA image
FROM cnstark/pytorch:2.0.1-py3.9.17-cuda11.8.0-ubuntu20.04

LABEL maintainer="breakstring@hotmail.com"
LABEL version="dev-20240209"
LABEL description="Docker image for GPT-SoVITS-Inference"


# Install 3rd party apps
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends tzdata ffmpeg libsox-dev parallel aria2 git git-lfs && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt initially to leverage Docker cache
WORKDIR /workspace
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# Define a build-time argument for image type
ARG IMAGE_TYPE=full

# Conditional logic based on the IMAGE_TYPE argument
# Always copy the Docker directory, but only use it if IMAGE_TYPE is not "elite"
COPY ./Docker /workspace/Docker 
# elite 类型的镜像里面不包含额外的模型

#如果能直接从官方（翻墙）下载，则打开如下的注释，否则参考ReadMe.md中的说明自行将模型文件放到对应的文件夹中
#RUN if [ "$IMAGE_TYPE" != "elite" ]; then \
#        chmod +x /workspace/Docker/download.sh && \
#        /workspace/Docker/download.sh && \
#        python /workspace/Docker/download.py && \
#        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple nltk && \
#        python -m nltk.downloader averaged_perceptron_tagger cmudict; \
#    fi



# Copy the rest of the application
COPY . /workspace

#EXPOSE 9871 9872 9873 9874 9880
EXPOSE 5000


CMD ["python", "app.py"]
