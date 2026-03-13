#!/usr/bin/env python3
"""
检查当前 Python 解释器路径，用于辅助功能权限配置。
"""

import sys
import os

print("=" * 60)
print("辅助功能权限诊断")
print("=" * 60)

# 当前 Python 解释器路径
python_exe = sys.executable
print(f"\n1. 当前 Python 解释器路径:")
print(f"   {python_exe}")

# 如果是虚拟环境
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print(f"\n2. 检测到虚拟环境:")
    print(f"   虚拟环境路径: {sys.prefix}")
    print(f"   基础 Python: {sys.base_prefix if hasattr(sys, 'base_prefix') else sys.real_prefix}")

# 运行方式
print(f"\n3. 启动命令:")
print(f"   {sys.argv[0]}")

print(f"\n4. 你需要给以下程序授权辅助功能权限:")
print(f"   ➡️  {python_exe}")

print("\n" + "=" * 60)
print("授权步骤:")
print("=" * 60)
print("""
1. 打开 系统设置 → 隐私与安全 → 辅助功能
2. 点击左下角的 "+" 按钮
3. 按 Cmd + Shift + G
4. 粘贴下面的路径:
   
   {python_path}
   
5. 点击 "打开"
6. 确保勾选框是 ✅ 状态
7. 完全退出当前终端/IDE (Cmd+Q)，重新打开
8. 重新运行测试
""".format(python_path=python_exe))

print("=" * 60)
print("快捷命令（复制到终端执行）:")
print("=" * 60)
print(f"""
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
""")
