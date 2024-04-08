import os, json
from typing import List 
from uuid import uuid4



from uuid import uuid4



import xml.etree.ElementTree as ET
from Inference.src.TTS_Instance import TTS_instance


"""
以下列表描述了每个元素中允许的一些内容示例：

audio：如果音频文件不可用或不可播放，可在 audio 元素的正文中包含可讲述的纯文本或 SSML 标记。 audio 元素还包含文本和以下元素：audio、break、p、s、phoneme、prosody、say-as 和 sub。
bookmark：此元素不能包含文本或任何其他元素。
break：此元素不能包含文本或任何其他元素。
emphasis：此元素可包含文本和以下元素：audio、break、emphasis、lang、phoneme、prosody、say-as 和 sub。
lang：此元素可包含除 mstts:backgroundaudio、voice 和 speak 以外的所有其他元素。
lexicon：此元素不能包含文本或任何其他元素。
math：此元素只能包含文本和 MathML 元素。
mstts:audioduration：此元素不能包含文本或任何其他元素。
mstts:backgroundaudio：此元素不能包含文本或任何其他元素。
mstts:embedding：此元素可包含文本和以下元素：audio、break、emphasis、lang、phoneme、prosody、say-as 和 sub。
mstts:express-as：此元素可包含文本和以下元素：audio、break、emphasis、lang、phoneme、prosody、say-as 和 sub。
mstts:silence：此元素不能包含文本或任何其他元素。
mstts:viseme：此元素不能包含文本或任何其他元素。
p：此元素可包含文本和以下元素：audio、break、phoneme、prosody、say-as、sub、mstts:express-as 和 s。
phoneme：此元素只能包含文本，不能包含任何其他元素。
prosody：此元素可包含文本和以下元素：audio、break、p、phoneme、prosody、say-as、sub 和 s。
s：此元素可包含文本和以下元素：audio、break、phoneme、prosody、say-as、mstts:express-as 和 sub。
say-as：此元素只能包含文本，不能包含任何其他元素。
sub：此元素只能包含文本，不能包含任何其他元素。
speak：SSML 文档的根元素。 此元素可包含以下元素：mstts:backgroundaudio 和 voice。
voice：此元素可包含除 mstts:backgroundaudio 和 speak 以外的所有其他元素。
"""

class SSML_Dealer:
    def __init__(self):
        self.ssml: str = ""
        self.task_queue : set = set()
        self.root : ET.Element = None
        self.tts_instance : TTS_instance = None
                    
    def analyze_element(self, root: ET.Element, father_task:TTS_Task):
        task = TTS_Task(father_task)
        root.set("uuid", task.uuid)
        
        if root.tag == "voice":
            task.character = root.get("name")
            if root.get("emotion") is not None:
                task.emotion = root.get("emotion")
            if root.get("style") is not None:
                task.emotion = root.get("style")
            
        
        for child in root:
            self.analyze_element(child, father_task)
        
    
    
        
    
    def read_ssml(self, ssml:str):
        self.ssml = ssml
        try:
            self.root = ET.fromstring(ssml)
        except Exception as e:
            raise ValueError("Invalid SSML.")
        
            
