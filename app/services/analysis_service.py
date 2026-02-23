from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Optional

from matplotlib import pyplot as plt
from pypdf import PdfReader


class PdfAnalysisService:
    """从 PDF 提取高频词并输出柱状图。"""

    STOP_WORDS = {
        "the", "and", "to", "of", "in", "for", "a", "is", "on", "with",
        "our", "we", "that", "as", "this", "be", "by", "at", "are", "from",
    }

    def __init__(self, output_dir: str = "app/storage/charts") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_word_frequency_chart(self, pdf_path: str, ticker: str) -> Optional[str]:
        reader = PdfReader(pdf_path)
        text_chunks = []
        for page in reader.pages[:10]:
            text_chunks.append(page.extract_text() or "")

        words = []
        for token in " ".join(text_chunks).lower().split():
            clean = "".join(ch for ch in token if ch.isalpha())
            if len(clean) >= 4 and clean not in self.STOP_WORDS:
                words.append(clean)

        if not words:
            return None

        top = Counter(words).most_common(12)
        labels = [w for w, _ in top]
        vals = [c for _, c in top]

        fig, ax = plt.subplots(figsize=(10, 5), facecolor="#0B1426")
        ax.set_facecolor("#0B1426")
        ax.bar(labels, vals, color="#3B82F6")
        ax.tick_params(axis="x", rotation=35, colors="white")
        ax.tick_params(axis="y", colors="white")
        ax.set_title(f"{ticker.upper()} Earnings PDF Word Frequency", color="white")
        for spine in ax.spines.values():
            spine.set_color("#6B7280")

        out = self.output_dir / f"{ticker.upper()}_word_freq.png"
        fig.tight_layout()
        fig.savefig(out, dpi=160)
        plt.close(fig)
        return str(out)
