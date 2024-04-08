import os, json
from typing import List , Dict
from uuid import uuid4

import sys
sys.path.append(".")

import xml.etree.ElementTree as ET
from Inference.src.TTS_Instance import TTS_instance, TTS_Task

import tempfile
import soundfile as sf

import numpy as np
import requests, librosa


special_dict_speed = {
    "x-slow": 0.5,
    "slow": 0.75,
    "medium": 1.0,
    "fast": 1.25,
    "x-fast": 1.5,
    "default": 1.0
}


def load_time(time:str) -> float:
    if time.endswith("ms"):
        return float(time[:-2]) / 1000
    if time.endswith("s"):
        return float(time[:-1])
    if time.endswith("min"):
        return float(time[:-3]) * 60
    return float(time)

class SSML_Dealer:
    def __init__(self):
        self.ssml: str = ""
        self.task_list: Dict[str, TTS_Task] = {}
        self.task_queue : List[str] = []
        self.audio_download_queue : List[Dict] = []
        self.root : ET.Element = None
        self.tts_instance : TTS_instance = None
                    
    def analyze_element(self, root: ET.Element, father_task:TTS_Task):
        task = TTS_Task(father_task)
        self.task_list[task.uuid] = task
        root.set("uuid", task.uuid)
        root.tag = root.tag.split('}')[-1].lower()
        task.text = root.text.strip() if root.text is not None else ""
        print(f"--------{root.tag} : {task.text}") # debug
        if root.tag in ["audio", "mstts:backgroundaudio"]:
            if root.get("src") is not None:
                self.audio_download_queue.append({"uuid": task.uuid, "src": root.get("src")})
            task.text = ""
        else:
            if root.tag in ["bookmark", "break", "mstts:silence", "mstts:viseme"]:
                task.text = ""
                
            task.update_from_param('text_language', root)
            task.update_from_param('character', root)
            task.update_from_param('emotion', root)
            task.update_from_param('speed', root, special_dict=special_dict_speed)
            task.update_from_param('top_k', root)
            task.update_from_param('top_p', root)
            
            task.update_from_param('temperature', root)
            task.update_from_param('batch_size', root)
            
            # task.update_from_param('loudness', root) # need to recheck
            # task.update_from_param('pitch', root)
            
                
            task.stream = False
            if task.text.strip() != "":
                self.task_queue.append(task.uuid)
        
        for child in root:
            self.analyze_element(child, father_task)
        
    
    def generate_audio_from_element(self, root: ET.Element, default_silence: float = 0.3) -> np.ndarray:
        # 认定所有的音频文件都已经生成
        audio_data = np.array([])
        uuid = root.get("uuid")
        task = self.task_list[uuid]
        sr = 32000
        # print(f"--------{root.tag}") # debug
        if root.tag in ["break", "mstts:silence"]:
            # print(f"--------break: {root.get('time')}") # debug
            duration = load_time(root.get("time"))
            audio_data = np.zeros(int(duration * sr))
        elif task.audio_path not in ["", None]:
            audio_data, sr = sf.read(task.audio_path)
        
        for child in root:
            audio_data = np.concatenate([audio_data, self.generate_audio_from_element(child)])
        
        if default_silence > 0:
            audio_data = np.concatenate([audio_data, np.zeros(int(default_silence * sr))])
        
        return audio_data
    
    def read_ssml(self, ssml:str):
        self.ssml = ssml
        try:
            self.root = ET.fromstring(ssml)
            self.analyze_element(self.root, None)
        except Exception as e:
            raise ValueError("Invalid SSML.")
        
    def generate_tasks(self, tts_instance:TTS_instance, tmp_dir:str):
        # 先按照人物排序
        self.task_queue.sort(key=lambda x: self.task_list[x].character)
        for uuid in self.task_queue:
            task = self.task_list[uuid]
            if task.text.strip() == "":
                continue
            gen = tts_instance.get_wav_from_task(task)
            sr, audio_data = next(gen)
            
            tmp_file = os.path.join(tmp_dir, f"{task.uuid}.wav")
            
            sf.write(tmp_file, audio_data, sr, format='wav')
            task.audio_path = tmp_file

    def download_audio(self, tmp_dir:str, sample_rate:int=32000):
        for audio in self.audio_download_queue:
            # 另开一个线程下载音频
            response = requests.get(audio["src"])
            # 重采样
            audio_format = audio["src"].split(".")[-1]
            tmp_file = os.path.join(tmp_dir, f"{uuid4()}.{audio_format}")
            with open(tmp_file, 'wb') as f:
                f.write(response.content)
            audio_data, sr = librosa.load(tmp_file, sr=sample_rate)
            sf.write(tmp_file, audio_data, sr, format='wav')
            self.task_list[audio["uuid"]].audio_path = tmp_file
    
    def generate_from_ssml(self, ssml:str, tts_instance:TTS_instance, format:str="wav"):
        self.read_ssml(ssml)
        tmp_dir = tempfile.mkdtemp()
        self.generate_tasks(tts_instance, tmp_dir)
        self.download_audio(tmp_dir)
        audio_data = self.generate_audio_from_element(self.root)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp_file:
            sf.write(tmp_file, audio_data, 32000, format=format)
            return tmp_file.name

if __name__ == "__main__":
    ssml = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
    大可以尝试一下
    <voice name="夏青">
        大可以尝试一下
    </voice>
    <voice >
        大可以尝试一下
    </voice>
</speak>
"""
    ssml_dealer = SSML_Dealer()
    tts_instance = TTS_instance()
    print(ssml_dealer.generate_from_ssml(ssml, tts_instance))
    
    for task in ssml_dealer.task_list.values():
        print(task)