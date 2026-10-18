#!/usr/bin/env python3
"""创建简短探索复盘，拒绝覆盖或路径穿越。"""
import argparse
import re
from datetime import date
from pathlib import Path

def session_name(value):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("slug只允许小写字母、数字、单个连字符")
    return value

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("slug",type=session_name)
    p.add_argument("--directory",type=Path,default=Path(__file__).resolve().parents[1]/"sessions")
    a=p.parse_args()
    stamp=date.today().isoformat()
    path=a.directory/(stamp+"-"+a.slug+".md")
    path.parent.mkdir(parents=True,exist_ok=True)
    body=f"""# {stamp} · {a.slug}

session_id: {stamp}-{a.slug}
验证: pending

## 目标与环境
## 原始证据
## 结论与限制
## 可复用方法
## 脚本与文档变更
## 下一步和验收条件
## 同步记录
- Notion:
- GitHub commit:
"""
    with path.open("x",encoding="utf-8") as f:
        f.write(body)
    print(path)

if __name__=="__main__":
    main()
