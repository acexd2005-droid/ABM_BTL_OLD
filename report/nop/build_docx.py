#!/usr/bin/env python3
"""Sinh report/nop/bao_cao_nop.docx từ report/bao_cao_nop.md bằng pandoc.

Chạy:  python report/nop/build_docx.py

Không sửa bao_cao_nop.md. Công thức dạng văn bản thuần (r^D_{i,t}, clip_[0;14], ...) được
chuyển thành LaTeX ($...$, $$...$$) TRONG BỘ NHỚ rồi ghi ra file tạm để pandoc dựng công thức
Word (OMML) có chỉ số trên/dưới. Chỉ đổi cách hiển thị, không đổi nội dung.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PANDOC = "/opt/homebrew/bin/pandoc"
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "report" / "bao_cao_nop.md"
OUT = ROOT / "report" / "nop" / "bao_cao_nop.docx"

# Công thức dòng riêng (khớp nguyên dòng, bỏ thụt đầu dòng 2 dấu cách).
DISPLAY = {
    "r^D_mô_hình = `deposit_rate_pct` / (1 − CASA),   chi phí vốn = r^D · (1 − CASA) + 0.15 = `deposit_rate_pct` + 0.15.":
        r"$$r^D_{\text{mô hình}} = \frac{\texttt{deposit\_rate\_pct}}{1-\mathrm{CASA}},\qquad \text{chi phí vốn} = r^D\cdot(1-\mathrm{CASA})+0.15 = \texttt{deposit\_rate\_pct}+0.15.$$",
    "r^D_{i,t} = clip_[0;14]( r^D_{i,t−1} + κ_t · [s₀ + δ · clip_±0.5(LDR_i − LDR*)] + φ · (ON_{t−1} + spread − r^D_{i,t−1}) )":
        r"$$r^D_{i,t} = \mathrm{clip}_{[0;14]}\Big( r^D_{i,t-1} + \kappa_t\cdot\big[s_0 + \delta\cdot \mathrm{clip}_{\pm 0.5}(LDR_i - LDR^*)\big] + \varphi\cdot(ON_{t-1} + \mathrm{spread} - r^D_{i,t-1}) \Big)$$",
    "r^L_{i,t} = r^L_{i,t−1} + λ · (FC^lag_{i} + m_i + 1.35 − r^L_{i,t−1})":
        r"$$r^L_{i,t} = r^L_{i,t-1} + \lambda\cdot\big(FC^{lag}_{i} + m_i + 1.35 - r^L_{i,t-1}\big)$$",
    "p_i = clip_[0.02; 0.98]( 1 / (1 + exp(−[2.5 · (P − 0.5) + 1.1 · (nim_i − 2.2)])) ),":
        r"$$p_i = \mathrm{clip}_{[0.02;\,0.98]}\Big( \frac{1}{1+\exp\!\big(-[2.5\cdot(P-0.5)+1.1\cdot(nim_i-2.2)]\big)} \Big),$$",
}
# Công thức nằm trong câu (thay đoạn con).
INLINE = {
    "g^D_i = clip_[g^D_min; g^D_max]( g^D_0 + σ · (r^D_i − r̄^D) )":
        r"$g^D_i = \mathrm{clip}_{[g^D_{\min};\,g^D_{\max}]}\big( g^D_0 + \sigma\cdot(r^D_i - \bar r^D) \big)$",
    "g^L_i = clip_[g^L_min; g^L_max]( g^L_0 − ε · (r^L_i − 9.5) )":
        r"$g^L_i = \mathrm{clip}_{[g^L_{\min};\,g^L_{\max}]}\big( g^L_0 - \varepsilon\cdot(r^L_i - 9.5) \big)$",
    "L_i = min( L_i·(1 + g^L_i), 1.60 · D_i )":
        r"$L_i = \min\big( L_i\cdot(1 + g^L_i),\ 1.60\cdot D_i \big)$",
}
GREEK = {"κ": r"\kappa", "λ": r"\lambda", "φ": r"\varphi", "σ": r"\sigma", "ε": r"\varepsilon", "δ": r"\delta"}
TOKEN = re.compile(r"(?<![\w/.\-])([A-Za-z]+|[A-Za-z]̄|[κλφσεδ])((?:[_^](?:\{[^}]*\}|[A-Za-z0-9]+))+)")
PART = re.compile(r"([_^])(\{[^}]*\}|[A-Za-z0-9]+)")


def _atom(t: str) -> str:
    t = t.strip("{}").replace("−", "-")
    return t if re.fullmatch(r"[A-Za-z0-9,\-]", t) or "," in t or "-" in t else (
        t if len(t) == 1 else r"\mathrm{%s}" % t)


def _token(m: re.Match) -> str:
    base, rest = m.group(1), m.group(2)
    if len(base) == 2 and base[1] == "̄":
        b = r"\bar %s" % base[0]
    elif base in GREEK:
        b = GREEK[base]
    elif len(base) > 1:
        b = r"\mathrm{%s}" % base
    else:
        b = base
    parts = "".join("%s{%s}" % (op, _atom(arg)) for op, arg in PART.findall(rest))
    return "$%s%s$" % (b, parts)


def transform(text: str) -> str:
    keep = []

    def stash(m):
        keep.append(m.group(0))
        return "\x00%d\x00" % (len(keep) - 1)

    lines = []
    for ln in text.split("\n"):
        body = ln[2:] if ln.startswith("  ") else None
        if body is not None and body in DISPLAY:
            ln = DISPLAY[body]
        lines.append(ln)
    text = "\n".join(lines)
    for a, b in INLINE.items():
        if text.count(a) != 1:
            sys.exit("Không khớp công thức trong câu: " + a[:40])
        text = text.replace(a, b)
    for k in DISPLAY.values():
        if k not in text:
            sys.exit("Không khớp công thức dòng riêng")
    # bảo vệ: công thức đã chuyển, đoạn code, URL
    text = re.sub(r"\$\$.*?\$\$|\$[^$\n]+\$|`[^`\n]*`|https?://\S+", stash, text, flags=re.S)
    text = TOKEN.sub(_token, text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], text)
    return text


def main():
    text = transform(SRC.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "bao_cao_nop_math.md"
        tmp.write_text(text, encoding="utf-8")
        subprocess.run(
            [PANDOC, str(tmp), "-f", "markdown+tex_math_dollars", "-o", str(OUT),
             "--toc", "--toc-depth=3", "-M", "lang=vi", "-M", "toc-title=Mục lục"],
            check=True)
    print("Đã tạo", OUT)


if __name__ == "__main__":
    main()
