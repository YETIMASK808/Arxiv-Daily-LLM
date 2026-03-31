"""
飞书消息推送模块
"""
import requests
import time
import hmac
import hashlib
import base64
from typing import List, Dict


class FeishuNotifier:
    """飞书消息推送"""
    
    def __init__(self, webhook: str, secret: str = ""):
        self.webhook = webhook
        self.secret = secret
    
    def _sign(self, timestamp: int) -> str:
        """生成飞书加签"""
        if not self.secret:
            return ""
        
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    def send_markdown(self, title: str, text: str) -> bool:
        """发送 Markdown 格式消息"""
        headers = {'Content-Type': 'application/json'}
        
        # 构建消息体
        # data = {
        #     "msg_type": "interactive",
        #     "card": {
        #         "header": {
        #             "title": {
        #                 "tag": "plain_text",
        #                 "content": title
        #             },
        #             "template": "blue"
        #         },
        #         "elements": [
        #             {
        #                 "tag": "markdown",
        #                 "content": text
        #             }
        #         ]
        #     }
        # }

        data = {
                "msg_type":"text",
                "content":
                    {"title": title,
                    "text": text}
                }
        
        # 如果配置了加签，添加签名
        if self.secret:
            timestamp = int(time.time())
            sign = self._sign(timestamp)
            data["timestamp"] = str(timestamp)
            data["sign"] = sign
        
        try:
            response = requests.post(self.webhook, json=data, headers=headers)
            result = response.json()
            
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print("✓ 飞书消息发送成功")
                return True
            else:
                print(f"✗ 飞书消息发送失败: {result}")
                return False
        except Exception as e:
            print(f"✗ 飞书消息发送异常: {e}")
            return False
    
    def send_papers(self, papers: List[Dict], date: str, keywords: List[str] = None, categories: List[str] = None) -> bool:
        """
        发送论文列表（使用简单文本模板）
        
        Args:
            papers: 论文列表
            date: 日期
            keywords: 关键词列表
            categories: 论文分类列表
        """
        if not papers:
            print("没有论文需要发送")
            return False
        
        # 飞书消息有长度限制，分批发送
        batch_size = 5
        success = True
        
        total_batches = (len(papers) + batch_size - 1) // batch_size
        
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            if total_batches > 1:
                title = f"📚 Arxiv 论文推送 ({date}) - 第 {batch_num}/{total_batches} 批"
            else:
                title = f"📚 Arxiv 论文推送 ({date})"
            
            # 构建消息文本
            message = f"共找到 {len(papers)} 篇相关论文，本批次 {len(batch)} 篇\n\n"
            
            # 添加关键词信息（只在第一批显示）
            if i == 0:
                if keywords:
                    message += f"🔑 匹配关键词: {', '.join(keywords)}\n"
                if categories:
                    message += f"📂 论文分类: {', '.join(categories)}\n"
                message += "\n"
            
            message += "=" * 50 + "\n\n"
            
            for j, paper in enumerate(batch, 1):
                paper_num = i + j
                message += self._format_paper(paper_num, paper)
            
            # 发送文本消息
            if not self._send_text(title, message):
                success = False
            
            # 避免发送过快
            if i + batch_size < len(papers):
                time.sleep(1)
        
        return success
    
    def _format_paper(self, num: int, paper: Dict) -> str:
        """格式化单篇论文信息"""
        template = f"""【论文 {num}】{paper['title']}

👤 作者: {self._format_authors(paper['authors'])}

🎯 匹配理由: {paper.get('match_reason', '与关键词相关')}

📝 摘要: {paper.get('abstract_zh', paper.get('abstract', ''))}

🔗 PDF链接: {paper['pdf_url']}
🔗 Arxiv页面: {paper['arxiv_url']}

{'=' * 50}

"""
        return template
    
    def _format_authors(self, authors: List[str]) -> str:
        """格式化作者列表"""
        if len(authors) <= 3:
            return ', '.join(authors)
        else:
            return ', '.join(authors[:3]) + f" 等 {len(authors)} 人"
    
    def _format_abstract(self, abstract: str) -> str:
        """格式化摘要（限制长度）"""
        max_length = 300
        if len(abstract) > max_length:
            return abstract[:max_length] + "..."
        return abstract
    
    def _send_text(self, title: str, text: str) -> bool:
        """发送纯文本消息"""
        headers = {'Content-Type': 'application/json'}
        
        # 组合标题和内容
        full_text = f"{title}\n\n{text}"
        
        data = {
            "msg_type": "text",
            "content": {
                "text": full_text
            }
        }
        
        # 如果配置了加签
        if self.secret:
            timestamp = int(time.time())
            sign = self._sign(timestamp)
            data["timestamp"] = str(timestamp)
            data["sign"] = sign
        
        try:
            response = requests.post(self.webhook, json=data, headers=headers)
            result = response.json()
            
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print("✓ 飞书消息发送成功")
                return True
            else:
                print(f"✗ 飞书消息发送失败: {result}")
                return False
        except Exception as e:
            print(f"✗ 飞书消息发送异常: {e}")
            return False
    
    def send_rich_text(self, papers: List[Dict], date: str) -> bool:
        """发送富文本格式消息（备用方案）"""
        if not papers:
            print("没有论文需要发送")
            return False
        
        headers = {'Content-Type': 'application/json'}
        
        # 构建富文本内容
        content = []
        content.append([{"tag": "text", "text": f"共找到 {len(papers)} 篇相关论文\n\n"}])
        
        for i, paper in enumerate(papers[:10], 1):  # 限制前10篇
            content.append([
                {"tag": "text", "text": f"{i}. "},
                {"tag": "a", "text": paper['title'], "href": paper['arxiv_url']},
                {"tag": "text", "text": "\n"}
            ])
            
            if "match_reason" in paper:
                content.append([
                    {"tag": "text", "text": f"匹配理由: {paper['match_reason']}\n"}
                ])
            
            content.append([{"tag": "text", "text": "\n"}])
        
        data = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"Arxiv 论文推送 ({date})",
                        "content": content
                    }
                }
            }
        }
        
        # 如果配置了加签
        if self.secret:
            timestamp = int(time.time())
            sign = self._sign(timestamp)
            data["timestamp"] = str(timestamp)
            data["sign"] = sign
        
        try:
            response = requests.post(self.webhook, json=data, headers=headers)
            result = response.json()
            
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print("✓ 飞书消息发送成功")
                return True
            else:
                print(f"✗ 飞书消息发送失败: {result}")
                return False
        except Exception as e:
            print(f"✗ 飞书消息发送异常: {e}")
            return False


# test = FeishuNotifier("https://www.feishu.cn/flow/api/trigger-webhook/051a44361519894f660fd4a2f2fa35dd", "2026-01-01")
# test_paper = {
#     "title": "test",
#     "authors": ["lishunran"],
#     "match_reason": "test",
#     "abstract_zh": "test" * 10000 + "<end>",
#     "pdf_url": "https://www.feishu.cn/",
#     "arxiv_url": "https://www.feishu.cn/"
# }
# test.send_papers([test_paper], "2026-01-01")
