# 对话报告（2025-08-09）

版本：1.0.20250809.001

## 目标
搭建一个可在网页端展示 CoinGecko 实时价格并可自定义代币与信息的应用，支持管理后台，能在 VPS 上通过域名访问，并上传代码到 GitHub。

## 主要改动与成果
- 复用并完善现有项目 `pythonwork/crypto_prices`：
  - 新增/恢复生产必需文件：`.gitignore`、`README.md`、`init_db.py`、`wsgi.py`。
  - 与你在 GitHub 的模板进行对接（参考：[templates 目录](https://github.com/BenjaminZH1777/crypto_tracker/tree/main/templates)），替换前台模板并新增 `static/script.js`。
  - 数据模型 `Coin` 增加投资组合字段：`buy_price`、`amount`。
  - 新增接口：`/api/prices`（返回名称、当前价格、买入价、数量与盈亏），保留原有 `/api/data`、`/api/coin_ids`、`/manage`、`/manage/delete/<id>`。
  - 将 Flask 应用静态与模板目录显式配置：`static/` 与 `templates/`。
  - 简单数据库“迁移”逻辑：`init_db.py` 检测缺失列并通过 `ALTER TABLE` 补全。

## 使用与部署
### 本地（Mac）
1. 虚拟环境与依赖：
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `python init_db.py`
2. 开发运行：`python app.py` 或 `gunicorn -w 2 -b 127.0.0.1:8000 wsgi:application`

### Git 与 GitHub
- 初始化 git 并提交；为推送配置 SSH 密钥；远程仓库建议：`github.com/BenjaminZH1777/crypto-prices-dashboard`。
- 本次版本设定：`1.0.20250809.001`（同时写入 `VERSION` 并创建 git tag）。

### VPS（Ubuntu 22.04）
1. 安装依赖：`apt install -y python3-venv python3-pip git nginx`
2. 目录：`/opt/crypto_prices`
3. 拉取与初始化：
   - `git clone https://github.com/BenjaminZH1777/crypto-prices-dashboard.git .`
   - `python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt`
   - `./.venv/bin/python init_db.py`
4. 前台试跑（可选）：`./.venv/bin/gunicorn -w 2 -b 127.0.0.1:8000 wsgi:application`
5. 创建 systemd 服务 `crypto_prices.service`，反代 Nginx 到 127.0.0.1:8000。

### 域名与证书
- 域名：`retailgo2048.ip-ddns.com`。
- DNS 在 Cloudns 指向 VPS 公网 IP。
- HTTPS：`certbot --nginx -d retailgo2048.ip-ddns.com --agree-tos -m <你的邮箱> --redirect --no-eff-email`。

## 页面与接口
- 前台：`/`（表格：名称、当前价、买入价、数量、盈亏；30 秒刷新）
- 管理页：`/manage`（配置 CoinGecko `id`、买入价、数量和自定义信息）
- 数据接口：`/api/prices`、`/api/data`、`/api/coin_ids`

## 参考
- GitHub 模板来源（前端结构对接）：[templates 目录](https://github.com/BenjaminZH1777/crypto_tracker/tree/main/templates)

## 下一步建议
- 增加分页与搜索；
- 增加自定义刷新频率、法币选择；
- 引入 Alembic 做正式迁移；
- 增加用户认证与权限控制（如将管理页加上密码）。


