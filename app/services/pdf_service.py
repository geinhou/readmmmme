from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


class InvestorPdfService:
    """从 IR 页面抓取并下载可能的财报 PDF。"""

    KEYWORDS = ("earnings", "quarter", "results", "presentation")

    def __init__(self, output_dir: str = "app/storage/pdfs") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_latest_pdf(self, ticker: str, ir_url: str) -> Optional[str]:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(ir_url, headers=headers, timeout=15)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        candidates = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").strip().lower()
            href_lower = href.lower()
            if ".pdf" in href_lower and any(k in (text + href_lower) for k in self.KEYWORDS):
                candidates.append(href)

        if not candidates:
            return None

        target = requests.compat.urljoin(ir_url, candidates[0])
        pdf_res = requests.get(target, headers=headers, timeout=30)
        pdf_res.raise_for_status()

        safe = re.sub(r"[^A-Za-z0-9_-]", "_", ticker.upper())
        out_path = self.output_dir / f"{safe}_latest_earnings.pdf"
        out_path.write_bytes(pdf_res.content)
        return str(out_path)
