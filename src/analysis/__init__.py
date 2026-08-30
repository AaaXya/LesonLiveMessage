"""
analysis 包 — 弹幕数据分析模块（预留目录）

规划结构：
    analysis/
    ├── __init__.py
    ├── api.py            # 分析结果 API（对接 CloseApi / HTTP 端点）
    ├── algorithms/       # 各分析算法实现
    │   ├── frequency.py  # 弹幕频率分析（按时段统计）
    │   ├── users.py      # 用户活跃度排行
    │   ├── gifts.py      # 礼物价值统计
    │   ├── keywords.py   # 关键词聚类（jieba + TF-IDF）
    │   └── sentiment.py  # 情感分析（未来）
    └── charts.py         # 图表数据生成（对接 ECharts 前端）

数据来源：data/danmu_{room_id}.db（danmu 表）
"""
