# BlueOcean Earnings Watch (Windows 桌面应用 MVP)

这是一个面向 **美股财报跟踪** 的桌面应用原型，支持：

- 输入股票代码，加入观察列表。
- 自动获取公司下一个财报发布日期。
- 标注财报时间是 **pre-market / post-market / unknown**。
- 日历视图显示每家公司财报日期。
- 财报日桌面提醒（系统通知）。
- 从配置的 Investor Relations 页面自动抓取财报相关 PDF。
- 对 PDF 做基础词频分析并输出图表。

## UI 设计

遵循你提出的海洋深蓝风格：

- 背景深蓝：`#0B1426` → `#0C1832`
- 强调色：`#3B82F6`
- 文本：白/灰层次
- 卡片：半透明感（MVP 中使用暗色卡片模拟毛玻璃效果）

## 运行方式（源码）

> 建议在 Windows + Python 3.11 环境运行。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

## 打包成 EXE（Windows）

你可以直接执行仓库内脚本：

```bat
scripts\build_windows_exe.bat
```

脚本会自动安装 `pyinstaller` 并打包，输出目录：

- `dist\BlueOceanEarningsWatch\BlueOceanEarningsWatch.exe`

也可以手动打包：

```bat
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name BlueOceanEarningsWatch app/main.py
```

## 数据存储位置

无论源码运行还是 EXE 运行，数据都会写入用户目录（Windows）：

- `C:\Users\<用户名>\AppData\Local\BlueOceanEarningsWatch\watchlist.json`
- `C:\Users\<用户名>\AppData\Local\BlueOceanEarningsWatch\pdfs\`
- `C:\Users\<用户名>\AppData\Local\BlueOceanEarningsWatch\charts\`

这样可避免 EXE 打包后的只读目录问题。

## 使用说明

1. 输入股票代码（例如 `AAPL`）。
2. 可选输入公司的 Investor Relations 页面 URL（用于自动下载 PDF）。
3. 点击“添加到观察列表”。
4. 在右侧日历查看财报日分布。
5. 输入目标代码并点击“下载并分析选中代码PDF”。

## 注意事项

- `yfinance` 数据源可能因公司不同存在延迟或缺失。
- IR 页面结构差异较大，自动 PDF 抓取是启发式策略（按关键词匹配）。
- 词频分析为 MVP 示例，后续可升级为 NER、情绪分析、同比环比可视化等。
