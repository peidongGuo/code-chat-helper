# code-chat-helper
RHINO Coding Helper （ https://chat.openai.com/g/g-48MTFZf5N-rhino-coding-helper-zhong-wen-ban ） 将GPT接入Git，为程序员提供软件开发方面的帮助，包括 Issue Fix 和 PR Review 等。主要功能如下：
*   **GitHub Issue 分析和修复建议**：当用户提出与特定 GitHub Issue 相关的问题，或寻求帮助以修复某个 Issue 时，RHINO 会自动获取该 Issue 的详细描述，并分析相关的代码文件。基于这些信息，提供解决方案、代码优化建议或实现新功能的方法，进而生成相关代码。
*   **代码文件解读**：对于用户需要帮助理解或评审的特定代码文件，RHINO 可以获取该文件的最新内容并提供详细解读。RHINO 能够将多个代码文件结合起来进行解读，还会指出代码文件中可能存在的问题，特别是当用户要求对特定代码文件进行检查或评审时。
*   **Pull Request (PR) 审查**：当用户要求对Pull Request 进行审查时，RHINO会获取 PR 的详细信息，包括代码变更和 PR 描述。如果 PR 提到相关 Issues，RHINO也会获取这些 Issue 的信息。然后RHINO会结合 PR 描述、相关 Issue和代码变更，对PR进行全面的审查，供审查结果。如果有必要，RHINO还会获取 PR 中每个被修改文件的完整内容，以便进行全面审查。
*   **提交评论到 PR 或 Issue**：如果用户需要，RHINO还可以向特定的 PR 或 Issue 提交评论。在提交之前，RHINO会向用户展示评论内容供审核。
在进行这些任务时，用户还可以会RHINO进行讨论，以便获得更准确的结果。

我们正在更新该项目的功能，敬请持续关注，以下视频反应较新的阶段性进展：

https://github.com/OpenRHINO/code-chat-reviewer/assets/20229719/40af494c-28d7-498f-acd6-fcf953137c9f

## 核心组件
1. **pr_review.py**:
   - 使用 Flask 创建 web 应用。
   - 集成 GitHub API，获取 Pull Request 的详细信息和代码变更。
   - 调用 OpenAI API 使用 GPT 模型生成审查意见。
   - 进行请求签名验证，确保 Webhook 安全。
   - 记录日志并以 JSON 格式输出，便于追踪和调试。
   - 使用 MongoDB 存储和检索审查对话和评论。
   - 将审查结果转换成中文并发布在 GitHub 上。

2. **conversation.py**:
   - 实现对Review结果进行后续讨论的交互界面。
   - 提供登录验证，确保只有授权用户能够访问和交互。
   - 提供界面供用户查看和参与审查对话。
   - 与 MongoDB 交互，保存和加载对话。
   - 调用 GPT 模型生成对用户输入的响应，并保存。

3. **template.html**:
   - HTML 模板文件，conversation.py用其构建用户界面。
   - 显示审查对话历史的对话框。
   - 用户输入问题或评论的输入框。
   - 发送消息和预设查询的按钮。
   - 通过 JavaScript 实现的动态内容加载和更新。

## 工作流程
1. GitHub 上的 Pull Request 发生变更时（新建、更新或重新开放），GitHub 通过 Webhook 向 `pr_review.py` 发送请求。
2. `pr_review.py` 接收请求，验证签名，从 GitHub API 获取 Pull Request 详细信息。
3. 使用这些信息构建 GPT 提示，调用 OpenAI API 生成审查意见。
4. 审查结果存储在 MongoDB 中，可通过 `conversation.py` 提供的界面查看和讨论。
5. 用户通过 `template.html` 界面发送消息，消息用于调用 GPT 模型生成响应，并更新对话历史。

## 安装与部署
1. **克隆仓库**:
git clone https://github.com/OpenRHINO/code-chat-reviewer.git

2. **设置环境变量**:
- 设置必要的环境变量，例如 `OPENAI_API_KEY`（OpenAI 的 API 密钥）和 `GITHUB_TOKEN`（GitHub 的访问令牌）。

3. **部署 MongoDB**:
- 可以使用 Kubernetes 配置文件 `kubernetes/mongodb.yaml` 部署 MongoDB。

4. **构建和运行 Docker 容器**:
- 使用提供的 Dockerfile 构建容器。
- 运行容器，确保 MongoDB 和应用服务能够正常通信。

5. **Kubernetes 部署**:
- 如果使用 Kubernetes，可以参考 `kubernetes` 目录下的配置文件进行部署。

## 使用说明
- 配置 GitHub 仓库的 Webhook，指向部署的服务地址。
- 在 PR 创建或更新时，会自动触发code-chat-reviewer进行代码审查。
- code-chat-reviewer提交的审查结果里包含一个Web页面链接，用户可以通过提供的 Web 界面与 AI 进行交互，获取更多的审查意见或进行对话。


