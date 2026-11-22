#!/usr/bin/env python3
"""Dựng report/nop/bao_cao_ABM_PTIT.docx theo mẫu PTIT từ report/nop/bao_cao_ptit.md.

Chạy (từ gốc repo):  python report/nop/build_ptit.py

Các bước: (1) chuyển công thức văn bản thuần sang LaTeX bằng transform() của build_docx.py;
(2) đánh số (1)–(4) cho các công thức dòng riêng; (3) gọi build_ptit_docx.py với file mẫu
mau_ptit.docx và thông tin bìa bia.json. Không sửa bao_cao_ptit.md.
"""
import importlib.util
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANDOC = "/opt/homebrew/bin/pandoc"
SRC = HERE / "bao_cao_ptit.md"
OUT = HERE / "bao_cao_ABM_PTIT.docx"

spec = importlib.util.spec_from_file_location("build_docx", HERE / "build_docx.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)


def main():
    md = bd.transform(SRC.read_text(encoding="utf-8"))
    n = 0

    def num(m):
        nonlocal n
        n += 1
        return m.group(0) + f" ({n})"

    md = re.sub(r"^\$\$.*\$\$$", num, md, flags=re.M)
    print("Số công thức được đánh số:", n)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "bao_cao_ptit_math.md"
        tmp.write_text(md, encoding="utf-8")
        subprocess.run([sys.executable, str(HERE / "build_ptit_docx.py"), str(tmp), str(HERE / "mau_ptit.docx"),
                        str(HERE / "bia.json"), str(OUT), "--pandoc", PANDOC], check=True)


if __name__ == "__main__":
    main()
