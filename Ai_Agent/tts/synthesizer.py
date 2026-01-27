"""文本转语音模块 - 使用 edge-tts"""
import asyncio
import edge_tts
import uuid
import os
from typing import Optional


class TTSSynthesizer:
    def __init__(self, output_dir: str = "audio_output"):
        """初始化 TTS 合成器
        Args:
            output_dir: 音频文件输出目录
        """
        self.output_dir = output_dir
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 默认语音配置
        self.default_voice = "zh-CN-XiaoxiaoNeural"  # 中文女性声音
        self.default_rate = "+0%"  # 语速
        self.default_volume = "+0%"  # 音量
    
    async def synthesize_async(self, text: str, voice: str = None, rate: str = None, volume: str = None) -> str:
        """异步合成语音
        Args:
            text: 要合成的文本
            voice: 语音类型，默认为 zh-CN-XiaoxiaoNeural
            rate: 语速，默认为 +0%
            volume: 音量，默认为 +0%
        Returns:
            音频文件路径
        """
        if not text.strip():
            raise ValueError("文本不能为空")
        
        # 使用默认配置或传入的配置
        voice = voice or self.default_voice
        rate = rate or self.default_rate
        volume = volume or self.default_volume
        
        # 生成唯一的文件名
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 使用 edge-tts 合成语音
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
            
            return filepath
        except Exception as e:
            raise Exception(f"TTS 合成失败: {str(e)}")
    
    def synthesize(self, text: str, voice: str = None, rate: str = None, volume: str = None) -> str:
        """同步合成语音
        Args:
            text: 要合成的文本
            voice: 语音类型，默认为 zh-CN-XiaoxiaoNeural
            rate: 语速，默认为 +0%
            volume: 音量，默认为 +0%
        Returns:
            音频文件路径
        """
        return asyncio.run(self.synthesize_async(text, voice, rate, volume))
    
    def synthesize_with_cache(self, text: str, voice: str = None, rate: str = None, volume: str = None) -> str:
        """带缓存的语音合成（相同文本不会重复生成）
        Args:
            text: 要合成的文本
            voice: 语音类型
            rate: 语速
            volume: 音量
        Returns:
            音频文件路径
        """
        # 为了简化，这里仍然每次都生成新文件
        # 实际应用中可以根据文本内容生成哈希作为缓存键
        return self.synthesize(text, voice, rate, volume)


# 全局实例
tts_synthesizer = TTSSynthesizer()