# 🤖 基金AI智能推荐系统 (Fund Advisor) v4.0 Edge

基于量化指标与 AI 深度协议的智能基金投研平台。系统通过分析历史净值、风险指标，并结合 v4.0 结构化 AI 分析协议，为投资者提供极简、专业且具备直观视觉体验的投资参考。

## 🌟 核心功能

- **v4.0 结构化 AI 分析**：采用全新的结构化分析卡片，涵盖基调总结、业绩归归因、压力测试及经理风格画像。
- **极简玻璃拟态 UI**：基于现代审美设计的深色模式界面，支持毛玻璃特效（Glassmorphism）与丝滑交互。
- **定投时光机 (DCA)**：内置历史定投回测引擎，直观展示“穿越”后的投资回报。
- **费率刺客揭露**：自动折算隐形成本，帮助投资者识别高费率陷阱。
- **自动化数据体系**：集成 AkShare 实时同步，支持本地静态快照与 API 动态加载的双重保障机制。
- **量化指标评估**：内置 Alpha、Beta、夏普比率、最大回测等深度量化维度。

## 🛠️ 技术栈

- **后端**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.9+)
- **量化**: [AkShare](https://akshare.xyz/), [Pandas](https://pandas.pydata.org/)
- **AI**: 兼容 OpenAI/DeepSeek 协议的 v4 结构化解析
- **前端**: Vue 3 (SFC-free), Lucide Icons, Vanilla CSS (Glassmorphism Design)

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
