find . -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -exec rm -f {} +
pip uninstall llamafactory -y # 先卸载旧版本
pip install -e .             # 以可编辑模式安装