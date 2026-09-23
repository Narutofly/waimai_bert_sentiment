"""让 pytest 把项目根目录加入 sys.path，使 `import training.xxx` / `import common.xxx` 可用。

放在根目录而不是 tests/ 下，是为了让测试从任意工作目录运行都能找到项目模块。
"""
