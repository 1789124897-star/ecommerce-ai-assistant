STRATEGY_TYPES = {
    "A": "痛点解决型",
    "B": "效率功能型",
    "C": "情绪品质型",
}


def build_analysis_prompt(name: str, function: str, price: str, extra: str) -> str:
    return f"""
你是一名资深电商产品分析师，请结合商品图片和商品文本信息完成一份结构化分析报告。

商品信息：
- 商品名称：{name}
- 核心功能：{function}
- 价格信息：{price}
- 补充说明：{extra or "无"}

请严格按下面结构输出：
1. 核心用户画像（3类）
2. 典型购买场景（3个）
3. 核心痛点（5个）
4. 核心卖点（5个，强调用户价值，并标注来源是视觉、功能还是价格）
5. 推荐营销方向（3个）

要求：
- 输出必须使用简体中文
- 结合图片中的材质、颜色、造型、质感、使用场景进行判断
- 语言要适合电商运营、商品策划和营销团队直接使用
"""


def build_strategy_prompt(analysis: str, strategy_code: str, strategy_name: str) -> str:
    return f"""
以下是商品分析报告：

{analysis}

请基于以上内容，输出一套 {strategy_code} 方案，方案类型为“{strategy_name}”。

输出必须是严格 JSON，格式如下：
{{
  "type": "{strategy_name}",
  "target_user": "一句话描述目标用户",
  "core_selling_point": "一句话表达核心卖点",
  "long_tail_keywords": "标题中可用的长尾关键词组合",
  "main_images": [
    {{"position": 1, "description": "主图设计说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 2, "description": "主图设计说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 3, "description": "主图设计说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 4, "description": "主图设计说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 5, "description": "主图设计说明", "prompt": "用于 AI 生图的中文提示词"}}
  ],
  "detail_pages": [
    {{"position": 1, "section_title": "模块标题", "description": "详情页说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 2, "section_title": "模块标题", "description": "详情页说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 3, "section_title": "模块标题", "description": "详情页说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 4, "section_title": "模块标题", "description": "详情页说明", "prompt": "用于 AI 生图的中文提示词"}},
    {{"position": 5, "section_title": "模块标题", "description": "详情页说明", "prompt": "用于 AI 生图的中文提示词"}}
  ],
  "sku_info": {{
    "options": ["规格1", "规格2"],
    "price_range": "价格区间",
    "additional_note": "补充说明"
  }}
}}

要求：
- 所有 prompt 必须是简体中文
- prompt 要具体、可执行，适合电商主图和详情图生成
- 输出不能有额外字段
"""
