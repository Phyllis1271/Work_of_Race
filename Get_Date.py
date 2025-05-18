import requests
import json
import csv
import os
from typing import Dict, List,Optional


# ------------------------- 元数据获取函数 -------------------------

def get_pypi_metadata(package_name: str) -> Optional[Dict]:
    """获取PyPI包元数据"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()["info"]
        return {
            "source": "pypi",
            "name": data["name"],
            "version": data["version"],
            "author": data.get("author"),
            "home_page": data.get("home_page")
        }
    except Exception as e:
        print(f"[PyPI错误] {package_name}: {str(e)}")
        return None


def get_github_metadata(owner: str, repo: str, token: str = None) -> Optional[Dict]:
    """获取GitHub仓库元数据"""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "source": "github",
            "name": f"{owner}/{repo}",
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "last_updated": data["updated_at"],
            "license": data.get("license", {}).get("spdx_id")
        }
    except Exception as e:
        print(f"[GitHub错误] {owner}/{repo}: {str(e)}")
        return None


# ------------------------- 文件输出函数 -------------------------

def save_to_json(data: List[Dict], output_path: str) -> None:
    """保存为JSON文件"""
    try:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"数据已保存至JSON文件: {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"JSON保存失败: {str(e)}")


def save_to_csv(data: List[Dict], output_path: str) -> None:
    """保存为CSV文件"""
    if not data:
        return

    try:
        keys = data[0].keys()
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"数据已保存至CSV文件: {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"CSV保存失败: {str(e)}")


# ------------------------- 主逻辑 -------------------------

def main():
    # 配置要获取的包列表
    targets = [
        {"source": "pypi", "name": "numpy"},
        {"source": "pypi", "name": "pandas"},
        {"source": "github", "name": "torvalds/linux"},
        {"source": "github", "name": "python/cpython"}
    ]

    # 收集元数据
    metadata = []
    for target in targets:
        if target["source"] == "pypi":
            result = get_pypi_metadata(target["name"])
        elif target["source"] == "github":
            owner, repo = target["name"].split("/")
            result = get_github_metadata(owner, repo)  # 可添加GitHub Token
        if result:
            metadata.append(result)

    # 保存文件（自动创建目录）
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)  # 确保目录存在

    # 同时保存JSON和CSV
    json_path = os.path.join(output_dir, "metadata.json")
    csv_path = os.path.join(output_dir, "metadata.csv")
    save_to_json(metadata, json_path)
    save_to_csv(metadata, csv_path)


if __name__ == "__main__":
    main()
