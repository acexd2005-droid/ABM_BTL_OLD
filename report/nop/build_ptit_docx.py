#!/usr/bin/env python3
"""Dựng báo cáo .docx theo mẫu "Báo cáo tổng kết đề tài NCKH sinh viên" (PTIT, Khoa TCKT1).

Cách dùng:
    python build_ptit_docx.py <bai.md> <mau.docx> <bia.json> <ra.docx> [--pandoc /duong/dan/pandoc]

- bai.md   : thân bài Markdown đã theo cấu trúc mẫu (# MỞ ĐẦU, # CHƯƠNG 1. ..., ## 1.1. ..., # KẾT LUẬN,
             # TÀI LIỆU THAM KHẢO, # PHỤ LỤC). Không có tiêu đề đề tài ở đầu (tiêu đề nằm trên bìa).
             Công thức viết bằng LaTeX ($...$, $$...$$). Công thức có số: viết `$$...$$ (1)` trên cùng
             một dòng. Chú thích bảng: dòng ": Bảng 2.1. ..." ngay trên bảng (cú pháp pandoc).
             Chú thích hình: ![Hình 2.1. ...](duong/dan.png). Dòng "Nguồn: ..." ngay sau bảng/hình.
- mau.docx : file mẫu gốc (dùng làm reference-doc cho style và lấy nguyên trang bìa, khung, logo).
- bia.json : thông tin bìa và phần đầu (xem SKILL.md).
"""
import copy, io, json, re, subprocess, sys, tempfile, os
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_EMBED = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'


def text_of(el):
    return ''.join(t.text or '' for t in el.iter(qn('w:t')))


def set_par_text(p_el, new_text):
    """Giữ định dạng run đầu tiên có chữ, thay toàn bộ chữ trong đoạn."""
    runs = [r for r in p_el.findall(qn('w:r')) if r.find(qn('w:t')) is not None]
    if not runs:
        return
    first = runs[0]
    for r in runs[1:]:
        p_el.remove(r)
    ts = first.findall(qn('w:t'))
    ts[0].text = new_text
    ts[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    for t in ts[1:]:
        first.remove(t)
    for pe in p_el.findall(qn('w:proofErr')):
        p_el.remove(pe)


def field_par(instr, style=None):
    """Đoạn chứa một trường Word (TOC...), Word cập nhật khi mở (F9)."""
    p = OxmlElement('w:p')
    if style:
        ppr = OxmlElement('w:pPr'); ps = OxmlElement('w:pStyle'); ps.set(qn('w:val'), style)
        ppr.append(ps); p.append(ppr)
    def run(child):
        r = OxmlElement('w:r'); r.append(child); p.append(r)
    b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'), 'begin'); b.set(qn('w:dirty'), 'true'); run(b)
    it = OxmlElement('w:instrText'); it.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve'); it.text = f' {instr} '; run(it)
    s = OxmlElement('w:fldChar'); s.set(qn('w:fldCharType'), 'separate'); run(s)
    t = OxmlElement('w:t'); t.text = 'Nhấn F9 (Cập nhật trường) để hiện nội dung.'; run(t)
    e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), 'end'); run(e)
    return p


def border(tag, sz=6):
    b = OxmlElement(f'w:{tag}')
    b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), str(sz)); b.set(qn('w:space'), '0'); b.set(qn('w:color'), '000000')
    return b


def style_tables(doc):
    for tbl in doc.tables:
        rows = tbl.rows
        for ri, row in enumerate(rows):
            for cell in row.cells:
                tcpr = cell._tc.get_or_add_tcPr()
                old = tcpr.find(qn('w:tcBorders'))
                if old is not None:
                    tcpr.remove(old)
                if ri == 0:
                    bs = OxmlElement('w:tcBorders'); bs.append(border('top')); bs.append(border('bottom')); tcpr.append(bs)
                elif ri == len(rows) - 1:
                    bs = OxmlElement('w:tcBorders'); bs.append(border('bottom')); tcpr.append(bs)
                for p in cell.paragraphs:
                    pf = p.paragraph_format
                    pf.space_before = Pt(0); pf.space_after = Pt(0); pf.line_spacing = 1.0; pf.first_line_indent = Pt(0)
                    if ri == 0:
                        p.alignment = 1
                        for r in p.runs:
                            r.font.bold = True


def fit_columns(doc, text_width_twips):
    """Chia độ rộng cột theo độ dài nội dung (cột chữ dài được rộng hơn), tổng bằng bề rộng vùng chữ."""
    for tbl in doc.tables:
        ncol = len(tbl.columns)
        if ncol == 0:
            continue
        lens = [6] * ncol
        for row in tbl.rows:
            for ci, cell in enumerate(row.cells[:ncol]):
                lens[ci] = max(lens[ci], min(len(cell.text.strip()), 40))
        tot = sum(lens)
        widths = [int(text_width_twips * l / tot) for l in lens]
        grid = tbl._tbl.find(qn('w:tblGrid'))
        if grid is not None:
            for gc, w in zip(grid.findall(qn('w:gridCol')), widths):
                gc.set(qn('w:w'), str(w))
        for row in tbl.rows:
            for ci, tc in enumerate(row._tr.findall(qn('w:tc'))[:ncol]):
                tcpr = tc.get_or_add_tcPr()
                tw = tcpr.find(qn('w:tcW'))
                if tw is None:
                    tw = OxmlElement('w:tcW'); tcpr.insert(0, tw)
                tw.set(qn('w:w'), str(widths[ci])); tw.set(qn('w:type'), 'dxa')
        tblpr = tbl._tbl.tblPr
        lay = tblpr.find(qn('w:tblLayout'))
        if lay is None:
            lay = OxmlElement('w:tblLayout'); tblpr.append(lay)
        lay.set(qn('w:type'), 'fixed')


def style_code(doc):
    """Tên biến/tham số trong dấu `...`: Courier New 11 pt, chữ đứng (style Verbatim Char của pandoc)."""
    try:
        st = doc.styles['Verbatim Char']
    except KeyError:
        return
    st.font.name = 'Courier New'; st.font.size = Pt(11); st.font.italic = False
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is not None:
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rf.set(qn(a), 'Courier New')


def style_captions(doc):
    """Chú thích bảng/hình: giữa, nghiêng, 13pt. 'Nguồn: ...': giữa, nghiêng, 12pt."""
    for p in doc.paragraphs:
        name = p.style.name if p.style is not None else ''
        txt = p.text.strip()
        if name in ('Table Caption', 'Image Caption') or re.match(r'^(Bảng|Hình)\s+[A-Z]?\d+(\.\d+)*\.\s', txt) and len(txt) < 300 and name in ('Body Text', 'First Paragraph', 'Compact'):
            p.alignment = 1
            p.paragraph_format.first_line_indent = Pt(0)
            for r in p.runs:
                r.font.italic = True; r.font.size = Pt(13)
        elif re.match(r'^Nguồn\s*:', txt) and len(txt) < 300:
            p.alignment = 1
            p.paragraph_format.first_line_indent = Pt(0)
            for r in p.runs:
                r.font.italic = True; r.font.size = Pt(12)
        if name == 'Captioned Figure':
            p.alignment = 1


def number_equations(doc, text_width_twips):
    """Công thức dòng riêng ($$...$$) mà đoạn ngay sau chỉ có '(n)': gộp thành một dòng,
    công thức ở giữa (tab giữa), số ở lề phải (tab phải). Pandoc tách $$..$$ thành đoạn riêng."""
    M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
    ps = doc.paragraphs
    for k, p in enumerate(ps[:-1]):
        el = p._p
        mp = el.find(f'{{{M}}}oMathPara')
        if mp is None or p.text.strip():
            continue
        nxt = ps[k + 1]
        m = re.fullmatch(r'\((\d+(?:\.\d+)?)\)', nxt.text.strip())
        if not m:
            continue
        omath = mp.find(f'{{{M}}}oMath')
        el.remove(mp)
        ppr = el.get_or_add_pPr()
        tabs = OxmlElement('w:tabs')
        for val, pos in (('center', text_width_twips // 2), ('right', text_width_twips)):
            t = OxmlElement('w:tab'); t.set(qn('w:val'), val); t.set(qn('w:pos'), str(pos)); tabs.append(t)
        ppr.append(tabs)
        ind = OxmlElement('w:ind'); ind.set(qn('w:firstLine'), '0'); ppr.append(ind)
        def tab_run():
            r = OxmlElement('w:r'); r.append(OxmlElement('w:tab')); return r
        el.append(tab_run()); el.append(omath); el.append(tab_run())
        r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = f'({m.group(1)})'; r.append(t); el.append(r)
        nxt._p.getparent().remove(nxt._p)


def build_front(tpl, out, cfg):
    """Chép phần đầu của mẫu (bìa ngoài, bìa trong, lời cảm ơn, mục lục, danh mục) vào đầu out."""
    tbody = tpl.element.body
    items = list(tbody.iterchildren())
    end = None
    for i, e in enumerate(items):
        if e.tag == qn('w:p') and e.find('.//' + qn('w:sectPr')) is not None:
            end = i; break
    if end is None:
        sys.exit('Không tìm thấy ngắt phân đoạn sau phần đầu trong file mẫu.')
    front = [copy.deepcopy(e) for e in items[:end + 1]]

    # ảnh (khung bìa, logo): chép sang gói docx mới
    for e in front:
        for blip in e.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            rid = blip.get(R_EMBED)
            blob = tpl.part.related_parts[rid].blob
            new_rid, _ = out.part.get_or_add_image(io.BytesIO(blob))
            blip.set(R_EMBED, new_rid)

    # thay chữ trên hai trang bìa theo cấu hình
    repl = {
        'HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG': cfg.get('truong'),
        'KHOA TÀI CHÍNH KẾ TOÁN 1': cfg.get('khoa'),
        'BÁO CÁO TỔNG KẾT': cfg.get('loai_bao_cao'),
        'ĐỀ TÀI NGHIÊN CỨU KHOA HỌC CỦA SINH VIÊN': cfg.get('loai_de_tai'),
        'NĂM HỌC 2026-2027': cfg.get('nam_hoc') and f"NĂM HỌC {cfg['nam_hoc']}",
        'NGHIÊN CỨU ẢNH HƯỞNG CỦA TIN TỨC TỚI BIẾN ĐỘNG GIÁ VÀNG TẠI VIỆT NAM': cfg.get('ten_de_tai', '').upper() or None,
        'Mã số đề tài: 02-SV-2026-TCKT1': cfg.get('ma_so') and f"Mã số đề tài: {cfg['ma_so']}",
        'Thuộc nhóm ngành khoa học: Kinh tế': cfg.get('nhom_nganh') and f"Thuộc nhóm ngành khoa học: {cfg['nhom_nganh']}",
        'Hà Nội, 11/2026': cfg.get('noi_thang'),
        'Người hướng dẫn: ThS. Trần Quốc Khánh': cfg.get('nguoi_huong_dan') and f"Người hướng dẫn: {cfg['nguoi_huong_dan']}",
        'Hà Nội, tháng 11 năm 2026': cfg.get('noi_ngay_cam_on'),
    }
    for e in front:
        for p in ([e] if e.tag == qn('w:p') else e.iter(qn('w:p'))):
            t = text_of(p).strip()
            if t in repl and repl[t] is not None:
                set_par_text(p, repl[t])
    # bỏ dòng mã số nếu cấu hình ghi null
    if 'ma_so' in cfg and cfg['ma_so'] is None:
        front[:] = [e for e in front if not (e.tag == qn('w:p') and text_of(e).strip().startswith('Mã số đề tài'))]
    # tên đề tài dài hơn 2 dòng: bỏ bớt dòng trống trước "Hà Nội, ..." để không đè khung bìa
    so_dong = max(1, -(-len(cfg.get('ten_de_tai', '')) // 60))
    thua = max(0, so_dong - 2)
    if thua:
        noi = cfg.get('noi_thang') or 'Hà Nội, 11/2026'
        vt_noi = [i for i, e in enumerate(front) if e.tag == qn('w:p') and text_of(e).strip() == noi]
        for vi in sorted(vt_noi, reverse=True):
            j, bo = vi - 1, 0
            while j >= 0 and bo < thua and front[j].tag == qn('w:p') and not text_of(front[j]).strip() and front[j].find('.//' + qn('w:drawing')) is None and front[j].find('.//' + qn('w:br')) is None:
                del front[j]; bo += 1; j -= 1

    # bảng sinh viên thực hiện (bảng đầu tiên trong phần đầu)
    tbls = [e for e in front if e.tag == qn('w:tbl')]
    sv = cfg.get('sinh_vien', [])
    if tbls and sv:
        t = tbls[0]
        trs = t.findall(qn('w:tr'))
        proto = trs[1]
        for tr in trs[1:]:
            t.remove(tr)
        for k, s in enumerate(sv, 1):
            tr = copy.deepcopy(proto)
            vals = [str(k), s.get('ho_ten', ''), s.get('gioi_tinh', ''), s.get('dan_toc', ''), s.get('lop_khoa', ''), s.get('nam_thu', ''), s.get('nganh', '')]
            for tc, v in zip(tr.findall(qn('w:tc')), vals):
                for p in tc.findall(qn('w:p')):
                    set_par_text(p, v)
            t.append(tr)

    # lời cảm ơn: thay các đoạn thân bằng đoạn cấu hình (giữ định dạng đoạn đầu)
    loi = cfg.get('loi_cam_on')
    if loi:
        idx = [i for i, e in enumerate(front) if e.tag == qn('w:p') and text_of(e).strip() == 'LỜI CẢM ƠN'][0]
        body_ps = []
        j = idx + 1
        while j < len(front) and not (front[j].tag == qn('w:p') and front[j].find('.//' + qn('w:jc')) is not None and front[j].find('.//' + qn('w:jc')).get(qn('w:val')) == 'right'):
            if front[j].tag == qn('w:p') and text_of(front[j]).strip():
                body_ps.append(j)
            j += 1
        proto = front[body_ps[0]]
        new = []
        for para in loi:
            p = copy.deepcopy(proto); set_par_text(p, para); new.append(p)
        for k in sorted(body_ps, reverse=True):
            del front[k]
        for k, p in enumerate(new):
            front.insert(body_ps[0] + k, p)

    # mục lục, danh mục bảng, danh mục hình: thay danh sách tĩnh bằng trường TOC
    def replace_block(start_title, instr):
        nonlocal front
        idx = [i for i, e in enumerate(front) if e.tag == qn('w:p') and text_of(e).strip() == start_title]
        if not idx:
            return
        i = idx[0] + 1
        stop = i
        while stop < len(front) and front[stop].tag == qn('w:p'):
            ps = front[stop].find('.//' + qn('w:pStyle'))
            sv_ = ps.get(qn('w:val')) if ps is not None else ''
            if sv_.lower().startswith('toc') or sv_.lower().startswith('tableoffigures') or sv_ == 'TableofFigures':
                stop += 1
            else:
                break
        del front[i:stop]
        front.insert(i, field_par(instr))
    replace_block('MỤC LỤC', 'TOC \\o "1-3" \\h \\z \\u')
    replace_block('DANH MỤC BẢNG BIỂU', 'TOC \\h \\z \\t "Table Caption,1"')
    replace_block('DANH MỤC HÌNH VẼ', 'TOC \\h \\z \\t "Image Caption,1"')

    # danh mục từ viết tắt
    vt = cfg.get('viet_tat')
    vt_tbl = [e for e in front if e.tag == qn('w:tbl') and text_of(e).startswith('Từ viết tắt')]
    if vt and vt_tbl:
        t = vt_tbl[0]
        trs = t.findall(qn('w:tr'))
        proto = trs[1]
        for tr in trs[1:]:
            t.remove(tr)
        for row in vt:
            tr = copy.deepcopy(proto)
            for tc, v in zip(tr.findall(qn('w:tc')), row):
                for p in tc.findall(qn('w:p')):
                    set_par_text(p, v)
            t.append(tr)
    if cfg.get('bo_danh_muc_hinh'):
        idx = [i for i, e in enumerate(front) if e.tag == qn('w:p') and text_of(e).strip() == 'DANH MỤC HÌNH VẼ']
        if idx:
            del front[idx[0]:idx[0] + 2]

    obody = out.element.body
    for k, e in enumerate(front):
        obody.insert(k, e)


def main():
    a = sys.argv[1:]
    pandoc = 'pandoc'
    if '--pandoc' in a:
        k = a.index('--pandoc'); pandoc = a[k + 1]; del a[k:k + 2]
    md, tpl_path, cfg_path, out_path = a
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    with tempfile.TemporaryDirectory() as td:
        body = os.path.join(td, 'body.docx')
        subprocess.run([pandoc, md, '-f', 'markdown', '-o', body, f'--reference-doc={tpl_path}'], check=True)
        out = docx.Document(body)
    tpl = docx.Document(tpl_path)
    sec = tpl.sections[-1]
    text_w = int((sec.page_width - sec.left_margin - sec.right_margin) / 635)  # EMU -> twips
    style_tables(out)
    fit_columns(out, text_w)
    style_code(out)
    style_captions(out)
    number_equations(out, text_w)
    build_front(tpl, out, cfg)
    # phân đoạn thân bài: số trang bắt đầu từ 1, chân trang giữa
    sp = out.element.body.find(qn('w:sectPr'))
    if sp.find(qn('w:pgNumType')) is None:
        pn = OxmlElement('w:pgNumType'); pn.set(qn('w:start'), '1')
        cols = sp.find(qn('w:cols'))
        (cols.addprevious(pn) if cols is not None else sp.append(pn))
    if sp.find(qn('w:footerReference')) is None:
        ft = out.sections[-1].footer
        ft.is_linked_to_previous = False
        fp = ft.paragraphs[0] if ft.paragraphs else ft.add_paragraph()
        fp.alignment = 1
        for child in list(field_par('PAGE')):
            if child.tag == qn('w:r'):
                fp._p.append(child)
        for t in fp._p.iter(qn('w:t')):
            t.text = '1'
    # Word hỏi cập nhật trường khi mở
    st = out.settings.element
    if st.find(qn('w:updateFields')) is None:
        u = OxmlElement('w:updateFields'); u.set(qn('w:val'), 'true'); st.append(u)
    out.save(out_path)
    print('Đã ghi', out_path)


if __name__ == '__main__':
    main()
