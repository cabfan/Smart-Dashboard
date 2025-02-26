# Smart Dashboard

一个智能数据分析和可视化平台。

## 最新功能更新

### 性能优化
- 双层缓存机制
  - 命令缓存：缓存自然语言到 SQL 的转换
  - 查询缓存：缓存 SQL 查询结果
- 数据库索引优化
  - 单列索引：team_name, player_name, basic_zone, shot_type
  - 复合索引：关键时刻查询 (quarter, mins_left)
  - 日期索引：按日期和球队/球员的组合查询
- 加载状态优化
  - 实时执行时间显示
  - 智能加载提示
  - 查询耗时统计

### 命令系统优化
- 简化为三个主要命令：`查询统计`、`查天气`、`当前时间`
- 支持命令自动补全和智能提示
- 命令提示界面区分基础命令和示例命令
- 完整的命令验证和错误提示

### 数据可视化增强
- 智能判断是否显示图表
  - 检查是否包含数值列
  - 识别统计类查询（通过关键词和SQL特征）
  - 排除不适合图表的数据（如详细列表）
- 双 Y 轴支持
  - 自动检测百分比和大数值
  - 合理布局不同量级的数据

### 表格功能增强
- 列排序功能
  - 支持数值、日期、文本智能排序
  - 支持中文排序
- 数据格式化
  - 大数值自动添加千分位分隔符
  - 百分比格式化（xx.xx%）
  - 日期本地化显示
  - 自动处理 null/undefined 值
- 表格合计行
  - 自动计算数值列的合计
  - 合计值应用相同的格式化规则

## 性能指标

### 查询响应时间
- 首次查询：~1.5s
  - 命令解析：1s
  - SQL执行：0.5s
- 命令缓存命中：~0.5s
  - SQL获取：0.01s
  - SQL执行：0.5s
- 完全缓存命中：<0.1s
  - SQL获取：0.01s
  - 结果获取：0.01s

### 缓存配置
- 命令缓存：2小时
- 查询缓存：1小时

## 功能特点

- 自然语言查询
- 数据可视化
- 实时数据更新
- 智能分析推荐
- 丰富的数据展示
  - 图表展示
  - 表格展示
  - 单值统计

## 技术栈

### 前端
- Vue 3
- Element Plus
- ECharts
- Markdown-it（文档渲染）
- Highlight.js（代码高亮）

### 后端
- Python
- FastAPI
- SQLite
- WebSocket
- OpenAI/Claude API

## 开发环境设置

### 前端
```bash
cd frontend
npm install
npm run dev
```

### 后端
```bash
cd backend
pip install -r requirements.txt

# 启动后端服务（Win本地）
e:
cd E:\99_my_zen\Smart-Dashboard\backend
call pyenv-venv activate smart-dash
python -m uvicorn src.app:app --host 0.0.0.0 --port 3001 --reload
```

## 环境变量配置

### OpenAI/Claude 配置
```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

### 天气 API 配置
```env
WEATHER_API_KEY=your-weather-api-key-here
```

## 使用说明

### 基础命令
- `@查询统计 xxx`：执行数据查询和统计分析
- `@查天气 xxx`：查询指定城市天气
- `@当前时间`：查看当前时间

### 示例查询
- `@查询统计 各队投篮命中率`
- `@查询统计 投篮区域命中率`
- `@查询统计 球员投篮排名`
- `@查天气 西安现在天气`

## 贡献指南

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 许可证

MIT
