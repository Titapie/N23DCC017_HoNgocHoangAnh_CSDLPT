# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN02-N
#
# Tệp tin: scripts/view_db.py - Script CLI xem nhanh chi tiết giao dịch từ 2 database
# ==============================================================================
import sys
import os
import sqlite3

# Set output encoding to UTF-8 to prevent Windows terminal crash
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DB_A_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_a.db'))
DB_B_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_b.db'))

def view_transaction(tx_id):
    print("==================================================")
    print(f"   CHI TIẾT GIAO DỊCH {tx_id} DƯỚI CSDL VẬT LÝ   ")
    print("==================================================")
    
    # 1. Truy vấn thông tin giao dịch ở Site A (Bản sạch)
    tx_a = None
    if os.path.exists(DB_A_PATH):
        conn_a = sqlite3.connect(DB_A_PATH)
        conn_a.row_factory = sqlite3.Row
        tx_a = conn_a.execute("SELECT * FROM Banking_Transactions WHERE TransactionID=?", (tx_id,)).fetchone()
        conn_a.close()
    
    # 2. Truy vấn thông tin giao dịch ở Site B (Bản chi nhánh)
    tx_b = None
    if os.path.exists(DB_B_PATH):
        conn_b = sqlite3.connect(DB_B_PATH)
        conn_b.row_factory = sqlite3.Row
        tx_b = conn_b.execute("SELECT * FROM Banking_Transactions WHERE TransactionID=?", (tx_id,)).fetchone()
        conn_b.close()
        
    # In kết quả đối chứng
    if not tx_a and not tx_b:
        print(f"[x] Không tìm thấy giao dịch {tx_id} ở cả hai database.")
        return
        
    print(f"Trạng thái tại Site A (Bản sạch đối chứng):")
    if tx_a:
        print(f"  -> Từ: {tx_a['From_Account']} | Đến: {tx_a['To_Account']} | Số tiền: ${tx_a['Amount']:.2f} | Block: {tx_a['BlockID']}")
    else:
        print("  -> (Không tồn tại - Có thể đã bị chèn khống ở Site B)")
        
    print(f"\nTrạng thái tại Site B (Bản chi nhánh):")
    if tx_b:
        print(f"  -> Từ: {tx_b['From_Account']} | Đến: {tx_b['To_Account']} | Số tiền: ${tx_b['Amount']:.2f} | Block: {tx_b['BlockID']}")
    else:
        print("  -> (Không tồn tại - Có thể đã bị XÓA khỏi Site B)")
    print("==================================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng: python scripts/view_db.py <TransactionID>")
        print("Ví dụ: python scripts/view_db.py TX-100150")
    else:
        view_transaction(sys.argv[1])
