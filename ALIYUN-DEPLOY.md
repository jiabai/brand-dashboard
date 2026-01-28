在基于 Debian/Ubuntu 的系统（如 Ubuntu 20.04、22.04 等）上，如果你是通过 apt 安装的 Node.js，可以按照以下步骤彻底卸载它：

✅ 步骤 1：卸载 Node.js 和 npm

sudo apt remove --purge nodejs npm

- remove：移除程序包
- --purge：同时删除配置文件

如果你还安装了 yarn 或其他相关包，也可以一并卸载：
sudo apt remove --purge yarn

✅ 步骤 2：清理不再需要的依赖（可选）

sudo apt autoremove

这会删除因安装 Node.js 而自动安装、现在已无用的依赖包。

✅ 步骤 3：清除残留的软件源（重要！）

很多用户是通过 NodeSource 官方仓库 添加了第三方 apt 源来安装特定版本的 Node.js。如果不删除，后续可能干扰新安装（比如用 nvm 时仍会提示 apt 可升级）。

查看是否添加了 nodesource 源：

ls /etc/apt/sources.list.d/ | grep -i node

常见文件名如：
- nodesource.list
- node_*.list

删除它：

sudo rm /etc/apt/sources.list.d/nodesource.list
或
sudo rm /etc/apt/sources.list.d/node_*  # 小心使用通配符

同时清理 GPG 密钥（可选但推荐）：

列出所有 apt 密钥
sudo apt-key list

找到类似 "NodeSource" 或 "https://deb.nodesource.com" 的条目，记下其 key ID（如 68B9F5E1）
然后删除（示例）：
sudo apt-key del 68B9F5E1

⚠️ 注意：apt-key 在较新 Ubuntu 版本中已被弃用，密钥可能直接放在 /etc/apt/trusted.gpg.d/ 目录下。你可以直接删除：
sudo rm /etc/apt/trusted.gpg.d/nodesource.gpg

✅ 步骤 4：更新 apt 缓存

sudo apt update

确保系统不再引用旧的 Node.js 仓库。

升级所有可升级的包（推荐定期执行）:
sudo apt upgrade -y

清理无用包（可选，保持系统整洁）：
sudo apt autoremove --purge

✅ 验证是否卸载干净

which node
which npm
node -v
npm -v

如果返回“command not found”或空值，说明已成功卸载。

🔁 后续建议

卸载完成后，推荐使用 nvm 安装 Node.js，便于多版本管理和升级，避免再次与系统包管理器冲突。
