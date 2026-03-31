"""
Arxiv 新提交论文爬取模块
专门爬取 https://arxiv.org/list/cs.CL/new 页面
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Optional
import time
import re
from datetime import datetime


class ArxivNewFetcher:
    """从 Arxiv 的 new submissions 页面爬取论文"""
    
    def __init__(self, category: str = "cs.CL"):
        self.category = category
        self.base_url = f"https://arxiv.org/list/{category}/new"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_new_submissions(self, retry_times: int = 10) -> Tuple[Optional[str], List[Dict]]:
        """
        获取新提交的论文
        
        Returns:
            Tuple[Optional[str], List[Dict]]: 
                - 日期字符串 (格式: YYYY-M-D)
                - 论文列表，每篇论文包含:
                    - arxiv_id: arXiv ID
                    - title: 标题
                    - authors: 作者列表
                    - abstract: 摘要
                    - arxiv_url: 论文页面链接
                    - pdf_url: PDF 下载链接
                    - subjects: 学科分类
                    - submission_type: 提交类型 (new/cross/replace)
        """
        for attempt in range(retry_times):
            try:
                print(f"正在获取 {self.base_url} ...")
                print(f"尝试 {attempt + 1}/{retry_times}")
                
                response = requests.get(self.base_url, headers=self.headers, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                print(f"✓ 页面获取成功，状态码: {response.status_code}")
                
                # 解析 HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取日期
                date_str = self._parse_date(soup)
                if date_str:
                    print(f"✓ 找到日期: {date_str}")
                else:
                    print("⚠️  未找到日期信息")
                
                papers = []
                
                # 找到所有论文条目
                # 新提交的论文在 id="dlpage" 的 dl 标签中
                dl_page = soup.find('dl', id='articles')
                
                if not dl_page:
                    print("⚠️  未找到论文列表容器")
                    return date_str, []
                
                # 获取所有 dt 和 dd 标签
                dt_tags = dl_page.find_all('dt')
                dd_tags = dl_page.find_all('dd')
                
                print(f"找到 {len(dt_tags)} 篇论文")
                
                # 遍历每篇论文
                for dt, dd in zip(dt_tags, dd_tags):
                    try:
                        paper = self._parse_paper(dt, dd)
                        if paper:
                            papers.append(paper)
                    except Exception as e:
                        print(f"⚠️  解析论文时出错: {e}")
                        continue
                
                print(f"成功解析 {len(papers)} 篇论文")
                return date_str, papers
                
            except requests.RequestException as e:
                print(f"⚠️  请求失败: {e}")
                if attempt < retry_times - 1:
                    # wait_time = (attempt + 1) * 10
                    wait_time = 10
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print("❌ 已达到最大重试次数")
                    return None, []
            except Exception as e:
                print(f"❌ 发生未预期的错误: {e}")
                return None, []
        
        return None, []

    def check_day_has_papers(self, day: str) -> bool:
        """
        检查某一天是否有论文发布
        
        Args:
            day: 日期字符串 (格式: YYYYMMDD)
            
        Returns:
            True 表示有论文，False 表示没有论文或出错
        """
        url = f"https://export.arxiv.org/api/query?search_query=cat:{self.category}+AND+submittedDate:[{day}0000+TO+{day}2359]&max_results=1&sortBy=submittedDate&sortOrder=descending"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # 解析 XML
            try:
                soup = BeautifulSoup(response.text, 'lxml-xml')
            except:
                soup = BeautifulSoup(response.text, 'html.parser')
            
            entries = soup.find_all('entry')
            
            # 检查是否有错误条目
            for entry in entries:
                id_tag = entry.find('id')
                if id_tag and 'api/errors' in id_tag.text:
                    return False
                title_tag = entry.find('title')
                if title_tag and title_tag.text.strip().lower() == 'error':
                    return False
            
            # 如果有正常的论文条目，返回 True
            return len(entries) > 0
            
        except Exception as e:
            print(f"⚠️  检查日期 {day} 时出错: {e}")
            return False
    
    def find_valid_date_range(self, max_days_back: int = 14) -> Tuple[Optional[str], Optional[str]]:
        """
        自动查找有效的日期范围（连续3天都有论文）
        
        Args:
            max_days_back: 最多往前查找多少天
            
        Returns:
            (start_day, end_day) 格式为 YYYYMMDD，如果找不到返回 (None, None)
        """
        from datetime import datetime, timedelta
        
        print("开始查找有效的日期范围...")
        
        today = datetime.now()
        consecutive_days = []
        
        for i in range(max_days_back):
            check_date = today - timedelta(days=i)
            date_str = check_date.strftime("%Y%m%d")
            
            print(f"检查日期: {date_str}...", end=" ")
            
            if self.check_day_has_papers(date_str):
                print("✓ 有论文")
                consecutive_days.append(date_str)
                
                # 如果找到连续3天都有论文
                if len(consecutive_days) >= 3:
                    # 返回最近的3天
                    end_day = consecutive_days[0]
                    start_day = consecutive_days[2]
                    print(f"\n✓ 找到有效日期范围: {start_day} 至 {end_day}")
                    return start_day, end_day
            else:
                print("✗ 无论文")
                # 重置连续天数
                consecutive_days = []
            
            time.sleep(1)  # 避免请求过快
        
        print(f"\n✗ 在过去 {max_days_back} 天内未找到连续3天有论文的日期")
        return None, None
    
    def fetch_specific_day(self, start_day, end_day, retry_times: int = 10) -> Tuple[Optional[str], List[Dict]]:
        """
        获取最近几天的论文
        
        Args:
            days: 获取最近几天的论文（默认3天）
            retry_times: 重试次数
            
        Returns:
            Tuple[Optional[str], List[Dict]]: 
                - 日期范围字符串 (格式: YYYY-M-D)
                - 论文列表
        """
        
        # 构建 URL
        url = f"https://export.arxiv.org/api/query?search_query=cat:{self.category}+AND+submittedDate:[{start_day}0000+TO+{end_day}2359]&max_results=100&sortBy=submittedDate&sortOrder=descending"
        
        print(f"正在获取 {start_day} 到 {end_day} 的论文...")
        print(f"URL: {url}")
        
        for attempt in range(retry_times):
            try:
                print(f"尝试 {attempt + 1}/{retry_times}")
                
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                print(f"✓ 页面获取成功，状态码: {response.status_code}")
                
                # 解析 XML (arXiv API 返回的是 XML 格式)
                # 使用 lxml-xml 解析器，如果没有安装 lxml，会自动降级到 html.parser
                try:
                    soup = BeautifulSoup(response.text, 'lxml-xml')
                except:
                    # 如果 lxml 不可用，使用 html.parser
                    soup = BeautifulSoup(response.text, 'html.parser')
                
                papers = []
                entries = soup.find_all('entry')
                
                print(f"找到 {len(entries)} 篇论文")
                
                for entry in entries:
                    try:
                        paper = self._parse_api_entry(entry)
                        if paper:
                            papers.append(paper)
                    except Exception as e:
                        print(f"⚠️  解析论文时出错: {e}")
                        continue
                
                print(f"成功解析 {len(papers)} 篇论文")
                
                # 返回日期范围
                date_range = f"{start_day}_{end_day}"
                return date_range, papers
                
            except requests.RequestException as e:
                print(f"⚠️  请求失败: {e}")
                if attempt < retry_times - 1:
                    wait_time = 10
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print("❌ 已达到最大重试次数")
                    return None, []
            except Exception as e:
                print(f"❌ 发生未预期的错误: {e}")
                return None, []
        
        return None, []
    
    def _parse_api_entry(self, entry) -> Dict:
        """解析 arXiv API 返回的单篇论文信息"""
        paper = {}
        
        try:
            # 获取 arXiv ID
            id_tag = entry.find('id')
            if id_tag:
                arxiv_url = id_tag.text.strip()
                arxiv_id = arxiv_url.split('/')[-1]
                paper['arxiv_id'] = arxiv_id
                paper['arxiv_url'] = arxiv_url
                paper['pdf_url'] = arxiv_url.replace('/abs/', '/pdf/') + '.pdf'
            else:
                return None
            
            # 获取标题
            title_tag = entry.find('title')
            if title_tag:
                title = title_tag.text.strip()
                title = re.sub(r'\s+', ' ', title)
                paper['title'] = title
            
            # 获取作者
            authors = []
            for author_tag in entry.find_all('author'):
                name_tag = author_tag.find('name')
                if name_tag:
                    authors.append(name_tag.text.strip())
            paper['authors'] = authors
            
            # 获取摘要
            summary_tag = entry.find('summary')
            if summary_tag:
                abstract = summary_tag.text.strip()
                abstract = re.sub(r'\s+', ' ', abstract)
                paper['abstract'] = abstract
            
            # 获取分类
            categories = []
            for category_tag in entry.find_all('category'):
                term = category_tag.get('term')
                if term:
                    categories.append(term)
            paper['subjects'] = ', '.join(categories) if categories else ''
            
            # 获取发布日期
            published_tag = entry.find('published')
            if published_tag:
                paper['published'] = published_tag.text.strip()
            
            paper['submission_type'] = 'recent'
            
            return paper
            
        except Exception as e:
            print(f"⚠️  解析 API 条目时出错: {e}")
            return None
    
    def _parse_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        解析页面上的日期
        例如: "Showing new listings for Wednesday, 25 February 2026" -> "2026-2-25"
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            日期字符串 (格式: YYYY-M-D) 或 None
        """
        try:
            # 查找包含日期的 h3 标签
            h3_tag = soup.find('h3')
            if not h3_tag:
                return None
            
            text = h3_tag.get_text().strip()
            # 例如: "Showing new listings for Wednesday, 25 February 2026"
            
            # 使用正则表达式提取日期部分
            # 匹配格式: "日, DD Month YYYY"
            pattern = r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})'
            match = re.search(pattern, text)
            
            if not match:
                return None
            
            day = match.group(1)
            month_name = match.group(2)
            year = match.group(3)
            
            # 月份名称到数字的映射
            month_map = {
                'January': '1', 'February': '2', 'March': '3', 'April': '4',
                'May': '5', 'June': '6', 'July': '7', 'August': '8',
                'September': '9', 'October': '10', 'November': '11', 'December': '12'
            }
            
            month = month_map.get(month_name)
            if not month:
                return None
            
            # 返回格式: YYYY-M-D
            return f"{year}-{month}-{day}"
            
        except Exception as e:
            print(f"⚠️  解析日期时出错: {e}")
            return None
    
    def _parse_paper(self, dt, dd) -> Dict:
        """解析单篇论文的信息"""
        paper = {}
        
        # 获取 arXiv ID
        arxiv_link = dt.find('a', title='Abstract')
        if arxiv_link:
            arxiv_id = arxiv_link.text.strip().replace('arXiv:', '')
            paper['arxiv_id'] = arxiv_id
            paper['arxiv_url'] = f"https://arxiv.org/abs/{arxiv_id}"
            paper['pdf_url'] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        else:
            return None
        
        # 获取提交类型 (new/cross/replace)
        span_tag = dt.find('span', class_='list-identifier')
        if span_tag:
            # 检查是否有 NEW, CROSS LIST, REPLACED 等标记
            submission_type = "new"
            if "CROSS" in span_tag.get_text().upper():
                submission_type = "cross"
            elif "REPLACE" in span_tag.get_text().upper():
                submission_type = "replace"
            paper['submission_type'] = submission_type
        
        # 获取标题
        title_div = dd.find('div', class_='list-title')
        if title_div:
            title = title_div.get_text().replace('Title:', '').strip()
            # 清理多余的空白字符
            title = re.sub(r'\s+', ' ', title)
            paper['title'] = title
        
        # 获取作者
        authors_div = dd.find('div', class_='list-authors')
        if authors_div:
            authors = []
            for author_link in authors_div.find_all('a'):
                authors.append(author_link.text.strip())
            paper['authors'] = authors
        
        # 获取学科分类
        subjects_div = dd.find('div', class_='list-subjects')
        if subjects_div:
            subjects_text = subjects_div.get_text().replace('Subjects:', '').strip()
            paper['subjects'] = subjects_text
        
        # 获取摘要
        abstract_p = dd.find('p', class_='mathjax')
        if abstract_p:
            abstract = abstract_p.get_text().strip()
            # 清理多余的空白字符
            abstract = re.sub(r'\s+', ' ', abstract)
            paper['abstract'] = abstract
        
        # 获取评论（如果有）
        comments_div = dd.find('div', class_='list-comments')
        if comments_div:
            comments = comments_div.get_text().replace('Comments:', '').strip()
            paper['comments'] = comments
        
        return paper
    
    def filter_by_keywords(self, papers: List[Dict], keywords: List[str]) -> List[Dict]:
        """
        根据关键词筛选论文
        
        Args:
            papers: 论文列表
            keywords: 关键词列表
            
        Returns:
            筛选后的论文列表
        """
        if not keywords:
            return papers
        
        filtered_papers = []
        
        for paper in papers:
            # 在标题和摘要中搜索关键词
            text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
            
            for keyword in keywords:
                if keyword.lower() in text:
                    filtered_papers.append(paper)
                    break
        
        print(f"关键词筛选: {len(papers)} -> {len(filtered_papers)} 篇")
        return filtered_papers
    
    def print_papers(self, papers: List[Dict]):
        """打印论文信息（用于调试）"""
        for i, paper in enumerate(papers, 1):
            print(f"\n{'='*80}")
            print(f"论文 {i}: {paper.get('title', 'N/A')}")
            print(f"ID: {paper.get('arxiv_id', 'N/A')}")
            print(f"作者: {', '.join(paper.get('authors', []))}")
            print(f"类型: {paper.get('submission_type', 'N/A')}")
            print(f"分类: {paper.get('subjects', 'N/A')}")
            print(f"链接: {paper.get('arxiv_url', 'N/A')}")
            print(f"摘要: {paper.get('abstract', 'N/A')}")

