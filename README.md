# Arxiv 论文自动推送系统

自动抓取 Arxiv 最新论文、LLM 翻译摘要、智能关键词匹配，并推送至飞书 / 邮箱。

## 功能特性

- 抓取 Arxiv 多个分类的当日新提交论文（HTML 解析，无需 API）
- LLM 多线程翻译论文摘要为中文
- LLM 智能关键词匹配，筛选相关论文
- 支持飞书 Webhook 推送
- 支持邮件推送（两封：全部论文 + 匹配论文）
- 支持 GitHub Actions 每日自动运行
- 周末 / 节假日自动检测并回退到最近有效日期
- 支持指定日期区间手动拉取
- LLM 调用默认使用 OpenAI 兼容接口，可自定义替换（见[常见问题 #6](#6-如何自定义-llm-请求接口)）

## 快速开始

### 方式一：本地运行

**1. 克隆项目**

```bash
git clone https://github.com/your-username/Arxiv-Daily-LLM.git
cd Arxiv-Daily-LLM
```

**2. 安装依赖**

```bash
pip install -r requirements.txt
```

**3. 配置（两种方式任选其一）**

**方式 A：配置文件**

新建 `config.yaml`（**注意：不要将含真实密钥的配置文件提交到仓库**）：

```yaml
# LLM 配置
llm:
  api_key: "your-api-key"
  api_base: "https://api.deepseek.com/v1"
  model: "deepseek-v3"

# 关键词配置（用于筛选相关论文）
keywords:
  - "Agent"
  - "智能体"
  - "强化学习"

# 飞书配置
feishu:
  enabled: true
  webhook: "your-webhook-url"
  secret: ""            # 可选：启用签名校验时填写

# 邮箱配置
email:
  enabled: false
  smtp_server: "smtp.qq.com"
  smtp_port: 465
  sender_email: "your@qq.com"
  sender_password: "your-auth-code"
  receiver_email: "receiver@qq.com"

# Arxiv 分类配置
arxiv:
  categories:
    - "cs.CL"   # 计算语言学
    - "cs.AI"   # 人工智能
    - "cs.LG"   # 机器学习
```

**方式 B：环境变量**

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `LLM_API_KEY` | LLM API 密钥 | `sk-xxx` |
| `LLM_API_BASE` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 模型名称 | `deepseek-v3` |
| `KEYWORDS` | 关键词（逗号分隔） | `Agent,智能体,强化学习` |
| `FEISHU_ENABLED` | 启用飞书 | `true` |
| `FEISHU_WEBHOOK` | 飞书 Webhook | `https://open.feishu.cn/...` |
| `FEISHU_SECRET` | 飞书签名密钥（可选） | `your-secret` |
| `EMAIL_ENABLED` | 启用邮件 | `true` |
| `EMAIL_SMTP_SERVER` | SMTP 服务器 | `smtp.qq.com` |
| `EMAIL_SMTP_PORT` | SMTP 端口 | `465` |
| `EMAIL_SENDER` | 发件人邮箱 | `your@qq.com` |
| `EMAIL_PASSWORD` | 邮箱授权码 | `your-auth-code` |
| `EMAIL_RECEIVER` | 收件人邮箱 | `receiver@qq.com` |
| `ARXIV_CATEGORIES` | 论文分类（逗号分隔） | `cs.CL,cs.AI,cs.LG` |

**4. 运行**

```bash
python main.py
```

---

### 方式二：GitHub Actions 自动运行（推荐）

1. **Fork** 本项目到你的 GitHub 账号

2. 进入仓库 **Settings → Secrets and variables → Actions**，添加以下 Secrets：

   | Secret 名称 | 说明 |
   |-------------|------|
   | `LLM_API_KEY` | LLM API 密钥 |
   | `LLM_API_BASE` | LLM API 地址 |
   | `LLM_MODEL` | 模型名称 |
   | `KEYWORDS` | 关键词，逗号分隔 |
   | `FEISHU_ENABLED` | `true` 或 `false` |
   | `FEISHU_WEBHOOK` | 飞书 Webhook 地址 |
   | `FEISHU_SECRET` | 飞书签名密钥（可选） |
   | `EMAIL_ENABLED` | `true` 或 `false` |
   | `EMAIL_SMTP_SERVER` | SMTP 服务器 |
   | `EMAIL_SMTP_PORT` | SMTP 端口 |
   | `EMAIL_SENDER` | 发件人邮箱 |
   | `EMAIL_PASSWORD` | 邮箱授权码 |
   | `EMAIL_RECEIVER` | 收件人邮箱 |
   | `ARXIV_CATEGORIES` | 论文分类，逗号分隔 |

3. 进入 **Actions** 标签页，启用 Workflows

4. 默认每天 **UTC 04:12（北京时间 12:12）** 自动运行；也可在 Actions → Daily Arxiv Paper Fetcher → Run workflow 手动触发

## 使用方法

### 自动模式（默认）

```bash
python main.py
```

自动获取当日新提交论文。若是周末 / 节假日，自动回退到最近有论文的日期范围。

### 指定日期区间

```bash
python main.py 20260222 20260225
```

获取指定日期区间内提交的论文（格式：`YYYYMMDD`）。

## 工作流程

```
抓取论文 → 多线程翻译摘要 → LLM 关键词匹配 → 去重 → 推送通知
```

1. 从 Arxiv 网页抓取指定分类的当日新提交论文
2. 多线程调用 LLM 将摘要翻译为中文，结果缓存至 `data/` 目录
3. 调用 LLM 对每篇论文进行关键词相关性判断
4. 跨分类去重（以 `arxiv_id` 为唯一键）
5. 推送通知：
   - **飞书**：分批次发送匹配的论文（每批 5 篇）
   - **邮件**：发送两封（所有翻译论文 + 仅匹配论文）

## 项目结构

```
Arxiv-Daily-LLM/
├── .github/
│   └── workflows/
│       └── daily-fetch.yml      # GitHub Actions 工作流
├── data/                        # 数据缓存目录（自动生成）
│   └── <日期>/
│       └── <分类>/
│           ├── papers.json              # 所有翻译后的论文
│           ├── tmp/                     # 并行翻译临时缓存
│           └── <关键词>/
│               ├── matched_papers.json  # 匹配的论文
│               └── match_log.json       # 匹配日志
├── main.py                      # 主程序入口
├── arxiv_crawl_new.py           # Arxiv 网页爬虫（HTML 解析）
├── llm_translator.py            # LLM 翻译 + 关键词匹配（多线程）
├── feishu_notifier.py           # 飞书推送
├── email_notifier.py            # 邮件推送
├── config.yaml                  # 本地配置文件（勿提交真实密钥）
└── requirements.txt             # 依赖列表
```

## 飞书机器人设置

1. 打开飞书群聊 → 右上角 `···` → 设置 → 群机器人
2. 添加机器人 → 自定义机器人
3. 设置名称，复制 Webhook 地址
4. （可选）启用签名校验并复制 secret

## 邮箱授权码获取

| 邮箱 | 步骤 |
|------|------|
| **QQ 邮箱** | 设置 → 账户 → 开启 POP3/SMTP 服务 → 生成授权码 |
| **163 邮箱** | 设置 → POP3/SMTP/IMAP → 开启服务 → 获取授权码 |
| **Gmail** | 开启两步验证 → 生成应用专用密码 |

## 常见问题

### 1. GitHub Actions 如何配置？

在仓库的 Settings → Secrets and variables → Actions 中添加所需环境变量，详见[方式二](#方式二github-actions-自动运行推荐)。

### 2. 如何添加多个论文分类？

环境变量：
```bash
export ARXIV_CATEGORIES="cs.CL,cs.AI,cs.LG,cs.CV"
```

或 `config.yaml`：
```yaml
arxiv:
  categories:
    - "cs.CL"
    - "cs.AI"
    - "cs.LG"
    - "cs.CV"
```

可选分类参考：`cs.CL`（计算语言学）、`cs.AI`（人工智能）、`cs.LG`（机器学习）、`cs.CV`（计算机视觉）、`cs.RO`（机器人）。

### 3. 周末 / 节假日没有新论文怎么办？

程序会自动检测：若抓取到的日期不是今天或昨天，自动向前查找最近连续有论文的日期范围（最多回溯 14 天），无需手动干预。

### 4. 如何只推送飞书或只发邮件？

在配置中将对应项的 `enabled` 设为 `true` 或 `false`：
```bash
export FEISHU_ENABLED=true
export EMAIL_ENABLED=false
```

### 5. 历史数据保存在哪里？

所有数据缓存在 `data/<日期>/<分类>/` 目录：
- `papers.json`：所有翻译后的论文
- `<关键词>/matched_papers.json`：匹配的论文
- `<关键词>/match_log.json`：LLM 匹配日志

### 6. 如何自定义 LLM 请求接口？

修改 `llm_translator.py` 中的 `self_define_receive_llm_output` 函数，该函数是翻译和关键词匹配的统一调用入口：

```python
def self_define_receive_llm_output(
    self,
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    # 替换为你自己的请求逻辑，返回模型输出的字符串即可
    ...
    return "模型返回的文本"
```

其他代码无需改动。
