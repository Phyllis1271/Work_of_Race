import requests
import json
import csv
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

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
            "home_page": data.get("home_page"),
            "checked_at": datetime.now().isoformat()  # 添加检查时间戳
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
            "license": data.get("license", {}).get("spdx_id"),
            "checked_at": datetime.now().isoformat()  # 添加检查时间戳
        }
    except Exception as e:
        print(f"[GitHub错误] {owner}/{repo}: {str(e)}")
        return None


# ------------------------- 文件操作函数 -------------------------

def load_previous_metadata(file_path: str) -> List[Dict]:
    """加载历史元数据"""
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载历史元数据失败: {str(e)}")
        return []


def save_to_json(data: List[Dict], output_path: str) -> None:
    """保存为JSON文件"""
    try:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
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


# ------------------------- 版本比较函数 -------------------------

def compare_metadata(old_data: List[Dict], new_data: List[Dict]) -> List[Dict]:
    """
    比较新旧元数据，返回更新日志
    返回格式: [
        {
            "source": "pypi/github",
            "name": 包名,
            "change_type": "新增/版本更新/仓库更新/移除",
            "old_value": 旧值,
            "new_value": 新值,
            "check_time": 检查时间
        }
    ]
    """
    updates = []
    
    # 创建快速查找字典
    old_dict = {(item["source"], item["name"]): item for item in old_data}
    new_dict = {(item["source"], item["name"]): item for item in new_data}

    # 检测更新和新增
    for key, new_item in new_dict.items():
        if key not in old_dict:
            updates.append({
                "source": new_item["source"],
                "name": new_item["name"],
                "change_type": "新增",
                "old_value": None,
                "new_value": new_item.get("version") or new_item.get("last_updated"),
                "check_time": new_item["checked_at"]
            })
        else:
            old_item = old_dict[key]
            # PyPI包版本比较
            if new_item["source"] == "pypi" and old_item["version"] != new_item["version"]:
                updates.append({
                    "source": "pypi",
                    "name": new_item["name"],
                    "change_type": "版本更新",
                    "old_value": old_item["version"],
                    "new_value": new_item["version"],
                    "check_time": new_item["checked_at"]
                })
            # GitHub仓库更新比较
            elif new_item["source"] == "github" and old_item["last_updated"] != new_item["last_updated"]:
                updates.append({
                    "source": "github",
                    "name": new_item["name"],
                    "change_type": "仓库更新",
                    "old_value": old_item["last_updated"],
                    "new_value": new_item["last_updated"],
                    "check_time": new_item["checked_at"]
                })

    # 检测移除的包
    for key in old_dict:
        if key not in new_dict:
            updates.append({
                "source": old_dict[key]["source"],
                "name": old_dict[key]["name"],
                "change_type": "移除",
                "old_value": old_dict[key].get("version") or old_dict[key].get("last_updated"),
                "new_value": None,
                "check_time": datetime.now().isoformat()
            })

    return updates


# ------------------------- 主逻辑 -------------------------

def main():
    # 配置参数
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 历史数据路径
    metadata_json = os.path.join(output_dir, "metadata.json")
    previous_data = load_previous_metadata(metadata_json)

    # 目标监控列表
    targets = [
        {"source": "pypi", "name": "numpy"},
        {"source": "pypi", "name": "pandas"},
        {"source": "github", "name": "torvalds/linux"},
        {"source": "github", "name": "python/cpython"}
    ]

    # 收集最新元数据
    current_data = []
    for target in targets:
        try:
            if target["source"] == "pypi":
                metadata = get_pypi_metadata(target["name"])
            elif target["source"] == "github":
                owner, repo = target["name"].split("/")
                metadata = get_github_metadata(owner, repo)
            
            if metadata:
                current_data.append(metadata)
                print(f"成功获取 {target['name']} 元数据")
            else:
                print(f"获取 {target['name']} 元数据失败")
        except Exception as e:
            print(f"处理 {target['name']} 时发生异常: {str(e)}")

    # 保存最新数据
    if current_data:
        save_to_json(current_data, metadata_json)
        save_to_csv(current_data, os.path.join(output_dir, "metadata.csv"))

    # 比较数据并生成报告
    update_report = compare_metadata(previous_data, current_data)
    if update_report:
        print("\n=== 更新检测报告 ===")
        report_path = os.path.join(output_dir, f"update_report_{datetime.now().strftime('%Y%m%d%H%M')}.json")
        save_to_json(update_report, report_path)
        
        # 控制台输出简要报告
        for item in update_report:
            print(f"[{item['change_type']}] {item['name']}:")
            if item["old_value"]:
                print(f"  旧值: {item['old_value']}")
            print(f"  新值: {item['new_value']}\n")
    else:
        print("\n没有检测到任何更新")


if __name__ == "__main__":
    main()
