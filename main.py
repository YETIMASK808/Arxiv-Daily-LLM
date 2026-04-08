"""
Arxiv 论文推送主程序
"""
import yaml
import sys
import os
from datetime import datetime, timedelta
from llm_translator import LLMTranslator
from feishu_notifier import FeishuNotifier
from arxiv_crawl_new import ArxivNewFetcher
from email_notifier import EmailNotifier

def load_config(config_path: str = "config.yaml") -> dict:
    """
    加载配置文件，优先使用环境变量
    环境变量会覆盖配置文件中的值
    """
    # 先尝试加载配置文件（如果存在）
    config = {}
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"⚠️  加载配置文件失败: {e}，将使用环境变量")
    
    # 从环境变量读取配置（优先级更高）
    # LLM 配置
    config.setdefault('llm', {})
    config['llm']['api_key'] = os.getenv('LLM_API_KEY', config.get('llm', {}).get('api_key', ''))
    config['llm']['api_base'] = os.getenv('LLM_API_BASE', config.get('llm', {}).get('api_base', 'https://api.openai.com/v1'))
    config['llm']['model'] = os.getenv('LLM_MODEL', config.get('llm', {}).get('model', 'deepseek-v3'))
    config['llm']['appid'] = os.getenv('LLM_APPID', config.get('llm', {}).get('appid', ''))
    
    # 关键词配置
    keywords_env = os.getenv('KEYWORDS', '')
    if keywords_env:
        # 支持逗号或分号分隔
        config['keywords'] = [k.strip() for k in keywords_env.replace(';', ',').split(',') if k.strip()]
    elif 'keywords' not in config or not config['keywords']:
        config['keywords'] = ['Agent', '智能体', '强化学习']
    
    # 飞书配置
    config.setdefault('feishu', {})
    config['feishu']['enabled'] = os.getenv('FEISHU_ENABLED', str(config.get('feishu', {}).get('enabled', 'false'))).lower() == 'true'
    config['feishu']['webhook'] = os.getenv('FEISHU_WEBHOOK', config.get('feishu', {}).get('webhook', ''))
    config['feishu']['secret'] = os.getenv('FEISHU_SECRET', config.get('feishu', {}).get('secret', ''))
    
    # 邮箱配置
    config.setdefault('email', {})
    config['email']['enabled'] = os.getenv('EMAIL_ENABLED', str(config.get('email', {}).get('enabled', 'false'))).lower() == 'true'
    config['email']['smtp_server'] = os.getenv('EMAIL_SMTP_SERVER', config.get('email', {}).get('smtp_server', 'smtp.qq.com'))
    config['email']['smtp_port'] = int(os.getenv('EMAIL_SMTP_PORT', str(config.get('email', {}).get('smtp_port', 465))))
    config['email']['sender_email'] = os.getenv('EMAIL_SENDER', config.get('email', {}).get('sender_email', ''))
    config['email']['sender_password'] = os.getenv('EMAIL_PASSWORD', config.get('email', {}).get('sender_password', ''))
    config['email']['receiver_email'] = os.getenv('EMAIL_RECEIVER', config.get('email', {}).get('receiver_email', ''))
    
    # Arxiv 配置
    config.setdefault('arxiv', {})
    categories_env = os.getenv('ARXIV_CATEGORIES', '')
    if categories_env:
        # 支持逗号或分号分隔
        config['arxiv']['categories'] = [c.strip() for c in categories_env.replace(';', ',').split(',') if c.strip()]
    elif 'categories' not in config.get('arxiv', {}):
        # 向后兼容旧的 category 配置
        category = config.get('arxiv', {}).get('category', 'cs.CL')
        config['arxiv']['categories'] = [category]
    
    return config


def validate_date_format(date_str: str) -> bool:
    """
    验证日期格式是否为 YYYYMMDD
    
    Args:
        date_str: 日期字符串
        
    Returns:
        bool: 格式正确返回 True，否则返回 False
    """
    # 检查长度
    if len(date_str) != 8:
        return False
    
    # 检查是否全为数字
    if not date_str.isdigit():
        return False
    
    # 检查是否为有效日期
    try:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        
        # 验证日期是否有效
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Arxiv 论文自动推送系统")
    print("=" * 60)
    print()
    
    # 解析命令行参数
    use_date_range = False
    start_day = None
    end_day = None
    
    if len(sys.argv) == 3:
        # python main.py 20260222 20260225 (获取指定日期区间的论文)
        start_day = sys.argv[1]
        end_day = sys.argv[2]
        
        # 验证日期格式
        if not validate_date_format(start_day):
            print(f"错误: 开始日期格式不正确 '{start_day}'")
            print("日期格式必须为 YYYYMMDD，例如: 20260222")
            print("示例: python main.py 20260222 20260225")
            exit(1)
        
        if not validate_date_format(end_day):
            print(f"错误: 结束日期格式不正确 '{end_day}'")
            print("日期格式必须为 YYYYMMDD，例如: 20260225")
            print("示例: python main.py 20260222 20260225")
            exit(1)
        
        # 验证日期逻辑（开始日期不能晚于结束日期）
        if start_day > end_day:
            print(f"错误: 开始日期 {start_day} 不能晚于结束日期 {end_day}")
            exit(1)
        
        use_date_range = True
        print(f"模式: 获取 {start_day} 至 {end_day} 的论文")
        
    elif len(sys.argv) == 2:
        print("错误: 参数不完整，需要提供开始日期和结束日期")
        print("用法:")
        print("  python main.py                    # 获取今天的新提交论文")
        print("  python main.py 20260222 20260225  # 获取指定日期区间的论文 (格式: YYYYMMDD)")
        exit(1)
    elif len(sys.argv) == 1:
        print("模式: 获取今天的新提交论文")
    else:
        print("错误: 参数过多")
        print("用法:")
        print("  python main.py                    # 获取今天的新提交论文")
        print("  python main.py 20260222 20260225  # 获取指定日期区间的论文 (格式: YYYYMMDD)")
        exit(1)
    
    print()
    
    # 加载配置
    print("1. 加载配置文件...")
    config = load_config()
    
    if config['feishu']['webhook'] == "your-feishu-webhook-url":
        print("错误: 请在 config.yaml 中配置你的飞书 Webhook 地址")
        exit(1)
    
    print("✓ 配置加载成功")
    print()
    
    # 获取分类列表
    categories = config['arxiv'].get('categories', [])
    if not categories:
        # 向后兼容：如果没有 categories，尝试读取旧的 category
        category = config['arxiv'].get('category', 'cs.CL')
        categories = [category]
    
    print(f"将处理以下分类: {', '.join(categories)}")
    print()
    
    # 存储所有分类的论文
    all_papers_by_category = {}
    all_matched_papers = []
    
    # 遍历每个分类
    for category_idx, category in enumerate(categories, 1):
        print("=" * 60)
        print(f"处理分类 [{category_idx}/{len(categories)}]: {category}")
        print("=" * 60)
        print()
        
        # 获取论文
        print(f"2.{category_idx} 从 Arxiv 获取 {category} 分类的论文...")
        fetcher = ArxivNewFetcher(category=category)
        
        if use_date_range:
            # 获取指定日期区间的论文
            date_str, papers = fetcher.fetch_specific_day(start_day=start_day, end_day=end_day)
        else:
            # 获取今天的新提交论文
            date_str, papers = fetcher.fetch_new_submissions()
            
            # 检查日期是否为今天或昨天（只在第一个分类时检查）
            if category_idx == 1 and date_str:
                from datetime import datetime, timedelta
                
                # 解析爬取到的日期
                try:
                    # date_str 格式: YYYY-M-D
                    parts = date_str.split('-')
                    crawled_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    yesterday = today - timedelta(days=1)
                    
                    # 如果爬取的日期不是今天或昨天，说明是周末
                    if crawled_date.date() not in [today.date(), yesterday.date()]:
                        print(f"⚠️  爬取到的日期 {date_str} 不是今天或昨天")
                        print("检测到可能是周末，arXiv 未更新")
                        print("开始自动查找有效的日期范围...")
                        
                        # 查找连续3天都有论文的日期
                        start_day, end_day = fetcher.find_valid_date_range(max_days_back=14)
                        
                        if start_day and end_day:
                            print(f"使用找到的日期范围: {start_day} 至 {end_day}")
                            date_str, papers = fetcher.fetch_specific_day(start_day=start_day, end_day=end_day)
                            use_date_range = True  # 标记为使用日期范围模式
                        else:
                            print("❌ 未找到有效的日期范围")
                            exit(1)
                            
                except Exception as e:
                    print(f"⚠️  日期解析出错: {e}")
                    # 继续使用原来的日期和论文
        
        if not date_str:
            print(f"✗ 获取 {category} 分类失败，跳过")
            continue
        
        print(f"✓ 获取的论文日期: {date_str}")
        
        if not papers:
            print(f"✗ {category} 分类没有找到任何论文，跳过")
            continue
        
        print(f"✓ 成功获取 {len(papers)} 篇论文")
        print()
        
        # 翻译摘要
        print(f"3.{category_idx} 翻译 {category} 分类的论文摘要...")
        translator = LLMTranslator(
            api_key=config['llm']['api_key'],
            api_base=config['llm']['api_base'],
            model=config['llm']['model'],
            appid=config['llm']['appid']
        )
        
        # 翻译并保存到 data/日期/分类/papers.json
        translator.batch_translate(
            papers=papers,
            date_str=date_str,
            category=category
        )
        
        # 从本地加载翻译后的数据
        papers = translator._load_papers(date_str, category)
        
        if not papers:
            print(f"✗ {category} 分类翻译失败或加载失败，跳过")
            continue
        
        print()
        
        # 匹配关键词
        print(f"4.{category_idx} 匹配 {category} 分类的关键词相关论文...")
        keywords = config['keywords']
        print(f"关键词: {', '.join(keywords)}")
        
        # 匹配并保存到 data/日期/分类/关键词/matched_papers.json
        matched_papers = translator.match_keywords(
            papers=papers,
            keywords=keywords,
            date_str=date_str,
            category=category
        )
        print()
        
        if matched_papers:
            print(f"✓ {category} 分类找到 {len(matched_papers)} 篇相关论文")
            all_matched_papers.extend(matched_papers)
        else:
            print(f"✗ {category} 分类没有找到相关论文")
        
        # 保存该分类的所有论文
        all_papers_by_category[category] = papers
        print()
    
    # 对匹配到的论文进行去重（根据 arxiv_id）
    if all_matched_papers:
        print("去重匹配到的论文...")
        seen_ids = set()
        unique_matched_papers = []
        for paper in all_matched_papers:
            arxiv_id = paper.get('arxiv_id')
            if arxiv_id and arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                unique_matched_papers.append(paper)
    
        if len(all_matched_papers) != len(unique_matched_papers):
            print(f"✓ 去重完成: {len(all_matched_papers)} 篇 → {len(unique_matched_papers)} 篇（去除 {len(all_matched_papers) - len(unique_matched_papers)} 篇重复）")
        else:
            print(f"✓ 无重复论文")
    
    all_matched_papers = unique_matched_papers
    
    # 检查是否有匹配的论文
    if not all_matched_papers:
        print("=" * 60)
        print("所有分类都没有找到相关论文，程序退出")
        print("=" * 60)
        exit(0)
    
    print("=" * 60)
    print(f"总计找到 {len(all_matched_papers)} 篇相关论文（来自 {len(categories)} 个分类）")
    print("=" * 60)
    print()
    
    # 发送通知
    print("5. 发送通知...")
    
    feishu_success = True
    email_success = True
    
    # 发送到飞书（如果启用）
    if config.get('feishu', {}).get('enabled', True):
        print("5.1 分批次发送匹配论文到飞书（每个批次5篇）...")
        feishu_notifier = FeishuNotifier(
            webhook=config['feishu']['webhook'],
            secret=config['feishu'].get('secret', '')
        )
        feishu_success = feishu_notifier.send_papers(
            all_matched_papers, 
            date_str, 
            keywords=config['keywords'],
            categories=categories
        )
    else:
        print("5.1 飞书推送未启用（在 config.yaml 中设置 feishu.enabled: true 启用）")
    
    # 发送邮件（如果启用）
    if config.get('email', {}).get('enabled', False):
        print("5.2 发送邮件...")
        email_notifier = EmailNotifier(
            smtp_server=config['email']['smtp_server'],
            smtp_port=config['email']['smtp_port'],
            sender_email=config['email']['sender_email'],
            sender_password=config['email']['sender_password'],
            receiver_email=config['email']['receiver_email']
        )
        
        # 合并所有分类的论文
        all_papers = []
        for papers in all_papers_by_category.values():
            if papers:  # 检查 papers 不为 None
                all_papers.extend(papers)
        
        # 第一封邮件：所有翻译后的论文
        print("  发送第一封邮件：所有翻译摘要后的论文...")
        email1_success = email_notifier.send_all_papers(
            all_papers, 
            date_str,
            categories=categories
        )
        
        # 第二封邮件：匹配到的相关论文
        print("  发送第二封邮件：匹配到的相关论文...")
        email2_success = email_notifier.send_matched_papers(
            all_matched_papers, 
            date_str,
            keywords=config['keywords'],
            categories=categories
        )
        
        email_success = email1_success and email2_success
    else:
        print("5.2 邮件推送未启用（在 config.yaml 中设置 email.enabled: true 启用）")
    
    print()
    print("=" * 60)
    if feishu_success and email_success:
        print("✓ 任务完成！")
    else:
        if not feishu_success:
            print("✗ 发送飞书消息时出现问题")
        if not email_success:
            print("✗ 发送邮件时出现问题")
    print("=" * 60)


if __name__ == "__main__":
    main()

