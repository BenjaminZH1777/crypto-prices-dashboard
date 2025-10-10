#!/bin/bash
# 价格监控设置脚本

echo "=== 加密货币价格监控配置 ==="
echo ""

# 检查是否在VPS上运行
if [ ! -d "/opt/crypto_prices" ]; then
    echo "警告: 似乎不在VPS上运行"
fi

# 提示用户输入邮件配置
read -p "请输入接收提醒的邮箱地址: " ALERT_EMAIL
read -p "请输入发送邮箱地址 (Gmail): " SMTP_USERNAME
read -sp "请输入Gmail应用专用密码: " SMTP_PASSWORD
echo ""

# 设置环境变量
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="$SMTP_USERNAME"
export SMTP_PASSWORD="$SMTP_PASSWORD"
export ALERT_EMAIL="$ALERT_EMAIL"

# 将环境变量写入systemd服务配置
echo "配置systemd服务环境变量..."
cat > /etc/systemd/system/crypto_prices_monitor.service << EOF
[Unit]
Description=Crypto Prices Monitor
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/crypto_prices
Environment="SMTP_SERVER=smtp.gmail.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USERNAME=$SMTP_USERNAME"
Environment="SMTP_PASSWORD=$SMTP_PASSWORD"
Environment="ALERT_EMAIL=$ALERT_EMAIL"
ExecStart=/opt/crypto_prices/.venv/bin/python3 /opt/crypto_prices/price_monitor.py
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 创建定时器
cat > /etc/systemd/system/crypto_prices_monitor.timer << EOF
[Unit]
Description=Crypto Prices Monitor Timer
Requires=crypto_prices_monitor.service

[Timer]
# 每10分钟执行一次
OnCalendar=*:0/10
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 重新加载systemd
systemctl daemon-reload

# 启用并启动定时器
systemctl enable crypto_prices_monitor.timer
systemctl start crypto_prices_monitor.timer

echo ""
echo "✅ 价格监控配置完成！"
echo ""
echo "监控服务状态："
systemctl status crypto_prices_monitor.timer --no-pager
echo ""
echo "查看监控日志："
echo "  tail -f /opt/crypto_prices/price_monitor.log"
echo ""
echo "手动测试监控："
echo "  systemctl start crypto_prices_monitor"
echo ""

