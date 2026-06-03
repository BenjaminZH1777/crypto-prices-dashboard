#!/usr/bin/env python3
"""
网站外部监控脚本 - 检查网站可用性并发送告警
可在本地Mac或其他服务器上运行，独立于VPS
"""

import requests
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import os

# 配置
WEBSITE_URL = os.environ.get("WEBSITE_URL", "https://retailgo2048.com")
MONITOR_URL = os.environ.get("MONITOR_URL", f"{WEBSITE_URL.rstrip('/')}/healthz")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "300"))  # 5分钟检查一次（秒）

# 邮件配置。请通过环境变量配置，避免把邮箱授权码提交到仓库。
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")

# 告警阈值
TIMEOUT_THRESHOLD = 10  # 超时阈值（秒）
RESPONSE_TIME_WARNING = 5  # 响应时间警告阈值（秒）
CONSECUTIVE_FAILURES = 3  # 连续失败次数才发送告警

# 状态文件
STATUS_FILE = os.path.expanduser("~/website_monitor_status.json")


class WebsiteMonitor:
    def __init__(self):
        self.consecutive_failures = 0
        self.last_alert_time = 0
        self.alert_cooldown = 3600  # 1小时内不重复发送离线告警
        self.is_down = False
        self.load_status()
    
    def load_status(self):
        """加载上次的状态"""
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    data = json.load(f)
                    self.consecutive_failures = data.get('consecutive_failures', 0)
                    self.last_alert_time = data.get('last_alert_time', 0)
                    self.is_down = data.get('is_down', False)
        except:
            pass
    
    def save_status(self):
        """保存当前状态"""
        try:
            with open(STATUS_FILE, 'w') as f:
                json.dump({
                    'consecutive_failures': self.consecutive_failures,
                    'last_alert_time': self.last_alert_time,
                    'is_down': self.is_down,
                    'last_check': time.time()
                }, f)
        except:
            pass
    
    def send_alert(self, subject, body):
        """发送告警邮件"""
        if not ALERT_EMAIL or not SMTP_USERNAME or not SMTP_PASSWORD:
            print("⚠️ 邮件配置未完成，跳过发送告警邮件")
            return False

        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = SMTP_USERNAME
            msg['To'] = ALERT_EMAIL
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                {body}
                <hr>
                <p style="color: #666; font-size: 12px;">
                    这是来自网站监控系统的自动通知<br>
                    监控网站：{WEBSITE_URL}<br>
                    检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html', 'utf-8'))
            
            import ssl
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ 告警邮件已发送: {subject}")
            return True
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def check_website(self):
        """检查网站状态"""
        try:
            start_time = time.time()
            response = requests.get(MONITOR_URL, timeout=TIMEOUT_THRESHOLD)
            response_time = time.time() - start_time
            
            # 检查响应状态
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}", response_time
            
            # 检查healthz返回的内容
            try:
                data = response.json()
                if not data.get('app') or not data.get('database'):
                    return False, "健康检查失败", response_time
            except:
                return False, "响应格式错误", response_time
            
            return True, "正常", response_time
            
        except requests.exceptions.Timeout:
            return False, "连接超时", TIMEOUT_THRESHOLD
        except requests.exceptions.ConnectionError:
            return False, "连接失败", 0
        except Exception as e:
            return False, f"未知错误: {str(e)}", 0
    
    def run_check(self):
        """执行一次检查"""
        print(f"\n{'='*60}")
        print(f"🔍 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        is_ok, status_msg, response_time = self.check_website()
        
        if is_ok:
            print(f"✅ 网站正常")
            print(f"📊 响应时间: {response_time:.2f}秒")
            
            # 响应时间告警
            if response_time > RESPONSE_TIME_WARNING:
                print(f"⚠️  响应时间过长（>{RESPONSE_TIME_WARNING}秒）")
            
            # 如果从离线恢复，发送恢复通知
            if self.is_down:
                down_duration = time.time() - self.last_alert_time
                self.send_alert(
                    "✅ 网站已恢复在线 - retailgo2048.com",
                    f"""
                    <div style="background: #d4edda; padding: 20px; border-left: 4px solid #28a745;">
                        <h2 style="color: #155724; margin-top: 0;">✅ 网站已恢复</h2>
                        <p><strong>网站</strong>: {WEBSITE_URL}</p>
                        <p><strong>离线时长</strong>: {int(down_duration/60)} 分钟</p>
                        <p><strong>当前状态</strong>: 正常运行</p>
                        <p><strong>响应时间</strong>: {response_time:.2f}秒</p>
                    </div>
                    """
                )
                self.is_down = False
            
            self.consecutive_failures = 0
            
        else:
            self.consecutive_failures += 1
            print(f"❌ 网站异常: {status_msg}")
            print(f"📊 连续失败: {self.consecutive_failures}/{CONSECUTIVE_FAILURES}")
            
            # 连续失败达到阈值且未在冷却期
            if self.consecutive_failures >= CONSECUTIVE_FAILURES:
                time_since_last_alert = time.time() - self.last_alert_time
                
                if not self.is_down or time_since_last_alert > self.alert_cooldown:
                    # 发送离线告警
                    self.send_alert(
                        "🚨 网站离线告警 - retailgo2048.com",
                        f"""
                        <div style="background: #f8d7da; padding: 20px; border-left: 4px solid #dc3545;">
                            <h2 style="color: #721c24; margin-top: 0;">🚨 网站离线</h2>
                            <p><strong>网站</strong>: {WEBSITE_URL}</p>
                            <p><strong>状态</strong>: {status_msg}</p>
                            <p><strong>检测时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>连续失败次数</strong>: {self.consecutive_failures}</p>
                            <hr>
                            <p><strong>建议操作</strong>:</p>
                            <ol>
                                <li>检查VPS服务器是否在线</li>
                                <li>检查服务状态: systemctl status crypto_prices</li>
                                <li>查看错误日志: journalctl -u crypto_prices -n 50</li>
                                <li>如需重启: systemctl restart crypto_prices</li>
                            </ol>
                        </div>
                        """
                    )
                    self.last_alert_time = time.time()
                    self.is_down = True
        
        self.save_status()
        print(f"{'='*60}")
    
    def run_continuous(self):
        """持续监控模式"""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🔍 网站监控系统已启动                                      ║
╚══════════════════════════════════════════════════════════════╝

监控网站: {WEBSITE_URL}
检查间隔: {CHECK_INTERVAL}秒 ({CHECK_INTERVAL//60}分钟)
告警邮箱: {ALERT_EMAIL}
失败阈值: 连续{CONSECUTIVE_FAILURES}次失败后告警

按 Ctrl+C 停止监控
        """)
        
        try:
            while True:
                self.run_check()
                print(f"\n⏰ {CHECK_INTERVAL//60}分钟后进行下次检查...")
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n🛑 监控已停止")
            self.save_status()


if __name__ == '__main__':
    import sys
    
    monitor = WebsiteMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 单次检查模式
        monitor.run_check()
    else:
        # 持续监控模式
        monitor.run_continuous()
