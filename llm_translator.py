"""
LLM 翻译和关键词匹配模块
"""
from openai import OpenAI
from typing import List, Dict, Optional
import time
import json
import requests
import os
from pathlib import Path
from datetime import datetime
import threading
from tqdm import tqdm

TRANSLATE_PROMPT = \
"你是一个专业的学术论文翻译助手，请将英文摘要翻译成流畅的中文。**注意**：直接翻译成中文，禁止输出多余文字。\n\n请翻译以下论文摘要：\n\n{abstract}"

MATCH_KEYWORDS_PROMPT = \
"""请判断以下论文是否与这些关键词相关：{keywords_str}

论文标题：{title}
论文摘要：{abstract}
中文摘要：{abstract_zh}

请回答"相关"或"不相关"，并简要说明理由（不超过50字）。
格式：相关/不相关 - 理由

**注意**
只要有一个关键词命中，就算命中

输出："""


class LLMTranslator:
    """使用 LLM 进行翻译和关键词匹配"""
    
    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.translate_prompt = TRANSLATE_PROMPT
        self.match_keywords_prompt = MATCH_KEYWORDS_PROMPT
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base) # 默认使用OpenAI风格调用LLM
    def self_define_receive_llm_output(self, prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        默认使用OpenAI 风格的 LLM 调用，返回模型输出文本
        可按照自己请求 LLM 的方式修改此函数
        """
        client = self.client
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        kwargs = dict(model=self.model, messages=messages, temperature=temperature)
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content.strip()

    def split_papers_for_threading(self, papers: List[Dict]) -> List[List[Dict]]:
        THREADING_NUM = 10
        total_papers_list = []
        paper_per_file = len(papers) // THREADING_NUM
        extra_paper_num = len(papers) % THREADING_NUM
        papers_iter = iter(papers)
        for idx in range(THREADING_NUM):
            tmp_papers_list = []
            for _ in range(paper_per_file + (1 if idx < extra_paper_num else 0)):
                tmp_papers_list.append(next(papers_iter))
            total_papers_list.append(tmp_papers_list)
        return total_papers_list
    
    def translate_abstract(self, abstract: str) -> str:
        """翻译摘要为中文"""
        try:
            return self.self_define_receive_llm_output(self.translate_prompt.format(abstract=abstract))
        except Exception as e:
            print(f"翻译失败: {e}")
            return abstract
    def translate_abstract_thread(self, idx: int, paper_list: List[Dict], date_str: str, category: str):
        """翻译摘要为中文"""
        try:
            save_dir = Path("data") / date_str / category / "tmp"
            save_dir.mkdir(parents=True, exist_ok=True)
            res = []
            with open(os.path.join(save_dir, f"{idx}.json"), "w", encoding="utf-8") as fw:
                for paper in tqdm(paper_list, desc=f"translating Thread {idx}..."):
                    paper["abstract_zh"] = self.translate_abstract(paper["abstract"])
                    res.append(paper)
                json.dump(res, fw, ensure_ascii=False, indent=2)
            print(f"保存成功: {os.path.join(save_dir, f'{idx}.json')}")
        except Exception as e:
            print(f"翻译失败: {e}")
            # return abstract
            exit(1)
    
    def batch_translate(self, papers: List[Dict], date_str: Optional[str] = None, category: str = "cs.CL") -> List[Dict]:
        """
        批量翻译论文摘要并保存到本地
        
        Args:
            papers: 论文列表
            date_str: 日期字符串 (格式: YYYY-M-D)，如果为 None 则不保存
            category: 论文分类 (如: cs.CL, cs.AI)
            
        Returns:
            翻译后的论文列表
        """

        def threading_translate(papers: List[List[Dict]], date_str: str, category: str):
            threadings = []
            for idx, paper_list in enumerate(papers):
                t = threading.Thread(target=self.translate_abstract_thread, args=(idx, paper_list, date_str, category))
                threadings.append(t)
                t.start()
            for t in threadings:
                t.join()

        def merge_all_thread_output():
            res = []
            idx = 0
            target_file = Path("data") / date_str / category / "tmp"
            for file in target_file.glob("*.json"):
                with open(file, "r", encoding="utf-8") as fr:
                    datas = json.load(fr)
                    for data in datas:
                        idx += 1
                        res.append(data)
            output_dir = Path("data") / date_str / category
            with open(output_dir / "papers.json", "w", encoding="utf-8") as fw:
                json.dump(res, fw, ensure_ascii=False, indent=2)
            print(f"✓ 共保存 {idx} 篇论文")
            print(f"✓ 合并所有线程输出完成，保存到 {output_dir / 'papers.json'}")

        # 如果提供了日期，先尝试从本地加载已翻译的数据
        if date_str:
            local_papers = self._load_papers(date_str, category)
            if local_papers:
                print("✓ 本地已有翻译数据，跳过翻译步骤")
                return local_papers
        
        # 本地没有数据，开始翻译
        print(f"开始翻译 {len(papers)} 篇论文摘要...")

        group_papers = self.split_papers_for_threading(papers)
        threading_translate(group_papers, date_str, category)
        print("翻译完成！")
        merge_all_thread_output()

    
    def _save_papers(self, papers: List[Dict], date_str: str, category: str):
        """
        保存论文数据到本地
        
        Args:
            papers: 论文列表
            date_str: 日期字符串 (格式: YYYY-M-D)
            category: 论文分类
        """
        try:
            # 创建目录结构: data/date_str/category
            save_dir = Path("data") / date_str / category
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存为 JSON 文件
            save_path = save_dir / "papers.json"
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 数据已保存到: {save_path}")
            print(f"  共保存 {len(papers)} 篇论文")
            
        except Exception as e:
            print(f"⚠️  保存数据失败: {e}")
    
    def _load_papers(self, date_str: str, category: str) -> Optional[List[Dict]]:
        """
        从本地加载已翻译的论文数据
        
        Args:
            date_str: 日期字符串 (格式: YYYY-M-D)
            category: 论文分类
            
        Returns:
            论文列表，如果文件不存在则返回 None
        """
        try:
            save_path = Path("data") / date_str / category / "papers.json"
            
            if not save_path.exists():
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                papers = json.load(f)
            
            print(f"✓ 从本地加载数据: {save_path}")
            print(f"  共加载 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            print(f"⚠️  加载本地数据失败: {e}")
            return None
    
    def _save_matched_papers(self, papers: List[Dict], date_str: str, category: str, keywords: List[str]):
        """
        保存匹配到的论文数据到本地
        
        Args:
            papers: 匹配到的论文列表
            date_str: 日期字符串 (格式: YYYY-M-D)
            category: 论文分类
            keywords: 关键词列表
        """
        try:
            # 将关键词列表转换为文件夹名称（用下划线连接）
            keywords_folder = "&".join(keywords)
            
            # 创建目录结构: data/date_str/category/keywords
            save_dir = Path("data") / date_str / category / keywords_folder
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存为 JSON 文件
            save_path = save_dir / "matched_papers.json"
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 匹配结果已保存到: {save_path}")
            print(f"  共保存 {len(papers)} 篇相关论文")
            
        except Exception as e:
            print(f"⚠️  保存匹配结果失败: {e}")
    
    def _save_match_log(self, log_entries: List[Dict], date_str: str, category: str, keywords: List[str]):
        """
        保存匹配过程的日志
        
        Args:
            log_entries: 日志条目列表
            date_str: 日期字符串 (格式: YYYY-M-D)
            category: 论文分类
            keywords: 关键词列表
        """
        try:
            # 将关键词列表转换为文件夹名称
            keywords_folder = "&".join(keywords)
            
            # 创建目录结构: data/date_str/category/keywords
            save_dir = Path("data") / date_str / category / keywords_folder
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存为日志文件
            log_path = save_dir / "match_log.json"
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_entries, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 匹配日志已保存到: {log_path}")
            
        except Exception as e:
            print(f"⚠️  保存匹配日志失败: {e}")
    
    def match_single_paper(self, paper: Dict, keywords_str: str) -> tuple:
        """
        匹配单篇论文
        
        Returns:
            (paper, log_entry, is_matched)
        """
        try:
            # 构建输入提示
            input_prompt = self.match_keywords_prompt.format(
                keywords_str=keywords_str, 
                title=paper['title'], 
                abstract=paper['abstract'],
                abstract_zh=paper.get('abstract_zh', '')
            )
            
            # 调用大模型
            result = self.self_define_receive_llm_output(input_prompt)
            
            # 记录日志
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "paper_id": paper.get('arxiv_id', 'unknown'),
                "paper_title": paper['title'],
                "input": input_prompt,
                "output": result,
                "is_matched": result.startswith("相关") if result else False
            }
            
            is_matched = False
            if result and result.startswith("相关"):
                paper["match_reason"] = result.split("-", 1)[1].strip() if "-" in result else "与关键词相关"
                is_matched = True
            
            return (paper, log_entry, is_matched)
            
        except Exception as e:
            # 记录错误日志
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "paper_id": paper.get('arxiv_id', 'unknown'),
                "paper_title": paper['title'],
                "error": str(e),
                "is_matched": False
            }
            return (paper, log_entry, False)
    
    def match_keywords_thread(self, idx: int, paper_list: List[Dict], keywords_str: str, date_str: str, category: str, keywords: List[str]):
        """多线程匹配关键词"""
        try:
            keywords_folder = "&".join(keywords)
            save_dir = Path("data") / date_str / category / keywords_folder / "tmp"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            matched_papers = []
            log_entries = []
            
            for paper in tqdm(paper_list, desc=f"Matching Thread {idx}..."):
                paper_result, log_entry, is_matched = self.match_single_paper(paper, keywords_str)
                log_entries.append(log_entry)
                if is_matched:
                    matched_papers.append(paper_result)
            
            # 保存线程结果
            with open(os.path.join(save_dir, f"matched_{idx}.json"), "w", encoding="utf-8") as fw:
                json.dump(matched_papers, fw, ensure_ascii=False, indent=2)
            
            with open(os.path.join(save_dir, f"log_{idx}.json"), "w", encoding="utf-8") as fw:
                json.dump(log_entries, fw, ensure_ascii=False, indent=2)
            
            print(f"✓ 线程 {idx} 完成: 匹配到 {len(matched_papers)} 篇论文")
            
        except Exception as e:
            print(f"✗ 线程 {idx} 失败: {e}")
            exit(1)
    
    def match_keywords(self, papers: List[Dict], keywords: List[str], date_str: Optional[str] = None, category: str = "cs.CL") -> List[Dict]:
        """
        使用 LLM 匹配关键词相关的论文（支持多线程）
        
        Args:
            papers: 论文列表
            keywords: 关键词列表
            date_str: 日期字符串 (格式: YYYY-M-D)，如果提供则先尝试从本地加载
            category: 论文分类
            
        Returns:
            匹配的论文列表
        """

        def threading_match(paper_groups: List[List[Dict]], keywords_str: str, date_str: str, category: str, keywords: List[str]):
            threadings = []
            for idx, paper_list in enumerate(paper_groups):
                t = threading.Thread(target=self.match_keywords_thread, args=(idx, paper_list, keywords_str, date_str, category, keywords))
                threadings.append(t)
                t.start()
            for t in threadings:
                t.join()
        
        def merge_all_thread_output(date_str: str, category: str, keywords: List[str]):
            keywords_folder = "&".join(keywords)
            tmp_dir = Path("data") / date_str / category / keywords_folder / "tmp"
            output_dir = Path("data") / date_str / category / keywords_folder
            
            all_matched_papers = []
            all_log_entries = []
            
            # 合并匹配结果
            for file in tmp_dir.glob("matched_*.json"):
                with open(file, "r", encoding="utf-8") as fr:
                    papers = json.load(fr)
                    all_matched_papers.extend(papers)
            
            # 合并日志
            for file in tmp_dir.glob("log_*.json"):
                with open(file, "r", encoding="utf-8") as fr:
                    logs = json.load(fr)
                    all_log_entries.extend(logs)
            
            # 保存合并后的结果
            if all_matched_papers:
                with open(output_dir / "matched_papers.json", "w", encoding="utf-8") as fw:
                    json.dump(all_matched_papers, fw, ensure_ascii=False, indent=2)
                print(f"✓ 匹配结果已保存到: {output_dir / 'matched_papers.json'}")
                print(f"  共保存 {len(all_matched_papers)} 篇相关论文")
            
            if all_log_entries:
                with open(output_dir / "match_log.json", "w", encoding="utf-8") as fw:
                    json.dump(all_log_entries, fw, ensure_ascii=False, indent=2)
                print(f"✓ 匹配日志已保存到: {output_dir / 'match_log.json'}")
            
            return all_matched_papers
        
        # 如果提供了日期，先尝试从本地加载已翻译的数据
        if date_str:
            local_papers = self._load_papers(date_str, category)
            if local_papers:
                print("✓ 使用本地已翻译的数据，跳过翻译步骤")
                papers = local_papers
        
        if not papers:
            return []
        
        print(f"开始匹配关键词相关论文...")
        keywords_str = "、".join(keywords)
        
        # 分组并多线程匹配
        paper_groups = self.split_papers_for_threading(papers)
        threading_match(paper_groups, keywords_str, date_str, category, keywords)
        
        print("匹配完成！")
        
        # 合并所有线程的输出
        matched_papers = merge_all_thread_output(date_str, category, keywords)
        
        print(f"找到 {len(matched_papers)} 篇相关论文")
        
        return matched_papers

