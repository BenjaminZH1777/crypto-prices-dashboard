# 🚨 价格监控功能说明

## 功能概述

自动监控代币价格，当价格低于设定的目标价格时，通过邮件发送提醒。

### 监控规则

- **融资价格提醒**：当代币当前价格 < 融资价格时，发送邮件
- **收入价格提醒**：当代币当前价格 < 收入价格时，发送邮件

### 特性

- ✅ 自动定时检查（每10分钟）
- ✅ 邮件HTML格式提醒
- ✅ 智能提醒（24小时内不重复发送相同提醒）
- ✅ 详细的监控日志
- ✅ 支持多个代币同时监控

## 📋 配置步骤

### 1. 准备Gmail账号

为了安全，建议创建一个专用的Gmail账号用于发送提醒邮件。

#### 获取Gmail应用专用密码：

1. 访问 https://myaccount.google.com/
2. 选择"安全性"
3. 开启"两步验证"
4. 在"两步验证"下方找到"应用专用密码"
5. 选择"邮件"和"其他设备"
6. 生成密码（16位，如：`abcd efgh ijkl mnop`）
7. 保存这个密码（去掉空格：`abcdefghijklmnop`）

### 2. 在VPS上配置

连接到您的VPS：

```bash
ssh root@156.244.46.107
cd /opt/crypto_prices
```

#### 方法A：使用配置脚本（推荐）

```bash
chmod +x setup_monitor.sh
./setup_monitor.sh
```

按提示输入：
- 接收提醒的邮箱
- 发送邮箱（Gmail）
- Gmail应用专用密码

#### 方法B：手动配置环境变量

编辑systemd服务文件：

```bash
vi /etc/systemd/system/crypto_prices_monitor.service
```

添加环境变量：

```ini
[Unit]
Description=Crypto Prices Monitor
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/crypto_prices
Environment="SMTP_SERVER=smtp.gmail.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USERNAME=your_email@gmail.com"
Environment="SMTP_PASSWORD=your_app_password"
Environment="ALERT_EMAIL=alert_recipient@example.com"
ExecStart=/opt/crypto_prices/.venv/bin/python3 /opt/crypto_prices/price_monitor.py
User=root

[Install]
WantedBy=multi-user.target
```

创建定时器：

```bash
vi /etc/systemd/system/crypto_prices_monitor.timer
```

```ini
[Unit]
Description=Crypto Prices Monitor Timer

[Timer]
OnCalendar=*:0/10
Persistent=true

[Install]
WantedBy=timers.target
```

启用服务：

```bash
systemctl daemon-reload
systemctl enable crypto_prices_monitor.timer
systemctl start crypto_prices_monitor.timer
```

### 3. 验证配置

#### 查看定时器状态

```bash
systemctl status crypto_prices_monitor.timer
```

#### 查看监控日志

```bash
tail -f /opt/crypto_prices/price_monitor.log
```

#### 手动运行测试

```bash
systemctl start crypto_prices_monitor
```

## 📊 监控邮件示例

当触发价格提醒时，您会收到如下格式的邮件：

**主题**：🚨 代币价格提醒 - 2个代币触发提醒

**内容**：
- 代币名称和ID
- 当前价格（红色高亮）
- 目标价格（融资价格或收入价格）
- 价差和百分比
- 提醒原因

## 🔧 高级配置

### 修改检查频率

编辑定时器配置：

```bash
vi /etc/systemd/system/crypto_prices_monitor.timer
```

修改 `OnCalendar` 参数：
- 每5分钟：`OnCalendar=*:0/5`
- 每10分钟：`OnCalendar=*:0/10`
- 每30分钟：`OnCalendar=*:0/30`
- 每小时：`OnCalendar=hourly`

### 修改提醒冷却时间

编辑监控脚本：

```bash
vi /opt/crypto_prices/price_monitor.py
```

修改 `ALERT_COOLDOWN_HOURS` 变量（默认24小时）

### 查看提醒历史

```bash
cat /opt/crypto_prices/alert_history.txt
```

## 🐛 故障排查

### 邮件发送失败

1. **检查Gmail应用专用密码**
   - 确保开启了两步验证
   - 使用应用专用密码，不是账号密码
   - 密码不包含空格

2. **检查环境变量**
   ```bash
   systemctl show crypto_prices_monitor.service | grep Environment
   ```

3. **查看详细日志**
   ```bash
   journalctl -u crypto_prices_monitor.service -f
   ```

### 监控未运行

1. **检查定时器状态**
   ```bash
   systemctl status crypto_prices_monitor.timer
   ```

2. **检查定时器列表**
   ```bash
   systemctl list-timers crypto_prices_monitor.timer
   ```

3. **重启定时器**
   ```bash
   systemctl restart crypto_prices_monitor.timer
   ```

## 📝 使用示例

### 场景1：监控代币跌破融资价格

1. 在网站管理页面添加代币
2. 填写融资价格（Financing Based Price）
3. 系统每10分钟检查一次
4. 当价格低于融资价格时，收到邮件
5. 24小时内不会重复发送相同提醒

### 场景2：同时监控融资价格和收入价格

1. 在管理页面同时填写：
   - Financing Based Price：融资价格
   - Income Based Price：收入价格
2. 当价格低于任一价格时都会收到提醒
3. 两种提醒独立计算冷却时间

## 📧 联系支持

如遇问题，请检查：
1. 监控日志：`/opt/crypto_prices/price_monitor.log`
2. 系统日志：`journalctl -u crypto_prices_monitor.service`
3. 邮件配置是否正确

---

**提示**：为了测试监控功能，可以在管理页面设置一个明显高于当前价格的融资价格，然后手动运行监控查看是否收到邮件。

