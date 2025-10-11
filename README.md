## Crypto Prices Dashboard (Flask + CoinGecko)

版本：`1.3.20251010.001`

使用 CoinGecko 实时价格 + 自定义字段，管理代币并展示到表格。

### 功能
- 配置任意 CoinGecko 代币 ID（如 `bitcoin`、`ethereum`）
- 后台管理页面添加/删除代币，并填写自定义信息（融资、代币经济学、Vesting 等）
- 前台表格自动每分钟刷新显示最新价格和你的自定义字段
 - 新增管理员登录，只有管理员可访问管理页面；首页新增支持打款信息
 - 优化：income based price=income valuation/total supply，且当 financing/income based price 大于现价时，显示为红色；UTC 时钟显示完整年月日
 - 安全：启用 CSRF 保护、登录限速/失败锁定（5 次失败锁 5 分钟）、会话 Cookie 安全参数
 - 性能：为接口增加 Cache-Control/ETag/Last-Modified，增加 CoinGecko 重试回退；新增 /healthz 健康检查与自定义错误页
- UI：新增站点 logo；首页版本号左侧展示 logo；浏览器标签页 favicon 使用同款 icon（无文字）
- 稳定性：修复 CSRF 保护阻塞 GET 请求问题；增加全面错误处理与日志记录；启动时健康检查与优雅降级
- **v1.3 新功能**：
  - 🎨 **深色模式**：支持明暗主题切换，自动保存用户偏好
  - 📱 **移动端优化**：响应式设计，触摸友好的界面
  - 🔍 **搜索过滤**：实时搜索代币名称/ID，按价格变化和市值过滤
  - 📊 **数据导出**：一键导出CSV格式数据
  - 🎯 **UI现代化**：使用CSS变量，更好的视觉层次和交互体验
- **v1.2 新功能**：
  - 🚨 **价格监控**：自动监控代币价格，低于融资价格/收入价格时邮件提醒
  - 📧 **邮件通知**：HTML格式邮件，详细的价格对比信息
  - ⏰ **定时检查**：每10分钟自动检查一次价格
  - 🔔 **智能提醒**：24小时内不重复发送相同提醒
  - ⚙️ **自定义冷却**：支持0.5h-24h多种冷却时间选项
- **v1.3 新功能**：
  - 🔃 **表格排序**：点击列头按升序/降序排序，支持所有数值列
  - 📊 **统计面板**：显示监控代币数、平均变化、涨跌分布、总市值
  - 🎯 **优化报告**：全面的功能检查和优化建议文档

### 本地运行
1. Python 3.10+
2. 安装依赖并初始化数据库：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   pip install -r requirements.txt
   python init_db.py
   ```
3. 开发环境启动：
   ```bash
   python app.py
   ```
   打开 `http://127.0.0.1:5000`

### 生产部署（Gunicorn + Nginx + systemd）
1. 服务器安装依赖：`python3-venv`、`nginx`。
2. 代码放到如 `/opt/crypto_prices/`，创建虚拟环境并安装依赖：
   ```bash
   python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
   python init_db.py
   ```
3. 使用 Gunicorn 启动（示例）：
   ```bash
   .venv/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app
   ```
4. Nginx 反向代理示例：
   ```nginx
   server {
       listen 80;
       server_name your.domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
5. 配置 systemd（可选）：`/etc/systemd/system/crypto_prices.service`
   ```ini
   [Unit]
   Description=Crypto Prices Dashboard
   After=network.target

   [Service]
   WorkingDirectory=/opt/crypto_prices
   ExecStart=/opt/crypto_prices/.venv/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app
   Restart=always
   User=www-data
   Group=www-data

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now crypto_prices

### 管理员配置
- 在服务器设置环境变量：
  - `SECRET_KEY`：Flask 会话密钥
  - `ADMIN_USERNAME`：管理员用户名（默认 `admin`）
  - 二选一：
    - `ADMIN_PASSWORD`：明文密码（开发用）
    - `ADMIN_PASSWORD_HASH`：使用 `werkzeug.security.generate_password_hash` 生成的哈希

### 首页打款信息
- 已在首页显示：
  - ERC20 地址：`0x12c7c8c992e74674c6311a182ab72dc2f0a9d13f`
  - Solana 地址：`7FEHSHCUVcXfMAmqrxmUKtbzBqZ3finTLnTQfSJDBkLL`
   ```

### DNS 与 CDN
- 在 Cloudns 添加你的域名 A 记录指向 VPS 公网 IP
- 在 Cloudflare 将站点接入（可选开启代理加速/安全）

### API 速率说明
本项目每分钟请求一次 CoinGecko 市场数据，尊重其速率限制即可。

### 结构
- `app.py`：Flask 应用与路由
- `templates/`：前台与管理页模板
- `init_db.py`：首次初始化数据库
- `requirements.txt`：依赖


