#!/usr/bin/env python3
"""
价格监控脚本 - 监控代币价格并发送邮件提醒
当代币价格低于融资价格或收入价格时，发送邮件通知
"""

import os
import sys
import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径到Python路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import app, db, Coin, SystemSettings, AlertHistory, get_cached_market_data

# 配置日志（带轮转）
from logging.handlers import RotatingFileHandler

# 创建日志处理器
file_handler = RotatingFileHandler(
    BASE_DIR / 'price_monitor.log',
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# 邮件配置（使用环境变量）
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', '')  # 接收提醒的邮箱

# 提醒冷却时间（小时）- 从数据库读取，默认24小时
# 这个值会在check_prices()函数中从数据库动态读取
ALERT_COOLDOWN_HOURS = 24  # 默认值

# 提醒记录存储
ALERT_HISTORY_FILE = BASE_DIR / 'alert_history.txt'


class PriceAlert:
    """价格提醒类型"""
    FINANCING_PRICE = 'financing_price'
    INCOME_PRICE = 'income_price'


def load_alert_history():
    """加载提醒历史记录"""
    history = {}
    if ALERT_HISTORY_FILE.exists():
        try:
            with open(ALERT_HISTORY_FILE, 'r') as f:
                for line in f:
                    parts = line.strip().split('|')
                    if len(parts) == 3:
                        coin_id, alert_type, timestamp = parts
                        key = f"{coin_id}_{alert_type}"
                        history[key] = float(timestamp)
        except Exception as e:
            logger.error(f"加载提醒历史失败: {e}")
    return history


def save_alert_history(history):
    """保存提醒历史记录"""
    try:
        with open(ALERT_HISTORY_FILE, 'w') as f:
            for key, timestamp in history.items():
                coin_id, alert_type = key.rsplit('_', 1)
                f.write(f"{coin_id}|{alert_type}|{timestamp}\n")
    except Exception as e:
        logger.error(f"保存提醒历史失败: {e}")


def should_send_alert(coin_id, alert_type, history, cooldown_hours):
    """判断是否应该发送提醒（检查冷却时间）"""
    key = f"{coin_id}_{alert_type}"
    if key not in history:
        return True
    
    last_alert_time = history[key]
    time_passed = time.time() - last_alert_time
    hours_passed = time_passed / 3600
    
    return hours_passed >= cooldown_hours


def send_email(subject, body_html):
    """发送邮件提醒"""
    if not ALERT_EMAIL or not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("邮件配置未完成，跳过发送邮件")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL
        
        # 添加HTML内容
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        # QQ邮箱需要使用SSL连接
        if 'qq.com' in SMTP_SERVER.lower():
            # QQ邮箱使用SSL端口465
            import ssl
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context, timeout=30)
            try:
                server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            finally:
                try:
                    server.quit()
                except:
                    pass
        else:
            # 其他邮箱使用TLS
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        
        logger.info(f"邮件发送成功: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"发送邮件失败: {e}", exc_info=True)
        return False


def format_price(price):
    """格式化价格显示"""
    if price is None:
        return 'N/A'
    return f'${price:.6f}'


def create_alert_email(alerts):
    """创建价格提醒邮件内容"""
    subject = f"🚨 代币价格提醒 - {len(alerts)}个代币触发提醒"
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f44336; color: white; padding: 20px; border-radius: 5px; }}
            .alert {{ background: #fff3cd; border-left: 4px solid #ff9800; padding: 15px; margin: 15px 0; }}
            .alert-financing {{ border-left-color: #e91e63; }}
            .alert-income {{ border-left-color: #9c27b0; }}
            .coin-name {{ font-size: 18px; font-weight: bold; color: #1976d2; }}
            .price-info {{ margin: 10px 0; }}
            .price {{ font-size: 16px; font-weight: bold; }}
            .price-current {{ color: #f44336; }}
            .price-target {{ color: #666; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            td {{ padding: 8px; }}
            .label {{ font-weight: bold; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 加密货币价格提醒</h1>
                <p>检测到 {len(alerts)} 个代币价格低于目标价格</p>
                <p>检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
    """
    
    for alert in alerts:
        alert_class = 'alert-financing' if alert['type'] == PriceAlert.FINANCING_PRICE else 'alert-income'
        alert_type_name = '融资价格' if alert['type'] == PriceAlert.FINANCING_PRICE else '收入价格'
        
        html += f"""
            <div class="alert {alert_class}">
                <div class="coin-name">{alert['coin_name']} ({alert['coin_id']})</div>
                <table>
                    <tr>
                        <td class="label">当前价格:</td>
                        <td class="price price-current">{format_price(alert['current_price'])}</td>
                    </tr>
                    <tr>
                        <td class="label">{alert_type_name}:</td>
                        <td class="price price-target">{format_price(alert['target_price'])}</td>
                    </tr>
                    <tr>
                        <td class="label">价差:</td>
                        <td class="price" style="color: #f44336;">
                            {format_price(alert['current_price'] - alert['target_price'])} 
                            ({alert['percentage']:.2f}%)
                        </td>
                    </tr>
                </table>
                <p><strong>提醒原因:</strong> 当前价格低于{alert_type_name}</p>
            </div>
        """
    
    html += f"""
            <div class="footer">
                <p>这是来自加密货币价格监控系统的自动提醒邮件</p>
                <p>监控网站: <a href="https://retailgo2048.com">https://retailgo2048.com</a></p>
                <p>如需停止接收提醒，请联系管理员</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, html


def check_prices():
    """检查所有代币价格并发送提醒"""
    logger.info("开始价格检查...")
    
    with app.app_context():
        try:
            # 从数据库读取冷却时间设置
            cooldown_hours_str = SystemSettings.get_setting('alert_cooldown_hours', '24')
            try:
                cooldown_hours = float(cooldown_hours_str)
            except:
                cooldown_hours = 24.0
            
            logger.info(f"当前提醒冷却时间: {cooldown_hours} 小时")
            
            # 获取市场数据
            market_data, last_fetch, ttl = get_cached_market_data(ttl_seconds=300)
            
            # 获取所有配置的代币
            coins = Coin.query.all()
            
            if not coins:
                logger.info("没有配置代币，跳过检查")
                return
            
            # 加载提醒历史
            alert_history = load_alert_history()
            alerts_to_send = []
            
            for coin in coins:
                market = market_data.get(coin.coin_id)
                if not market:
                    logger.warning(f"未找到 {coin.coin_id} 的市场数据")
                    continue
                
                current_price = market.get('current_price')
                if current_price is None:
                    continue
                
                coin_name = market.get('name', coin.coin_id)
                
                # 计算融资价格（与app.py逻辑一致）
                computed_fbp = None
                computed_ibp = None
                try:
                    total_supply = market.get('total_supply')
                    found_raises = coin.found_raises
                    investor_pct = coin.investor_percentage
                    if total_supply and total_supply > 0 and found_raises and investor_pct:
                        investor_fraction = investor_pct if investor_pct <= 1 else investor_pct / 100.0
                        denom = total_supply * investor_fraction
                        if denom:
                            computed_fbp = float(found_raises) / float(denom)
                    # 计算收入价格 = income_valuation / total_supply
                    income_valuation = coin.income_valuation
                    if total_supply and total_supply > 0 and income_valuation:
                        computed_ibp = float(income_valuation) / float(total_supply)
                except Exception as e:
                    logger.error(f"计算价格失败 {coin.coin_id}: {e}")
                    computed_fbp = None
                    computed_ibp = None
                
                # 使用计算后的价格，如果没有则使用数据库中的值
                financing_based_price = computed_fbp if computed_fbp is not None else coin.financing_based_price
                income_based_price = computed_ibp if computed_ibp is not None else coin.income_based_price
                
                # 检查融资价格
                if financing_based_price and current_price < financing_based_price:
                    if should_send_alert(coin.coin_id, PriceAlert.FINANCING_PRICE, alert_history, cooldown_hours):
                        percentage = ((current_price - financing_based_price) / financing_based_price) * 100
                        alerts_to_send.append({
                            'coin_id': coin.coin_id,
                            'coin_name': coin_name,
                            'current_price': current_price,
                            'target_price': financing_based_price,
                            'type': PriceAlert.FINANCING_PRICE,
                            'percentage': percentage
                        })
                        logger.info(f"触发融资价格提醒: {coin_name} 当前${current_price:.6f} < 融资${financing_based_price:.6f}")
                
                # 检查收入价格
                if income_based_price and current_price < income_based_price:
                    if should_send_alert(coin.coin_id, PriceAlert.INCOME_PRICE, alert_history, cooldown_hours):
                        percentage = ((current_price - income_based_price) / income_based_price) * 100
                        alerts_to_send.append({
                            'coin_id': coin.coin_id,
                            'coin_name': coin_name,
                            'current_price': current_price,
                            'target_price': income_based_price,
                            'type': PriceAlert.INCOME_PRICE,
                            'percentage': percentage
                        })
                        logger.info(f"触发收入价格提醒: {coin_name} 当前${current_price:.6f} < 收入${income_based_price:.6f}")
            
            # 发送提醒邮件
            if alerts_to_send:
                subject, body = create_alert_email(alerts_to_send)
                email_sent = send_email(subject, body)
                email_error = None if email_sent else "邮件发送失败"
                
                # 保存提醒历史到数据库和文件
                current_time = time.time()
                for alert in alerts_to_send:
                    # 保存到数据库
                    try:
                        alert_record = AlertHistory(
                            coin_id=alert['coin_id'],
                            coin_name=alert['coin_name'],
                            alert_type=alert['type'],
                            current_price=alert['current_price'],
                            target_price=alert['target_price'],
                            price_diff=alert['current_price'] - alert['target_price'],
                            price_diff_pct=alert['percentage'],
                            triggered_at=current_time,
                            email_sent=email_sent,
                            email_error=email_error
                        )
                        db.session.add(alert_record)
                    except Exception as e:
                        logger.error(f"保存提醒历史到数据库失败: {e}")
                
                try:
                    db.session.commit()
                except Exception as e:
                    logger.error(f"提交数据库事务失败: {e}")
                    db.session.rollback()
                
                # 更新文件历史（用于冷却检查）
                if email_sent:
                    for alert in alerts_to_send:
                        key = f"{alert['coin_id']}_{alert['type']}"
                        alert_history[key] = current_time
                    save_alert_history(alert_history)
                    logger.info(f"发送了 {len(alerts_to_send)} 个价格提醒")
                else:
                    logger.warning(f"检测到 {len(alerts_to_send)} 个提醒，但邮件发送失败")
            else:
                logger.info("没有需要发送的提醒")
                
        except Exception as e:
            logger.error(f"价格检查失败: {e}", exc_info=True)


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("价格监控脚本启动")
    logger.info(f"SMTP服务器: {SMTP_SERVER}:{SMTP_PORT}")
    logger.info(f"接收邮箱: {ALERT_EMAIL if ALERT_EMAIL else '未配置'}")
    logger.info(f"默认提醒冷却时间: {ALERT_COOLDOWN_HOURS} 小时（将从数据库读取实际设置）")
    logger.info("=" * 60)
    
    check_prices()
    
    logger.info("价格监控脚本执行完成")

