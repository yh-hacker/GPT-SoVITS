#!/bin/bash
conda install -c conda-forge gcc -y
conda install -c conda-forge gxx -y
conda install ffmpeg cmake -y
conda install pytorch==2.1.1 torchvision==0.16.1 torchaudio==2.1.1 pytorch-cuda=11.8 -c pytorch -c nvidia -y
pip install -r requirements.txt



