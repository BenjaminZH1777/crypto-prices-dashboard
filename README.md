## Crypto Prices Dashboard (Flask + CoinGecko)

版本：`1.1.20250809.003`

使用 CoinGecko 实时价格 + 自定义字段，管理代币并展示到表格。

### 功能
- 配置任意 CoinGecko 代币 ID（如 `bitcoin`、`ethereum`）
- 后台管理页面添加/删除代币，并填写自定义信息（融资、代币经济学、Vesting 等）
- 前台表格自动每分钟刷新显示最新价格和你的自定义字段
 - 新增管理员登录，只有管理员可访问管理页面；首页新增支持打款信息
 - 优化：income based price=income valuation/total supply，且当 financing/income based price 大于现价时，显示为红色；UTC 时钟显示完整年月日

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


