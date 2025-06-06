# 部署到 Render.com 操作指南

本文档将指导您如何将此 Python Flask 项目部署到 [Render](https://render.com/)。

## 准备工作

在开始之前，请确保您已经将所有最新的代码（包括 `app.py`, `requirements.txt`, `products.csv` 以及 `static` 和 `templates` 文件夹）推送到了您的 GitHub 或 GitLab 仓库。Render 将会从您的代码仓库中拉取代码进行部署。

## 在 Render 上创建 Web 服务

1.  **登录 Render**: 打开 [Render Dashboard](https://dashboard.render.com/) 并登录。
2.  **新建服务**: 点击 **"New +"** 按钮，然后选择 **"Web Service"**。
3.  **连接代码仓库**:
    *   选择您的 GitHub 或 GitLab 账户。
    *   找到并选择包含此项目的代码仓库。
    *   点击 **"Connect"**。

## 配置 Web 服务

在接下来的配置页面中，填写以下信息：

1.  **Name**: 为您的服务起一个独一无二的名字（例如 `my-chat-app`）。

2.  **Region**: 选择一个离您的用户最近的服务器地理位置（例如 `Ohio (US East)`）。

3.  **Branch**: 选择您想要部署的分支（通常是 `main` 或 `master`）。

4.  **Root Directory**: 保持默认的空白即可，除非您的项目文件不在仓库的根目录。

5.  **Runtime**: 选择 **`Python 3`**。

6.  **Build Command**: 这是安装项目依赖的命令。填写：
    ```bash
    pip install -r requirements.txt
    ```

7.  **Start Command**: 这是启动您的 Web 应用的命令。填写：
    ```bash
    gunicorn app:app
    ```

8.  **Instance Type**: 对于个人项目或测试，**`Free`** 套餐通常已经足够。

## 添加环境变量

您的应用需要 API 密钥等敏感信息。这些信息应该通过环境变量来配置，而不是硬编码在代码里。

1.  在配置页面的 **"Environment"** 部分，点击 **"Add Environment Variable"**。
2.  添加以下环境变量：
    *   **Key**: `DEEPSEEK_API_KEY`
    *   **Value**: 填入您的 DeepSeek API 密钥。
    *   **Key**: `PYTHON_VERSION`
    *   **Value**: `3.10.6` (或者您本地开发使用的 Python 版本，确保版本兼容性)
    *   **Key**: `APP_ENV`
    *   **Value**: `production` (这会激活您在 `app.py` 中设置的生产环境逻辑)

    *如果您有其他需要配置的环境变量，也请一并添加。*

## 完成创建

1.  检查所有配置项是否正确。
2.  点击页面底部的 **"Create Web Service"** 按钮。

Render 将会开始拉取您的代码，执行构建命令 (`pip install...`)，然后执行启动命令 (`gunicorn...`)。您可以在 Render 的日志界面看到实时的部署进度。

部署成功后，Render 会为您提供一个 `*.onrender.com` 的公开访问网址。您可以通过这个网址访问您的在线聊天应用。

---
**部署后检查:**
*   访问您的 `onrender.com` 网址，确保应用可以正常打开。
*   尝试发送一条消息，检查聊天功能是否正常工作。
*   在 Render 的 "Logs" 标签页中查看应用日志，排查可能出现的错误。