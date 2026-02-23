from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from plyer import notification
from tkcalendar import Calendar

from models import WatchItem
from services.analysis_service import PdfAnalysisService
from services.data_provider import EarningsDataProvider
from services.pdf_service import InvestorPdfService
from ui.theme import THEME


APP_NAME = "BlueOceanEarningsWatch"


def _resolve_data_home() -> Path:
    """返回可写的数据目录，兼容源码运行与 EXE 运行。"""
    if sys.platform.startswith("win"):
        root = Path.home() / "AppData" / "Local"
    else:
        root = Path.home() / ".local" / "share"
    data_home = root / APP_NAME
    data_home.mkdir(parents=True, exist_ok=True)
    return data_home


DATA_HOME = _resolve_data_home()
DATA_FILE = DATA_HOME / "watchlist.json"
PDF_DIR = DATA_HOME / "pdfs"
CHART_DIR = DATA_HOME / "charts"


class EarningsDeskApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BlueOcean Earnings Watch")
        self.geometry("1200x760")
        ctk.set_appearance_mode("dark")

        self.provider = EarningsDataProvider()
        self.pdf_service = InvestorPdfService(output_dir=str(PDF_DIR))
        self.analysis_service = PdfAnalysisService(output_dir=str(CHART_DIR))

        self.items: list[WatchItem] = []
        self._build_ui()
        self._load_data()
        self._refresh_table()
        self.after(25_000, self._check_notifications)

    def _build_ui(self) -> None:
        self.configure(fg_color=THEME["bg_top"])

        top = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=16)
        top.pack(fill="x", padx=16, pady=16)

        self.ticker_entry = ctk.CTkEntry(top, width=140, placeholder_text="输入股票代码, 如 AAPL")
        self.ticker_entry.grid(row=0, column=0, padx=10, pady=12)
        self.ir_entry = ctk.CTkEntry(top, width=460, placeholder_text="可选：Investor Relations 页面 URL")
        self.ir_entry.grid(row=0, column=1, padx=10, pady=12)

        ctk.CTkButton(top, text="添加到观察列表", fg_color=THEME["accent"], command=self._add_item).grid(
            row=0, column=2, padx=10, pady=12
        )
        ctk.CTkButton(top, text="更新全部", command=self._refresh_all).grid(row=0, column=3, padx=10, pady=12)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(body, fg_color=THEME["card"], corner_radius=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.table = ctk.CTkTextbox(left, wrap="none", font=("Consolas", 13))
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

        right = ctk.CTkFrame(body, fg_color=THEME["card"], corner_radius=16)
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right, text="财报日历", font=("Microsoft YaHei", 18, "bold")).pack(pady=(12, 6))
        self.calendar = Calendar(
            right,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            background=THEME["bg_bottom"],
            foreground="white",
            headersbackground=THEME["accent"],
            normalbackground=THEME["bg_top"],
            weekendbackground=THEME["bg_top"],
            bordercolor=THEME["bg_bottom"],
        )
        self.calendar.pack(fill="x", padx=12, pady=8)

        self.calendar_hint = ctk.CTkLabel(right, text="选中日期后显示公司", text_color=THEME["text_sub"])
        self.calendar_hint.pack(padx=12, pady=(4, 10))

        ctk.CTkButton(right, text="查看当天公司", command=self._show_day_items).pack(padx=12, pady=6, fill="x")
        ctk.CTkButton(right, text="下载并分析选中代码PDF", command=self._download_and_analyze).pack(
            padx=12, pady=6, fill="x"
        )

        self.target_entry = ctk.CTkEntry(right, placeholder_text="输入要分析的代码, 如 MSFT")
        self.target_entry.pack(padx=12, pady=8, fill="x")

    def _load_data(self) -> None:
        if not DATA_FILE.exists():
            return
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        self.items = [WatchItem.from_dict(x) for x in raw]

    def _save_data(self) -> None:
        DATA_FILE.write_text(
            json.dumps([x.to_dict() for x in self.items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _add_item(self) -> None:
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            messagebox.showwarning("提示", "请输入股票代码")
            return

        try:
            t, name, date_str, session = self.provider.fetch_earnings_info(ticker)
            ir_url = self.ir_entry.get().strip() or None
            item = WatchItem(ticker=t, company_name=name, earnings_date=date_str, market_session=session, ir_url=ir_url)
            item.set_updated_now()
            self.items = [x for x in self.items if x.ticker != ticker] + [item]
            self._save_data()
            self._refresh_table()
            self._paint_calendar_events()
        except Exception as exc:
            messagebox.showerror("错误", f"获取数据失败: {exc}")

    def _refresh_all(self) -> None:
        refreshed = []
        for item in self.items:
            try:
                t, name, date_str, session = self.provider.fetch_earnings_info(item.ticker)
                item.company_name = name
                item.earnings_date = date_str
                item.market_session = session
                item.set_updated_now()
                refreshed.append(t)
            except Exception:
                continue
        self._save_data()
        self._refresh_table()
        self._paint_calendar_events()
        messagebox.showinfo("更新完成", f"已刷新 {len(refreshed)} 个标的")

    def _refresh_table(self) -> None:
        self.table.delete("1.0", "end")
        header = "代码      公司                      财报日期      时段          最后更新\n"
        self.table.insert("end", header)
        self.table.insert("end", "-" * 90 + "\n")
        for i in sorted(self.items, key=lambda x: x.earnings_date or "9999-99-99"):
            row = f"{i.ticker:<8}{i.company_name[:24]:<26}{(i.earnings_date or 'N/A'):<14}{i.market_session:<14}{(i.updated_at or '')}\n"
            self.table.insert("end", row)
        self._paint_calendar_events()

    def _paint_calendar_events(self) -> None:
        self.calendar.calevent_remove("all")
        for item in self.items:
            if item.earnings_date and item.earnings_date != "N/A":
                self.calendar.calevent_create(item.earnings_date, f"{item.ticker} {item.market_session}", tags=item.ticker)

    def _show_day_items(self) -> None:
        day = self.calendar.get_date()
        matched = [x for x in self.items if x.earnings_date == day]
        if not matched:
            self.calendar_hint.configure(text=f"{day} 没有公司发布财报")
            return
        lines = [f"{x.ticker} - {x.company_name} ({x.market_session})" for x in matched]
        self.calendar_hint.configure(text=f"{day}\n" + "\n".join(lines))

    def _check_notifications(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        due = [x for x in self.items if x.earnings_date == today]
        for x in due:
            notification.notify(
                title=f"财报提醒: {x.ticker}",
                message=f"{x.company_name} 今日发布财报 ({x.market_session})",
                timeout=10,
            )
        self.after(25_000, self._check_notifications)

    def _download_and_analyze(self) -> None:
        ticker = self.target_entry.get().strip().upper()
        if not ticker:
            messagebox.showwarning("提示", "请先输入股票代码")
            return

        target = next((x for x in self.items if x.ticker == ticker), None)
        if not target or not target.ir_url:
            messagebox.showwarning("提示", "该代码不存在或未配置 IR URL")
            return

        try:
            pdf = self.pdf_service.download_latest_pdf(ticker, target.ir_url)
            if not pdf:
                messagebox.showwarning("提示", "未找到可下载的财报 PDF 链接")
                return
            chart = self.analysis_service.build_word_frequency_chart(pdf, ticker)
            target.last_pdf_path = pdf
            self._save_data()
            msg = f"PDF 已下载: {pdf}"
            if chart:
                msg += f"\n分析图已生成: {chart}"
            messagebox.showinfo("完成", msg)
        except Exception as exc:
            messagebox.showerror("错误", f"下载或分析失败: {exc}")


if __name__ == "__main__":
    app = EarningsDeskApp()
    app.mainloop()
