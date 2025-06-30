pandas>=2.0
numpy>=1.24
openpyxl>=3.1
pyarrow>=12.0
python-dotenv>=1.0
loguru>=0.7
requests>=2.31
tqdm>=4.65
pytest>=7.3
python-dateutil>=2.8

#initialization
#0 - 1 memo

#0 -2 data







[project]
name = "actuarial-decrement-dashboard"
version = "0.1.0"
description = "精算减量表数据分析平台"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
dependencies = [
    "pandas>=2.0",
    "numpy>=1.24",
    "pyarrow>=12.0",
    "loguru>=0.7"
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
pythonpath = [
    "."
]
testpaths = [
    "tests"
]
