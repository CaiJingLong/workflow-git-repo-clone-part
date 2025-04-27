# 部分仓库克隆 GitHub Action

这个 GitHub Action 允许你从多个 GitHub 仓库中选择性地克隆部分文件或目录，并将它们合并到以仓库名称命名的分支中。

## 功能特点

- 支持从多个 GitHub 仓库中选择性克隆
- 可以指定每个仓库中需要克隆的具体文件路径或目录
- 自动将克隆的内容合并到以仓库名称命名的分支
- 完全通过配置文件驱动，易于维护和扩展
- 使用 GitHub CLI 和 GitHub Actions 权限进行安全的仓库操作

## 使用方法

### 1. 配置文件

创建一个 YAML 配置文件 `config.yml`，指定需要克隆的仓库和路径：

```yaml
repos:
  - name: "分支名称1"
    url: "https://github.com/用户名/仓库名.git"
    path:
      - "需要克隆的路径1"
      - "需要克隆的路径2"
  
  - name: "分支名称2"
    url: "https://github.com/用户名/仓库名.git"
    path: "单个路径"
```

配置说明：

- `name`: 仓库的描述性名称，**同时也是目标分支的名称**
- `url`: GitHub 仓库的 URL
- `path`: 需要克隆的文件或目录路径，可以是单个字符串或字符串数组

### 2. 手动触发工作流

这个 Action 设计为手动触发，你可以在 GitHub 仓库的 Actions 标签页中找到 "Partial Repository Clone" 工作流并手动运行它。

### 3. 工作流程

工作流执行时会：

1. 检出当前仓库
2. 读取 `config.yml` 配置文件
3. 对于配置中的每个仓库项目：
   - 创建临时目录并克隆或创建以 `name` 为名称的分支
   - 克隆目标仓库并复制指定路径的文件/目录
   - 提交更改并推送到对应的分支

## 权限配置

此工作流使用 GitHub Actions 的内置权限系统进行授权：

```yaml
permissions:
  contents: write  # 允许修改仓库内容
  pull-requests: write  # 如果需要创建 PR，可以添加此权限
```

工作流使用 GitHub CLI (`gh`) 进行仓库操作，这样可以安全地利用 GitHub Actions 的权限系统，无需额外的访问令牌。

## 示例

配置文件示例 (`config.yml`):

```yaml
repos:
  - name: "react-components"
    url: "https://github.com/facebook/react.git"
    path:
      - "packages/react"
      - "packages/react-dom"
  
  - name: "vue-reactivity"
    url: "https://github.com/vuejs/core.git"
    path: "packages/reactivity"
  
  - name: "tensorflow-tutorials"
    url: "https://github.com/tensorflow/tensorflow.git"
    path: "tensorflow/examples/tutorials"
```

使用上述配置，工作流会创建或更新三个分支：`react-components`、`vue-reactivity` 和 `tensorflow-tutorials`，每个分支包含相应仓库中指定的文件和目录。

## 注意事项

- 工作流已配置了必要的权限，无需额外的访问令牌
- 对于大型仓库，部分克隆可以显著减少工作流执行时间
- 如果目标路径已存在，将会被覆盖
- 如果目标分支不存在，将会自动创建

## 许可证

MIT
