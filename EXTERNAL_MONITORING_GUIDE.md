# 🔍 外部监控配置完整指南

---

## 🎯 监控方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **UptimeRobot** | 专业、免费、全球检测 | 需注册账号 | ⭐⭐⭐⭐⭐ |
| **自建脚本（Mac）** | 完全控制、已配置好 | 依赖Mac开机 | ⭐⭐⭐⭐ |
| **两者都用** | 双重保障 | - | ⭐⭐⭐⭐⭐ |

---

## 方案A：UptimeRobot（推荐）

### 📋 配置步骤（5分钟）

#### 步骤1：注册账号
1. 访问：https://uptimerobot.com
2. 点击"Free Sign Up"
3. 填写信息：
   - Email: `402541430@qq.com`（或任意邮箱）
   - Password: 设置一个密码
4. 验证邮箱

#### 步骤2：添加监控
1. 登录后，点击"**+ Add New Monitor**"
2. 填写信息：
   ```
   Monitor Type: HTTP(s)
   Friendly Name: Crypto Prices Dashboard
   URL (or IP): https://retailgo2048.com/healthz
   Monitoring Interval: Every 5 minutes
   ```
3. 点击"Create Monitor"

#### 步骤3：配置告警
1. 点击"**My Settings**"
2. 在"Alert Contacts"添加：
   - Type: E-mail
   - Email: `402541430@qq.com`
3. 验证邮箱（点击验证邮件中的链接）

#### 步骤4：完成
- ✅ 监控立即生效
- ✅ 网站离线会收到邮件
- ✅ 恢复在线也会收到通知

### 📊 UptimeRobot功能

**免费版包含**：
- ✅ 50个监控点
- ✅ 5分钟检查间隔
- ✅ 无限邮件通知
- ✅ 2个月历史数据
- ✅ 公开状态页面
- ✅ 响应时间统计

**查看统计**：
- 可用性百分比（30天）
- 平均响应时间
- 离线次数和时长
- 响应时间趋势图

---

## 方案B：自建监控（已配置好）

### 🚀 快速启动（1分钟）

#### 在Mac上运行

**选项1：前台运行（测试用）**
```bash
cd /Users/benjaminzh/Desktop/pythonwork/crypto_prices
python3 website_monitor.py
```

按`Ctrl+C`停止

**选项2：后台服务（推荐）**
```bash
cd /Users/benjaminzh/Desktop/pythonwork/crypto_prices
chmod +x setup_mac_monitor.sh
./setup_mac_monitor.sh
```

### 📋 管理命令

```bash
# 启动监控
launchctl load ~/Library/LaunchAgents/com.crypto.website-monitor.plist

# 停止监控
launchctl unload ~/Library/LaunchAgents/com.crypto.website-monitor.plist

# 查看监控日志
tail -f ~/website_monitor.log

# 查看错误日志
tail -f ~/website_monitor_error.log

# 手动测试一次
cd /Users/benjaminzh/Desktop/pythonwork/crypto_prices
python3 website_monitor.py --once
```

### 工作原理

```
您的Mac电脑（开机状态）
    ↓ 每5分钟
访问 https://retailgo2048.com/healthz
    ↓
检查响应状态
    ↓
┌─────────────────┬─────────────────┐
│  正常           │   异常          │
│  记录日志       │   连续3次失败   │
│                 │   发送邮件告警  │
└─────────────────┴─────────────────┘
```

### 监控内容

- ✅ HTTP状态码（期望200）
- ✅ 响应时间（>5秒告警）
- ✅ healthz内容验证
- ✅ 数据库状态检查
- ✅ 连续失败检测

### 告警机制

**触发条件**：
- 连续3次检查失败（15分钟）
- 才发送离线告警
- 避免误报

**冷却机制**：
- 1小时内不重复发送离线告警
- 恢复时立即通知

---

## 方案C：双重监控（最佳）

### 推荐配置

1. **UptimeRobot**（主要）
   - 专业、稳定、免费
   - 全球多地检测
   - 不依赖您的设备

2. **Mac本地监控**（辅助）
   - 备用监控
   - 本地日志记录
   - 可自定义逻辑

### 优势
- ✅ 双重保障
- ✅ UptimeRobot离线也有Mac监控
- ✅ 更全面的监控覆盖

---

## 📧 告警邮件示例

### 离线告警
```
主题：🚨 网站离线告警 - retailgo2048.com

【网站离线】

网站: https://retailgo2048.com
状态: 连接超时
检测时间: 2025-10-11 15:30:25
连续失败次数: 3

建议操作:
1. 检查VPS服务器是否在线
2. 检查服务状态: systemctl status crypto_prices
3. 查看错误日志: journalctl -u crypto_prices -n 50
4. 如需重启: systemctl restart crypto_prices
```

### 恢复通知
```
主题：✅ 网站已恢复在线 - retailgo2048.com

【网站已恢复】

网站: https://retailgo2048.com
离线时长: 15 分钟
当前状态: 正常运行
响应时间: 0.18秒
```

---

## 🎯 推荐方案

### 我的建议：**UptimeRobot + Mac监控**

**理由**：
1. **UptimeRobot**：
   - ✅ 专业可靠
   - ✅ 免费
   - ✅ 不依赖您的设备
   - ✅ 5分钟配置

2. **Mac监控**：
   - ✅ 已经配置好
   - ✅ 1分钟启动
   - ✅ 备用方案
   - ✅ 本地日志

**配置时间**：
- UptimeRobot: 5分钟
- Mac监控: 1分钟
- **总计：6分钟** ⏱️

---

## 🚀 立即开始

### 现在就可以做：

#### 1. 启动Mac本地监控（1分钟）
```bash
cd /Users/benjaminzh/Desktop/pythonwork/crypto_prices
chmod +x setup_mac_monitor.sh
./setup_mac_monitor.sh
```

**立即生效**！Mac会每5分钟检查网站。

#### 2. 注册UptimeRobot（5分钟）
- 访问：https://uptimerobot.com
- 注册 → 添加监控 → 验证邮箱
- **完成**！

---

## 📝 测试验证

### 测试监控是否工作

**方法1：手动运行测试**
```bash
cd /Users/benjaminzh/Desktop/pythonwork/crypto_prices
python3 website_monitor.py --once
```

应该看到：
```
✅ 网站正常
📊 响应时间: 0.18秒
```

**方法2：模拟离线**
临时关闭VPS上的服务，看是否收到告警：
```bash
# 不建议在生产环境测试
# 可以在UptimeRobot控制台测试告警
```

---

## 🎁 额外福利

### 监控统计仪表盘

配置UptimeRobot后，您会获得：
- 📊 可用性统计（今天/7天/30天）
- 📈 响应时间趋势图
- 🌍 全球检测位置
- 📋 离线历史记录
- 🔗 公开状态页面（可分享）

### 示例统计
```
30天可用性: 99.98%
平均响应时间: 185ms
离线次数: 0次
总检查次数: 8,640次
```

---

## ❓ 常见问题

### Q1: Mac关机了监控还工作吗？
**A**: Mac监控不工作，但UptimeRobot继续工作（推荐两者都配置）

### Q2: 会不会收到很多邮件？
**A**: 不会。只有离线时才发送，且有冷却机制

### Q3: 监控会影响网站性能吗？
**A**: 不会。每5分钟1次请求，对服务器影响可忽略

### Q4: 需要付费吗？
**A**: 不需要。UptimeRobot免费版完全够用

---

## 🎯 下一步

**现在您可以**：

1. **立即启动Mac监控**（已配置好）
   ```bash
   cd /Users/benjaminzh/Desktop/pythonwork/crypto_prices
   ./setup_mac_monitor.sh
   ```

2. **注册UptimeRobot**（5分钟）
   - https://uptimerobot.com
   - 按上面步骤配置

3. **或者两者都配置**（最佳）

需要我帮您执行Mac监控的配置吗？

