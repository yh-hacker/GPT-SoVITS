# 在开头加入路径
import os, sys

# 尝试清空含有GPT_SoVITS的路径
for path in sys.path:
    if path.find(r"GPT_SoVITS") != -1:
        sys.path.remove(path)

now_dir = os.getcwd()
sys.path.append(now_dir)
# sys.path.append(os.path.join(now_dir, "GPT_SoVITS"))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Inference.src.config_manager import __version__ as backend_version
print(f"Backend version: {backend_version}")

import soundfile as sf
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import uvicorn  
import io
import urllib.parse
import tempfile
import hashlib, json

# 将当前文件所在的目录添加到 sys.path


# 从配置文件读取配置
from Inference.src.config_manager import Inference_Config, params_config
from Inference.src.TTS_Instance import TTS_Task
inference_config = Inference_Config()

workers = inference_config.workers
tts_host = inference_config.tts_host
tts_port = inference_config.tts_port
default_batch_size = inference_config.default_batch_size
default_word_count = inference_config.default_word_count
enable_auth = inference_config.enable_auth
is_classic = inference_config.is_classic
models_path = inference_config.models_path
disabled_features = inference_config.disabled_features
if enable_auth:
    users = inference_config.users

try:
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS
except ImportError:
    is_classic = True
    pass

if not is_classic:
    from Inference.src.TTS_Instance import TTS_instance
    from Inference.src.config_manager import update_character_info,  get_deflaut_character_name
    tts_instance = TTS_instance() 
else:
    from Inference.src.classic_inference.classic_load_infer_info import load_character, character_name, get_wav_from_text_api,  update_character_info
    pass

# 存储临时文件的字典
temp_files = {}

app = FastAPI()

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/character_list')
async def character_list():
    res = JSONResponse(update_character_info()['characters_and_emotions'])
    return res

@app.get('/voice/speakers')
async def speakers():
    speaker_dict = update_character_info()['characters_and_emotions']
    name_list = list(speaker_dict.keys())
    speaker_list = [{"id": i, "name": name_list[i], "lang":["zh","en","ja"]} for i in range(len(name_list))]
    res = {
        "VITS": speaker_list,
        "GSVI": speaker_list,
        "GPT-SOVITS": speaker_list
    }
    return JSONResponse(res)     

# route 由 json 文件配置
async def tts(request: Request):
    # 尝试从JSON中获取数据，如果不是JSON，则从查询参数中获取
    if request.method == "GET":
        data = request.query_params
    else:
        data = await request.json()

    task = TTS_Task()
    task.load_from_dict(data)
    print(task.to_dict())
    
    if task.text == "":
        return HTTPException(status_code=400, detail="Text is empty")
    
    params = task.to_dict()
    character = task.character
    format = task.format
    save_temp = task.save_temp
    request_hash = None if not save_temp else task.md5()
    stream = task.stream
    
    
    if not is_classic:
        tts_instance.load_character(character)
        gen = tts_instance.get_wav_from_text_api(**params)
    else:
        global character_name
        if character is not None and character != character_name and os.path.exists(os.path.join(models_path, task.character)):
            character_name = character
            load_character(character_name)
        gen = get_wav_from_text_api(**params)


    if stream == False:
        if save_temp and request_hash in temp_files:
            return FileResponse(path=temp_files[request_hash], media_type=f'audio/{format}')
        else:
            # 假设 gen 是你的音频生成器
            try:
                sampling_rate, audio_data = next(gen)
            except StopIteration:
                raise HTTPException(status_code=404, detail="Generator is empty or error occurred")
            # 创建一个临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as tmp_file:
                # 尝试写入用户指定的格式，如果失败则回退到 WAV 格式
                try:
                    sf.write(tmp_file, audio_data, sampling_rate, format=format)
                except Exception as e:
                    # 如果指定的格式无法写入，则回退到 WAV 格式
                    sf.write(tmp_file, audio_data, sampling_rate, format='wav')
                    format = 'wav'  # 更新格式为 wav
                
                tmp_file_path = tmp_file.name
                task.audio_path = tmp_file_path
                if save_temp:
                    temp_files[request_hash] = tmp_file_path
            # 返回文件响应，FileResponse 会负责将文件发送给客户端
            return FileResponse(tmp_file_path, media_type=f"audio/{format}", filename=f"audio.{format}")
    else:
        return StreamingResponse(gen,  media_type='audio/wav')

routes = ['/tts']
try:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "params_config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)
        routes = config.get("route", {}).get("alias", ['/tts'])
except:
    pass

# 注册路由
for path in routes:
    app.api_route(path, methods=['GET', 'POST'])(tts)

# 便于小白理解
def print_ipv4_ip(host = "127.0.0.1", port = 5000):
    import socket

    def get_internal_ip():
        """获取内部IP地址"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 这不会发送真正的数据包
            s.connect(('10.253.156.219', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    if host == "0.0.0.0":
        display_hostname = get_internal_ip()
        if display_hostname != "127.0.0.1":
            print(f"Please use http://{display_hostname}:{port} to access the service.")

if __name__ == "__main__":
    print_ipv4_ip(tts_host, tts_port)
    uvicorn.run(app, host=tts_host, port=tts_port)

