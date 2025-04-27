#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import shutil
import tempfile
import subprocess
from pathlib import Path

def main():
    # 配置文件固定为 config.yml
    config_path = "config.yml"

    print(f"读取配置文件: {config_path}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if "repos" not in config:
        raise ValueError("配置文件中缺少 repos 节点")

    # 获取当前仓库信息
    github_repository = os.environ.get('GITHUB_REPOSITORY')
    if not github_repository:
        raise ValueError("无法获取 GITHUB_REPOSITORY 环境变量")
    
    # 获取 GitHub Token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        # 尝试从 github.token 环境变量获取
        github_token = os.environ.get('INPUT_TOKEN')
        if not github_token:
            print("警告: 无法获取 GITHUB_TOKEN，将使用默认认证方式")

    # 处理每个仓库
    for repo in config["repos"]:
        name = repo.get("name")
        url = repo.get("url")
        paths = repo.get("path", [])
        
        if not name or not url or not paths:
            print(f"警告: 仓库配置不完整，跳过: {repo}")
            continue
        
        # 使用 name 字段作为目标分支
        target_branch = name
        print(f"处理仓库: {name} ({url}), 目标分支: {target_branch}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"创建临时目录: {temp_dir}")
        
        try:
            # 检查分支是否存在
            check_branch_cmd = ["gh", "api", 
                               f"repos/{github_repository}/branches/{target_branch}", 
                               "--silent", "-f"]
            branch_exists = subprocess.run(check_branch_cmd, capture_output=True).returncode == 0
            
            if branch_exists:
                print(f"分支 {target_branch} 已存在，克隆该分支")
                # 使用 GitHub CLI 克隆特定分支
                subprocess.run(
                    ["gh", "repo", "clone", f"{github_repository}", temp_dir, "--", 
                     "--branch", target_branch, "--single-branch", "--depth", "1"],
                    check=True
                )
            else:
                print(f"分支 {target_branch} 不存在，克隆默认分支并创建新分支")
                # 克隆默认分支
                subprocess.run(
                    ["gh", "repo", "clone", f"{github_repository}", temp_dir, "--", 
                     "--depth", "1"],
                    check=True
                )
                # 创建新分支
                subprocess.run(
                    ["git", "checkout", "-b", target_branch],
                    cwd=temp_dir,
                    check=True
                )
            
            # 配置 Git 用户
            subprocess.run(
                ["git", "config", "user.name", "github-actions[bot]"], 
                cwd=temp_dir, 
                check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], 
                cwd=temp_dir, 
                check=True
            )
            
            # 如果有 GitHub Token，配置远程仓库 URL 使用 token 认证
            if github_token:
                remote_url = f"https://x-access-token:{github_token}@github.com/{github_repository}.git"
                subprocess.run(
                    ["git", "remote", "set-url", "origin", remote_url],
                    cwd=temp_dir,
                    check=True
                )
            
            # 为这个仓库创建临时目录
            repo_temp_dir = tempfile.mkdtemp()
            
            try:
                # 克隆仓库
                print(f"克隆仓库 {url} 到临时目录")
                subprocess.run(
                    ["git", "clone", "--depth", "1", url, repo_temp_dir],
                    check=True
                )
                
                # 确保路径是列表
                if isinstance(paths, str):
                    paths = [paths]
                
                # 复制指定路径到目标目录
                for path in paths:
                    src_path = os.path.join(repo_temp_dir, path)
                    if not os.path.exists(src_path):
                        print(f"警告: 路径不存在，跳过: {path}")
                        continue
                    
                    dest_path = os.path.join(temp_dir, path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    if os.path.isdir(src_path):
                        print(f"复制目录: {path}")
                        if os.path.exists(dest_path):
                            shutil.rmtree(dest_path)
                        shutil.copytree(src_path, dest_path)
                    else:
                        print(f"复制文件: {path}")
                        shutil.copy2(src_path, dest_path)
            
            finally:
                # 清理仓库临时目录
                shutil.rmtree(repo_temp_dir)
            
            # 提交更改
            subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
            
            # 检查是否有更改需要提交
            status = subprocess.run(
                ["git", "status", "--porcelain"], 
                cwd=temp_dir, 
                capture_output=True, 
                text=True,
                check=True
            )
            
            if status.stdout.strip():
                # 有更改需要提交
                subprocess.run(
                    ["git", "commit", "-m", f"Update with partial clone from {name}"],
                    cwd=temp_dir,
                    check=True
                )
                
                # 使用标准 git push 命令推送更改
                print(f"推送更改到 {target_branch} 分支")
                
                # 打印 git remote -v 信息，用于调试
                subprocess.run(
                    ["git", "remote", "-v"],
                    cwd=temp_dir,
                    check=True
                )
                
                # 推送更改
                push_cmd = ["git", "push", "origin", target_branch]
                
                # 如果是新分支，添加 -u 参数
                if not branch_exists:
                    push_cmd.insert(2, "-u")
                
                subprocess.run(
                    push_cmd,
                    cwd=temp_dir,
                    check=True
                )
                
                print(f"仓库 {name} 的部分克隆完成并已推送")
            else:
                print(f"仓库 {name} 没有需要提交的更改")
        
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    
    print("所有仓库处理完成")

if __name__ == "__main__":
    main()
