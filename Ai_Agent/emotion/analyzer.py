"""情绪分析模块 - 分析用户输入的情绪并生成相应回复"""
from typing import Dict, List, Tuple
import re


class EmotionAnalyzer:
    def __init__(self):
        """初始化情绪分析器"""
        self.emotion_keywords = {
            "开心": ["开心", "快乐", "高兴", "愉快", "兴奋", "喜悦", "幸福", "满意", "棒", "好", "赞", "awesome", "great", "good", "happy", "joy"],
            "难过": ["难过", "伤心", "悲伤", "沮丧", "失落", "痛苦", "失望", "sad", "unhappy", "depressed", "sorrow"],
            "生气": ["生气", "愤怒", "恼火", "气愤", "rage", "angry", "mad", "annoyed", "furious"],
            "焦虑": ["焦虑", "紧张", "担心", "害怕", "恐惧", "忧虑", "stress", "anxious", "worried", "scared", "nervous"],
            "平静": ["平静", "淡定", "冷静", "平和", "安宁", "peaceful", "calm", "relaxed", "serene"],
            "困惑": ["困惑", "疑惑", "疑问", "不懂", "不明白", "what", "huh", "confused", "puzzle", "unclear"]
        }
        
        # 情绪回应模板
        self.emotion_responses = {
            "开心": [
                "看到你这么开心，我也感到很高兴！😊",
                "你的快乐感染了我！继续保持这种积极的心态吧！🌟",
                "很高兴能让你开心，有什么我可以继续帮助你的吗？😄"
            ],
            "难过": [
                "听到你不开心，我也有些难过。需要聊聊吗？😔",
                "抱抱~ 生活中总有起伏，一切都会好起来的。💪",
                "我在这里陪着你，有什么想说的都可以告诉我。🤗"
            ],
            "生气": [
                "我能感受到你的愤怒，要不要先深呼吸放松一下？😌",
                "看起来你现在很生气，能告诉我发生了什么吗？🤔",
                "情绪激动时，先静一静可能会有所帮助哦。🧘‍♀️"
            ],
            "焦虑": [
                "我能理解你的担忧，让我们一步步来解决问题吧。🤝",
                "不要太过担心，大部分焦虑都是我们想象出来的。😌",
                "深呼吸，慢慢来，我会尽力帮助你。💖"
            ],
            "平静": [
                "感觉你现在心情很平静呢，这种状态很棒！😌",
                "宁静致远，有时候平静的心能带来更好的思路。🧘",
                "享受这份宁静吧，有什么想法可以慢慢告诉我。🍃"
            ],
            "困惑": [
                "不用担心，每个人都会有困惑的时候。让我来帮你解答吧！💡",
                "有什么不清楚的地方吗？我很乐意为你解释。📚",
                "困惑是学习的开始，我们一起探索答案吧！🔍"
            ]
        }
    
    def detect_emotion(self, text: str) -> Tuple[str, float]:
        """检测文本中的情绪
        Returns:
            tuple: (情绪类型, 置信度分数)
        """
        text_lower = text.lower()
        emotion_scores = {}
        
        # 计算每种情绪的得分
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                # 使用正则表达式进行词匹配，避免部分匹配
                matches = re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower)
                score += len(matches)
                
                # 检查关键词是否在感叹句中（增加权重）
                if f"{keyword}!" in text_lower or f"{keyword}！" in text:
                    score += 1
            
            emotion_scores[emotion] = score
        
        # 找到最高分的情绪
        if sum(emotion_scores.values()) == 0:
            return "平静", 0.0
        
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[dominant_emotion]
        total_score = sum(emotion_scores.values())
        
        # 计算置信度（基于最高分占总分的比例）
        confidence = max_score / total_score if total_score > 0 else 0.0
        
        return dominant_emotion, confidence
    
    def get_emotion_response(self, emotion: str) -> str:
        """根据情绪类型获取相应的回应"""
        import random
        if emotion in self.emotion_responses:
            return random.choice(self.emotion_responses[emotion])
        else:
            return "我能感受到你的情绪，有什么我可以帮助你的吗？😊"
    
    def analyze_and_respond(self, text: str) -> Dict[str, any]:
        """分析情绪并返回分析结果和建议回应"""
        emotion, confidence = self.detect_emotion(text)
        
        result = {
            "detected_emotion": emotion,
            "confidence": confidence,
            "emotion_response": self.get_emotion_response(emotion),
            "should_adjust_tone": confidence > 0.3  # 如果置信度大于0.3，则建议调整语气
        }
        
        return result


# 全局实例
emotion_analyzer = EmotionAnalyzer()