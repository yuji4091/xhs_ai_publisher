"""
AI辅助内容生成器 - 减少内容创作时间
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from datetime import datetime
import logging

from src.core.logger import logger


@dataclass
class ContentTemplate:
    """内容模板"""
    id: str
    name: str
    category: str
    title_template: str
    content_template: str
    tags: List[str]
    image_suggestions: List[str]


@dataclass
class GeneratedContent:
    """生成的内容"""
    title: str
    content: str
    tags: List[str]
    image_keywords: List[str]
    category: str
    created_at: datetime


class AIContentGenerator:
    """AI内容生成器"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("未设置OpenAI API Key，AI内容生成功能将受限")

        # 预定义模板
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, ContentTemplate]:
        """加载内容模板"""
        templates = {}

        # 小红书风格模板
        templates['lifestyle'] = ContentTemplate(
            id='lifestyle',
            name='生活方式',
            category='生活',
            title_template='「{emotion}」{topic}，{benefit}！',
            content_template='''
🌟 {topic}分享

大家好！今天想和大家分享关于{topic}的心得体会。

{detail_description}

💡 我的经验总结：
{key_points}

📸 实拍分享：
{image_description}

# {hashtags}
            ''',
            tags=['生活', '分享', '经验', '日常'],
            image_suggestions=['自然光', '生活化', '真实场景']
        )

        templates['beauty'] = ContentTemplate(
            id='beauty',
            name='美妆分享',
            category='美妆',
            title_template='{product}真的{benefit}！{rating}分推荐',
            content_template='''
✨ {product}测评分享

姐妹们！今天给大家带来{product}的详细测评！

📦 包装设计：
{packaging_desc}

💄 使用体验：
{usage_experience}

👍 优点：
{pros}

👎 缺点：
{cons}

💰 价格参考：{price_range}

# {hashtags}
            ''',
            tags=['美妆', '测评', '推荐', '护肤'],
            image_suggestions=['产品特写', '使用场景', '对比图']
        )

        templates['food'] = ContentTemplate(
            id='food',
            name='美食分享',
            category='美食',
            title_template='{dish}做法分享，{benefit}！',
            content_template='''
🍽️ {dish}家常做法

今天分享一款{dish}的简单做法，超级{difficulty}！

🛒 食材准备：
{ingredients}

📝 制作步骤：
{steps}

💡 小贴士：
{tips}

口感：{taste_desc}

# {hashtags}
            ''',
            tags=['美食', '烹饪', '家常菜', '教程'],
            image_suggestions=['成品图', '步骤图', '食材图']
        )

        return templates

    async def generate_content_batch(self, topic: str, count: int = 5,
                                   template_id: str = 'lifestyle') -> List[GeneratedContent]:
        """批量生成内容"""
        if not self.api_key:
            return self._generate_mock_content(topic, count, template_id)

        template = self.templates.get(template_id, self.templates['lifestyle'])
        contents = []

        for i in range(count):
            try:
                content = await self._generate_single_content(topic, template, i)
                contents.append(content)

                # 添加延迟避免API限制
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"生成第{i+1}篇内容失败: {e}")
                continue

        return contents

    async def _generate_single_content(self, topic: str, template: ContentTemplate,
                                     index: int) -> GeneratedContent:
        """生成单篇内容"""
        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)

            # 生成标题
            title_prompt = f"""
基于主题"{topic}"，使用模板风格"{template.title_template}"生成一个吸引人的标题。
要求：标题简洁有力，包含数字或emoji，适合小红书风格。
"""

            title_response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": title_prompt}],
                max_tokens=50,
                temperature=0.8
            )
            title = title_response.choices[0].message.content.strip()

            # 生成内容
            content_prompt = f"""
请基于主题"{topic}"，按照以下模板生成小红书风格的内容：

模板：
{template.content_template}

要求：
1. 内容真实有用，包含个人体验
2. 使用emoji增加可读性
3. 结尾包含相关话题标签
4. 字数控制在800-1200字
5. 语言亲切自然，像朋友在分享
"""

            content_response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": content_prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            content = content_response.choices[0].message.content.strip()

            # 生成标签
            tags = template.tags.copy()
            # 添加主题相关标签
            if topic not in tags:
                tags.insert(0, topic)

            # 生成图片关键词
            image_keywords = template.image_suggestions.copy()
            image_keywords.extend([topic, "小红书", "分享"])

            return GeneratedContent(
                title=title,
                content=content,
                tags=tags,
                image_keywords=image_keywords,
                category=template.category,
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"AI生成内容失败: {e}")
            raise

    def _generate_mock_content(self, topic: str, count: int, template_id: str) -> List[GeneratedContent]:
        """生成模拟内容（当API不可用时）"""
        template = self.templates.get(template_id, self.templates['lifestyle'])
        contents = []

        for i in range(count):
            contents.append(GeneratedContent(
                title=f"关于{topic}的分享{i+1}",
                content=f"这是关于{topic}的模拟内容{i+1}。\n\n{template.content_template}",
                tags=template.tags,
                image_keywords=template.image_suggestions,
                category=template.category,
                created_at=datetime.now()
            ))

        return contents

    def get_available_templates(self) -> Dict[str, str]:
        """获取可用模板"""
        return {tid: template.name for tid, template in self.templates.items()}

    async def optimize_content(self, content: str) -> str:
        """优化现有内容"""
        if not self.api_key:
            return content

        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)

            optimize_prompt = f"""
请优化以下小红书内容，使其更符合平台风格：

{content}

优化要求：
1. 增加emoji使用
2. 调整语言更亲切自然
3. 优化段落结构
4. 确保包含话题标签
5. 保持原有信息完整性
"""

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": optimize_prompt}],
                max_tokens=2000,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"内容优化失败: {e}")
            return content


# 全局实例
content_generator = AIContentGenerator()


# 使用示例
async def demo():
    """演示函数"""
    print("开始AI内容生成演示...")

    # 生成生活方式内容
    contents = await content_generator.generate_content_batch(
        topic="居家办公",
        count=3,
        template_id='lifestyle'
    )

    for i, content in enumerate(contents, 1):
        print(f"\n=== 生成内容 {i} ===")
        print(f"标题: {content.title}")
        print(f"标签: {', '.join(content.tags)}")
        print(f"内容预览: {content.content[:200]}...")
        print(f"图片关键词: {', '.join(content.image_keywords)}")

    # 优化现有内容
    sample_content = "今天分享一下我的居家办公经验。希望对大家有帮助。"
    optimized = await content_generator.optimize_content(sample_content)
    print(f"\n优化前: {sample_content}")
    print(f"优化后: {optimized}")


if __name__ == "__main__":
    asyncio.run(demo())