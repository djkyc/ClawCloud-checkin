
TG_BOT_TOKEN	电报

TG_CHAT_ID	接收消息的 chat_id

如果你要自动更新 GitHub Secrets（可选）

| 变量名                 | 作用                        |
| ------------------- | ------------------------- |
| `REPO_TOKEN`        | 有 `repo` 权限的 GitHub Token |
| `GITHUB_REPOSITORY` | `用户名/仓库名`                 |

GH_ACCOUNTS

```
export GH_ACCOUNTS=

[
  {
    "name": "主号",
    "GH_USERNAME": "your_github_user_1",
    "GH_PASSWORD": "your_github_pass_1",
    "GH_SESSION": "",
    "GH_SESSION_SECRET": "GH_SESSION_1"
  },
  {
    "name": "小号",
    "GH_USERNAME": "your_github_user_2",
    "GH_PASSWORD": "your_github_pass_2",
    "GH_SESSION": "",
    "GH_SESSION_SECRET": "GH_SESSION_2"
  }
]
