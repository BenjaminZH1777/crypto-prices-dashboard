#!/bin/bash
# 在Mac上配置网站监控为后台服务

echo "🔍 配置Mac本地网站监控服务"
echo "========================================"

PROJECT_DIR="/Users/benjaminzh/Desktop/pythonwork/crypto_prices"
PLIST_FILE="$HOME/Library/LaunchAgents/com.crypto.website-monitor.plist"

# 确保脚本可执行
chmod +x "$PROJECT_DIR/website_monitor.py"

# 创建LaunchAgent配置
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.crypto.website-monitor</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$PROJECT_DIR/website_monitor.py</string>
        <string>--once</string>
    </array>
    
    <key>StartInterval</key>
    <integer>300</integer>
    
    <key>StandardOutPath</key>
    <string>$HOME/website_monitor.log</string>
    
    <key>StandardErrorPath</key>
    <string>$HOME/website_monitor_error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ 配置文件已创建: $PLIST_FILE"

# 加载服务
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

echo "✅ 监控服务已启动"
echo ""
echo "📋 管理命令："
echo "  启动监控: launchctl load ~/Library/LaunchAgents/com.crypto.website-monitor.plist"
echo "  停止监控: launchctl unload ~/Library/LaunchAgents/com.crypto.website-monitor.plist"
echo "  查看日志: tail -f ~/website_monitor.log"
echo "  查看错误: tail -f ~/website_monitor_error.log"
echo ""
echo "🔍 监控已启动，每5分钟检查一次"
echo "如果网站离线，会发送邮件到: $ALERT_EMAIL"

