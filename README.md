# 🤖 基金AI智能推荐系统 (Fund Advisor) v3.0

基于量化指标和 AI 分析的智能基金推荐平台。系统通过分析历史净值、风险指标，并结合 AI 大模型进行多维度评估，为投资者提供科学的基金选择建议。

## 🌟 核心功能

- **自动化数据采集**：集成 AkShare，自动抓取全量基金数据及历史行情。
- **量化指标评估**：内置多种风控与收益模型（夏普比率、卡玛比率、波动率、回撤管理等）。
- **AI 智能深度分析**：结合 OpenAI/DeepSeek 等大模型，对入选基金进行深度定性与定量分析。
- **多维度快照系统**：支持生成每日/每周市场快照，记录市场表现与筛选结果。
- **现代化 Web 界面**：直观的仪表盘，展示系统状态、入选基金明细及 AI 生成的周报/日报。
- **自动化调度**：后台自动执行数据更新与分析任务。

## 🛠️ 技术栈

- **后端**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.9+)
- **量化**: [AkShare](https://akshare.xyz/), [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **AI**: [OpenAI SDK](https://github.com/openai/openai-python) (兼容多种主流大模型)
- **调度**: [APScheduler](https://apscheduler.readthedocs.io/)
- **前端**: 原生 HTML5 / CSS3 / JavaScript (现代化响应式设计)

## 🚀 快速开始

### 1. 环境准备

确保您的本地环境已安装 Python 3.9 或更高版本。

```bash
# 克隆仓库
git clone https://github.com/QS1314520ZHOU/fund-advisor.git
cd fund-advisor
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件，并参考以下配置：

```env
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo
ADMIN_TOKEN=your_admin_token
```

### 4. 运行应用

```bash
python backend/main.py
```
启动后，系统将自动在浏览器中打开：`http://127.0.0.1:8000/app`

## 📂 项目结构

```text
fund-advisor/
├── backend/            # 后端核心代码
│   ├── api/            # API 接口路由
│   ├── data/           # 本地存储数据及数据库
│   ├── services/       # 业务逻辑处理 (AI, 量化, 快照)
│   ├── main.py         # 应用入口
│   └── config.py       # 配置管理
├── frontend/           # 前端 Web 页面
├── data/               # 基础原始数据 (可选)
├── requirements.txt    # 依赖说明
└── README.md           # 项目文档
```

## 📚 API 文档

系统启动后可访问以下路径查看交互式 API 文档：

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---
Copyright © 2024 [QS1314520ZHOU](https://github.com/QS1314520ZHOU)
