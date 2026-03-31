# Arxiv 论文自动推送系统

一个自动获取 Arxiv 论文、翻译摘要、匹配关键词并推送到飞书/邮箱的工具。

## 功能特性

- 🔍 自动获取 Arxiv 多个分类的最新论文
- 🎯 根据关键词智能匹配相关论文
- 📱 支持推送到飞书
- 📧 支持发送邮件（两封：全部论文 + 匹配论文）
- 🤖 支持 GitHub Actions 自动运行
- 💾 支持本地运行
- 🔧 LLM 调用默认使用 OpenAI 兼容接口，可自定义替换为任意请求方式（详见[常见问题 #6](#6-如何自定义-llm-请求接口)）

## 快速开始

### 方式一：本地运行

1. 克隆项目
```bash
git clone https://github.com/your-username/Daily-Arxiv-LLM.git
cd Daily-Arxiv-LLM
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置（两种方式任选其一）

**方式 A：使用配置文件**

新建 `config.yaml`：

```yaml
# LLM 配置
llm:
  api_key: "your-api-key-here"  # LLM API 密钥
  api_base: "your-api-base-url"  # API 地址
  model: "your-model-name"  # 模型名称

# 关键词配置
keywords:
  - "Agent"
  - "智能体"
  - "强化学习"

# 飞书配置
feishu:
  enabled: true
  webhook: "your-webhook-url"
  secret: ""

# 邮箱配置
email:
  enabled: false
  smtp_server: "smtp.qq.com"
  smtp_port: 465
  sender_email: "your@qq.com"
  sender_password: "your-auth-code"
  receiver_email: "receiver@qq.com"

# Arxiv 配置
arxiv:
  categories:
    - "cs.CL"  # 计算语言学
    - "cs.AI"  # 人工智能
    - "cs.LG"  # 机器学习
```

**方式 B：使用环境变量**

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `LLM_API_KEY` | LLM API 密钥 | `sk-xxx` |
| `LLM_API_BASE` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 模型名称 | `deepseek-v3` |
| `KEYWORDS` | 关键词（逗号分隔） | `Agent,智能体,强化学习` |
| `FEISHU_ENABLED` | 启用飞书 | `true` |
| `FEISHU_WEBHOOK` | 飞书 Webhook | `https://open.feishu.cn/...` |
| `FEISHU_SECRET` | 飞书密钥（可选） | `your-secret` |
| `EMAIL_ENABLED` | 启用邮件 | `true` |
| `EMAIL_SMTP_SERVER` | SMTP 服务器 | `smtp.qq.com` |
| `EMAIL_SMTP_PORT` | SMTP 端口 | `465` |
| `EMAIL_SENDER` | 发件人邮箱 | `your@qq.com` |
| `EMAIL_PASSWORD` | 邮箱授权码 | `your-auth-code` |
| `EMAIL_RECEIVER` | 收件人邮箱 | `receiver@qq.com` |
| `ARXIV_CATEGORIES` | 论文分类（逗号分隔） | `cs.CL,cs.AI,cs.LG` |

完整的环境变量说明请查看 [ENV_CONFIG.md](ENV_CONFIG.md)

### 方式二：GitHub Actions 自动运行（推荐）

1. Fork 本项目到你的 GitHub 账号

2. 在仓库的 Settings → Secrets and variables → Actions 中添加以下 Secrets：
   - `LLM_API_KEY`: LLM API 密钥
   - `LLM_API_BASE`: LLM API 地址（如：`https://api.deepseek.com/v1`）
   - `LLM_MODEL`: 模型名称（如：`deepseek-v3`）
   - `KEYWORDS`: 关键词，用逗号分隔（如：`Agent,智能体,强化学习`）
   - `FEISHU_ENABLED`: 是否启用飞书（`true` 或 `false`）
   - `FEISHU_WEBHOOK`: 飞书 Webhook 地址
   - `FEISHU_SECRET`: 飞书签名密钥（可选，启用签名校验时填写）
   - `EMAIL_ENABLED`: 是否启用邮件（`true` 或 `false`）
   - `EMAIL_SMTP_SERVER`: SMTP 服务器（如：`smtp.qq.com`）
   - `EMAIL_SMTP_PORT`: SMTP 端口（如：`465`）
   - `EMAIL_SENDER`: 发件人邮箱
   - `EMAIL_PASSWORD`: 邮箱授权码
   - `EMAIL_RECEIVER`: 收件人邮箱（可以与发件人邮箱是同一个）
   - `ARXIV_CATEGORIES`: 论文分类（如：`cs.CL,cs.AI,cs.LG`）

3. 启用 GitHub Actions
   - 进入 Actions 标签页
   - 启用 Workflows
   - 每天 UTC 04:12（北京时间 12:12）自动运行

4. 手动触发（可选）
   - 进入 Actions → Daily Arxiv Paper Fetcher
   - 点击 "Run workflow"

详细的环境变量配置说明请查看 [ENV_CONFIG.md](ENV_CONFIG.md)

## 使用方法

### 自动模式（默认）
```bash
python main.py
```
自动获取今天的新提交论文，如果是周末会自动查找最近有效日期。

### 指定日期模式
```bash
python main.py 20260222 20260225
```
获取指定日期区间的论文（格式：YYYYMMDD）。

## 飞书机器人设置

1. 打开飞书群聊
2. 点击右上角 `...` → `设置` → `群机器人`
3. 点击 `添加机器人` → `自定义机器人`
4. 设置机器人名称和描述
5. 复制 Webhook 地址
6. （可选）启用签名校验并复制 secret

## 邮箱授权码获取

### QQ 邮箱
1. 登录 QQ 邮箱
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启 POP3/SMTP 服务
4. 生成授权码

### 163 邮箱
1. 登录 163 邮箱
2. 设置 → POP3/SMTP/IMAP
3. 开启服务
4. 获取授权码

### Gmail
1. 开启两步验证
2. 生成应用专用密码
3. 使用应用密码作为授权码

## 项目结构

```
Daily-Arxiv-LLM/
├── .github/
│   └── workflows/
│       └── daily-fetch.yml      # GitHub Actions 工作流
├── data/                        # 数据缓存目录（自动生成）
│   └── 日期/
│       └── 分类/
│           ├── papers.json      # 所有翻译后的论文
│           ├── tmp/             # 临时缓存文件
│           └── 关键词/
│               ├── matched_papers.json  # 匹配的论文
│               └── match_log.json       # 匹配日志
├── main.py                      # 主程序入口
├── arxiv_crawl_new.py           # Arxiv 爬虫模块（HTML 解析）
├── llm_translator.py            # LLM 翻译和匹配模块（多线程）
├── feishu_notifier.py           # 飞书推送模块
├── email_notifier.py            # 邮件推送模块
├── config.yaml                  # 配置文件（可自行新建，本地开发用）
├── requirements.txt             # 依赖列表
├── README.md                    # 说明文档
└── ENV_CONFIG.md                # 环境变量配置说明
```

## 工作流程

1. **获取论文**：从 Arxiv 爬取指定分类的新论文
2. **周末检测**：如果是周末，自动查找最近有效日期
3. **多分类处理**：并行处理多个分类的论文
4. **翻译摘要**：使用多线程翻译论文摘要为中文
5. **关键词匹配**：使用 LLM 智能匹配相关论文
6. **去重**：对匹配结果去重
7. **推送通知**：
   - 飞书：发送匹配的论文
   - 邮件：发送两封（全部论文 + 匹配论文）

## 常见问题

### 1. GitHub Actions 如何配置？

在仓库的 Settings → Secrets and variables → Actions 中添加所需的环境变量。详见 [ENV_CONFIG.md](ENV_CONFIG.md)

### 2. 如何添加多个论文分类？

设置环境变量：
```bash
export ARXIV_CATEGORIES="cs.CL,cs.AI,cs.LG,cs.CV"
```

或在 `config.yaml` 中：
```yaml
arxiv:
  categories:
    - "cs.CL"
    - "cs.AI"
    - "cs.LG"
```

### 3. 周末没有新论文怎么办？

程序会自动检测，如果爬取的日期不是今天或昨天，会自动往前查找连续3天有论文的日期。

### 4. 如何只发送飞书或只发送邮件？

设置对应的 `enabled` 为 `true` 或 `false`：
```bash
export FEISHU_ENABLED=true
export EMAIL_ENABLED=false
```

### 5. 如何查看历史数据？

所有数据保存在 `data/日期/分类/` 目录下：
- `papers.json`: 所有翻译后的论文
- `tmp/`: 临时缓存文件
- `关键词/matched_papers.json`: 匹配的论文
- `关键词/match_log.json`: 匹配日志

### 6. 如何自定义 LLM 请求接口？

本项目默认使用 OpenAI 兼容接口调用 LLM。如果你希望替换为自己的请求方式，只需修改 `llm_translator.py` 中的 `self_define_receive_llm_output` 函数即可，无需改动其他代码。

该函数是翻译和关键词匹配的统一入口，签名如下：

```python
def self_define_receive_llm_output(self, prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
    # 替换为你自己的请求逻辑，保证返回模型输出的字符串即可
    ...
    return "模型返回的文本"
```

## 定时任务

### GitHub Actions（推荐）

Fork 本项目后，GitHub Actions 会自动每天运行。无需额外配置。
> 注意：设定的定时任务只是任务提交时间，还要排队，程序真正运行要等40min+
