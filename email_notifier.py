"""
邮件发送模块
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import time


class EmailNotifier:
    """邮件发送"""
    
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str, receiver_email: str):
        """
        初始化邮件发送器
        
        Args:
            smtp_server: SMTP 服务器地址 (如: smtp.gmail.com, smtp.qq.com)
            smtp_port: SMTP 端口 (通常 465 for SSL, 587 for TLS)
            sender_email: 发件人邮箱
            sender_password: 发件人邮箱密码或授权码
            receiver_email: 收件人邮箱
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email
    
    def send_email(self, subject: str, body: str) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            
        Returns:
            是否发送成功
        """
        try:
            # 创建邮件对象
            message = MIMEMultipart()
            message['From'] = self.sender_email
            message['To'] = self.receiver_email
            message['Subject'] = subject
            
            # 添加邮件正文
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 连接 SMTP 服务器并发送
            if self.smtp_port == 465:
                # SSL 连接
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(message)
            else:
                # TLS 连接
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(message)
            
            print(f"✓ 邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            print(f"✗ 邮件发送失败: {e}")
            return False
    
    def send_all_papers(self, papers: List[Dict], date: str, categories: List[str] = None) -> bool:
        """
        发送所有翻译后的论文
        
        Args:
            papers: 论文列表
            date: 日期
            categories: 论文分类列表
            
        Returns:
            是否发送成功
        """
        if not papers:
            print("没有论文需要发送")
            return False
        
        subject = f"📚 Arxiv 论文推送 - 所有翻译摘要后论文 ({date})"
        
        # 构建邮件正文
        body = f"共找到 {len(papers)} 篇论文\n\n"
        
        # 添加分类信息
        if categories:
            body += f"📂 论文分类: {', '.join(categories)}\n\n"
        
        body += "=" * 80 + "\n\n"
        
        for i, paper in enumerate(papers, 1):
            body += self._format_paper(i, paper)
        
        return self.send_email(subject, body)
    
    def send_matched_papers(self, papers: List[Dict], date: str, keywords: List[str] = None, categories: List[str] = None) -> bool:
        """
        发送匹配到的相关论文
        
        Args:
            papers: 论文列表
            date: 日期
            keywords: 关键词列表
            categories: 论文分类列表
            
        Returns:
            是否发送成功
        """
        if not papers:
            print("没有匹配的论文需要发送")
            return False
        
        subject = f"🎯 Arxiv 论文推送 - 关键词匹配论文 ({date})"
        
        # 构建邮件正文
        body = f"共找到 {len(papers)} 篇相关论文\n\n"
        
        # 添加关键词信息
        if keywords:
            body += f"🔑 匹配关键词: {', '.join(keywords)}\n"
        
        # 添加分类信息
        if categories:
            body += f"📂 论文分类: {', '.join(categories)}\n"
        
        body += "\n" + "=" * 80 + "\n\n"
        
        for i, paper in enumerate(papers, 1):
            body += self._format_paper(i, paper, include_match_reason=True)
        
        return self.send_email(subject, body)
    
    def _format_paper(self, num: int, paper: Dict, include_match_reason: bool = False) -> str:
        """格式化单篇论文信息"""
        template = f"""【论文 {num}】{paper['title']}

👤 作者: {self._format_authors(paper['authors'])}
"""
        
        # 如果是匹配的论文，添加匹配理由
        if include_match_reason and "match_reason" in paper:
            template += f"\n🎯 匹配理由: {paper['match_reason']}\n"
        
        # 中文摘要
        if "abstract_zh" in paper:
            template += f"\n📝 中文摘要: {paper['abstract_zh']}\n"
        
        # 英文摘要
        template += f"\n📝 英文摘要: {paper.get('abstract', '')}\n"
        
        # 链接
        template += f"""
🔗 PDF链接: {paper['pdf_url']}
🔗 Arxiv页面: {paper['arxiv_url']}

{'=' * 80}

"""
        return template
    
    def _format_authors(self, authors: List[str]) -> str:
        """格式化作者列表"""
        if len(authors) <= 3:
            return ', '.join(authors)
        else:
            return ', '.join(authors[:3]) + f" 等 {len(authors)} 人"

