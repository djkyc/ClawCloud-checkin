
TG_BOT_TOKEN	电报

TG_CHAT_ID	接收消息的 chat_id

如果你要自动更新 GitHub Secrets（可选）

| 变量名                 | 作用                        |
| ------------------- | ------------------------- |
| `REPO_TOKEN`        | 有 `repo` 权限的 GitHub Token |
| `GITHUB_REPOSITORY` | `用户名/仓库名`                 |

GH_ACCOUNTS

```
export GH_ACCOUNTS='[
  {
    "name": "主号",
    "username": "github_user_1",
    "password": "github_pass_1",
    "session": "",
    "secret": "GH_SESSION_1"
  },
  {
    "name": "小号",
    "username": "github_user_2",
    "password": "github_pass_2",
    "session": "",
    "secret": "GH_SESSION_2"
  }
]'
