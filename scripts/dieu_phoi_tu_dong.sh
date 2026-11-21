#!/usr/bin/env bash
# Chạy /dieu-phoi tự động: mỗi giai đoạn một phiên Claude Code mới (ngữ cảnh sạch).
# Dùng:  bash scripts/dieu_phoi_tu_dong.sh [so_vong_toi_da] [model]
# Dừng giữa chừng: Ctrl+C (giai đoạn đang chạy dở sẽ không được commit).
set -uo pipefail
MAX=${1:-8}
MODEL=${2:-sonnet}
TT=docs/ke_hoach/TRANG_THAI.md
mkdir -p logs

con_viec() { grep -E '^\| GD[0-9a-z]+ ' "$TT" | grep -q 'CHUA_LAM'; }
co_dung()  { grep -E '^\| GD[0-9a-z]+ ' "$TT" | grep -q '| DUNG |'; }

for i in $(seq 1 "$MAX"); do
  if co_dung; then echo "Có giai đoạn DUNG – xem $TT. Kết thúc."; break; fi
  if ! con_viec; then echo "Không còn giai đoạn CHUA_LAM. Kết thúc."; break; fi
  truoc=$(md5 -q "$TT" 2>/dev/null || md5sum "$TT" | cut -d' ' -f1)
  LOG="logs/dieu_phoi_$(date +%Y%m%d_%H%M%S)_vong$i.log"
  echo "=== Vòng $i – phiên mới ($MODEL) – log: $LOG ==="
  claude -p --model "$MODEL" --permission-mode dontAsk \
    "Bạn là điều phối viên. Đọc .claude/commands/dieu-phoi.md và làm đúng theo đó với tham số 'tiep', NHƯNG chỉ chạy đúng MỘT giai đoạn (giai đoạn CHUA_LAM đầu tiên đủ điều kiện tiên quyết; giai đoạn thiếu điều kiện thì đánh BI_CHAN như hướng dẫn). Sau khi giai đoạn đó được commit và push (hoặc DUNG/BI_CHAN), cập nhật TONG_HOP.md rồi kết thúc phiên. Chế độ không giao diện: không hỏi người dùng; lệnh bị từ chối quyền thì tìm cách khác trong danh sách cho phép, nếu không được thì ghi vào báo cáo và đánh DUNG." \
    > "$LOG" 2>&1
  ma=$?
  tail -5 "$LOG"
  sau=$(md5 -q "$TT" 2>/dev/null || md5sum "$TT" | cut -d' ' -f1)
  if [ "$ma" -ne 0 ]; then echo "Phiên thoát lỗi (mã $ma). Xem $LOG. Kết thúc."; break; fi
  if [ "$truoc" = "$sau" ]; then echo "TRANG_THAI.md không đổi sau một phiên – tránh lặp vô hạn. Xem $LOG. Kết thúc."; break; fi
done
echo "Xong lượt tự động. Đọc reports/giai_doan/TONG_HOP.md và $TT."
