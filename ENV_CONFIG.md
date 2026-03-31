# 环境变量配置说明

本项目支持通过环境变量进行配置，适合在 GitHub Actions 或其他 CI/CD 环境中使用。

## 环境变量列表

### LLM 配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `LLM_API_KEY` | LLM API 密钥 | - | `sk-xxx` |
| `LLM_API_BASE` | LLM API 地址 | - | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 使用的模型名称 | - | `deepseek-v3` |

### 关键词配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `KEYWORDS` | 用于筛选论文的关键词，用逗号分隔 | - | `Agent,智能体,强化学习,分类` |

### 飞书配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `FEISHU_ENABLED` | 是否启用飞书推送 | - | `true` 或 `false` |
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook 地址 | - | `https://open.feishu.cn/open-apis/bot/v2/hook/xxx` |
| `FEISHU_SECRET` | 飞书机器人加签密钥（可选） | - | `your-secret` |

### 邮箱配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `EMAIL_ENABLED` | 是否启用邮件推送 | - | `true` 或 `false` |
| `EMAIL_SMTP_SERVER` | SMTP 服务器地址 | - | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP 端口 | - | `465` (SSL) 或 `587` (TLS) |
| `EMAIL_SENDER` | 发件人邮箱 | - | `your_email@qq.com` |
| `EMAIL_PASSWORD` | 授权码 | - | `your_auth_code` |
| `EMAIL_RECEIVER` | 收件人邮箱 | - | `receiver@example.com` |

### Arxiv 配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `ARXIV_CATEGORIES` | 论文分类列表，用逗号分隔 | - | `cs.CL,cs.AI,cs.LG` |

## 常用 Arxiv 分类

- `cs.CL` - 计算语言学 (Computation and Language)
- `cs.AI` - 人工智能 (Artificial Intelligence)
- `cs.LG` - 机器学习 (Machine Learning)
- `cs.CV` - 计算机视觉 (Computer Vision)
- `cs.RO` - 机器人 (Robotics)
- `cs.NE` - 神经与进化计算 (Neural and Evolutionary Computing)

## 使用方法

### 本地开发

1. 编辑 `config.yaml` 填写配置（可选）：

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

2. 或者设置环境变量：

```bash
# Linux/Mac
export LLM_API_KEY="sk-xxx"
export LLM_API_BASE="your-api-base-url"
export LLM_MODEL="your-model-name"
export KEYWORDS="Agent,智能体,强化学习"
export FEISHU_ENABLED=true
export FEISHU_WEBHOOK="your-webhook-url"
export ARXIV_CATEGORIES="cs.CL,cs.AI"

# Windows PowerShell
$env:LLM_API_KEY="sk-xxx"
$env:LLM_API_BASE="your-api-base-url"
$env:LLM_MODEL="your-model-name"
$env:KEYWORDS="Agent,智能体,强化学习"
$env:FEISHU_ENABLED="true"
$env:FEISHU_WEBHOOK="your-webhook-url"
$env:ARXIV_CATEGORIES="cs.CL,cs.AI"
```

### GitHub Actions

在 GitHub 仓库的 Settings → Secrets and variables → Actions 中添加以下 Secrets：

- `LLM_API_KEY`
- `LLM_API_BASE`
- `LLM_MODEL`
- `KEYWORDS`
- `FEISHU_ENABLED`
- `FEISHU_WEBHOOK`
- `FEISHU_SECRET`（可选）
- `EMAIL_ENABLED`
- `EMAIL_SMTP_SERVER`
- `EMAIL_SMTP_PORT`
- `EMAIL_SENDER`
- `EMAIL_PASSWORD`
- `EMAIL_RECEIVER`
- `ARXIV_CATEGORIES`

配置完成后，每天 UTC 04:12（北京时间 12:12）将自动运行，也可在 Actions 页面手动触发。

然后在 workflow 文件中使用：

```yaml
- name: Run Arxiv Fetcher
  env:
    LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
    LLM_API_BASE: ${{ secrets.LLM_API_BASE }}
    LLM_MODEL: ${{ secrets.LLM_MODEL }}
    KEYWORDS: ${{ secrets.KEYWORDS }}
    FEISHU_ENABLED: ${{ secrets.FEISHU_ENABLED }}
    FEISHU_WEBHOOK: ${{ secrets.FEISHU_WEBHOOK }}
    FEISHU_SECRET: ${{ secrets.FEISHU_SECRET }}
    EMAIL_ENABLED: ${{ secrets.EMAIL_ENABLED }}
    EMAIL_SMTP_SERVER: ${{ secrets.EMAIL_SMTP_SERVER }}
    EMAIL_SMTP_PORT: ${{ secrets.EMAIL_SMTP_PORT }}
    EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
    EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
    EMAIL_RECEIVER: ${{ secrets.EMAIL_RECEIVER }}
    ARXIV_CATEGORIES: ${{ secrets.ARXIV_CATEGORIES }}
  run: python main.py
```

## 配置优先级

环境变量的优先级高于配置文件：

1. 环境变量（最高优先级）
2. `config.yaml` 配置文件
3. 默认值（最低优先级）

这意味着你可以在本地使用 `config.yaml`，在 GitHub Actions 中使用环境变量，两者可以共存。
