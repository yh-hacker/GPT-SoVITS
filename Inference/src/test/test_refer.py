import sys
sys.path.append(".")

from Inference.src.Adapter.GPT_soVITS_Adapter import GSV_Instance 
from Inference.src.TTS_Task import TTS_Task

gsv_instance = GSV_Instance()
task = TTS_Task()

task.text = "你好，我是一个测试文本。"

gen = gsv_instance.generate_from_text(task)
sr, audio = next(gen)

import tempfile
import soundfile as sf
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    sf.write(f.name, audio, sr)
    print(f"Audio saved to {f.name}")