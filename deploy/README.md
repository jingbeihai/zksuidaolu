# 云服务器 systemd 部署（端口 8003）

## 1. 准备项目目录

若克隆在嵌套目录，先整理：

```bash
cd /opt
mv zksuidaolu/zksuidaolu zksuidaolu-app 2>/dev/null || true
rmdir zksuidaolu 2>/dev/null || true
mv zksuidaolu-app zksuidaolu 2>/dev/null || git clone git@github.com:jingbeihai/zksuidaolu.git zksuidaolu
cd /opt/zksuidaolu
```

## 2. Python 虚拟环境与依赖

```bash
apt update
apt install -y python3 python3-venv python3-pip

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## 3. 环境变量

```bash
cp .env.example .env
nano .env
```

在 `.env` 中设置（**PORT 与 systemd 一致**）：

```env
PORT=8003
DB_HOST=...
DB_PORT=...
DB_USER=...
DB_PASSWORD=...
DB_NAME=...
SECRET_KEY=生产环境请改为随机长字符串
```

## 4. 安装 systemd 服务

```bash
cp deploy/zksuidaolu.service /etc/systemd/system/zksuidaolu.service

# 若项目不在 /opt/zksuidaolu，编辑服务文件中的路径：
# nano /etc/systemd/system/zksuidaolu.service

systemctl daemon-reload
systemctl enable zksuidaolu
systemctl start zksuidaolu
systemctl status zksuidaolu
```

## 5. 常用命令

```bash
systemctl start zksuidaolu      # 启动
systemctl stop zksuidaolu       # 停止
systemctl restart zksuidaolu    # 重启（代码更新后）
systemctl status zksuidaolu     # 状态
journalctl -u zksuidaolu -f     # 实时日志
```

## 6. 防火墙 / 安全组

云厂商控制台放行 **TCP 8003**（若仅内网访问 TV 大屏，可只放行内网 IP）。

```bash
# Ubuntu ufw 示例
ufw allow 8003/tcp
```

## 7. 代码更新后

```bash
cd /opt/zksuidaolu
git pull origin main
source venv/bin/activate && pip install -r requirements.txt && deactivate
systemctl restart zksuidaolu
```

## 8. 访问

- 管理端：`http://服务器IP:8003/login`
- TV 大屏：`http://服务器IP:8003/tv`

默认账号见 `sql/create_admin.py`（部署后需执行初始化脚本创建管理员）。
