import sys
import os
import time

# Bổ sung thư mục cha vào đường dẫn hệ thống để có thể import package 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import get_db_connection, get_block_hashes, get_transactions_by_block
from core.merkle import get_root_hash, hash_transaction, compare_leaf_hashes

# Xác định đường dẫn vật lý của các tệp cơ sở dữ liệu SQLite
DB_A_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_a.db'))
DB_B_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_b.db'))
DB_TTP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/ttp.db'))

def run_audit():
    print("==================================================")
    print("          STARTING TRANSACTION LOG AUDIT          ")
    print("==================================================")
    
    # 0. Kiểm tra xem các file cơ sở dữ liệu đã tồn tại chưa
    if not all(os.path.exists(p) for p in [DB_A_PATH, DB_B_PATH, DB_TTP_PATH]):
        print("[x] ERROR: Database files are missing. Please run generator first.")
        sys.exit(1)

    # 1. Truy cập Bên thứ ba trung lập (TTP) để tải danh sách các Root Hash đã đăng ký bất biến
    block_hashes = get_block_hashes(DB_TTP_PATH)
    if not block_hashes:
        print("[i] No blocks found in TTP registry.")
        return

    total_blocks = len(block_hashes)
    tampered_blocks_list = []
    
    # Bắt đầu đo thời gian chạy của quá trình kiểm toán bằng đồng hồ độ chính xác cao
    start_audit_time = time.perf_counter()

    # 2. Duyệt qua từng Block để kiểm tra tính toàn vẹn độc lập
    for bh in block_hashes:
        block_id = bh['BlockID']
        ttp_root = bh['RootHash']
        
        # Lấy danh sách giao dịch hiện thời từ Site B (Bản chi nhánh nghi bị sửa đổi)
        txs_b = get_transactions_by_block(DB_B_PATH, block_id)
        
        # Tự tính toán lại mã băm gốc Merkle Root cục bộ dựa trên dữ liệu của Site B
        local_root_b = get_root_hash(txs_b)
        
        # 3. So sánh mã băm cục bộ của Site B với Root Hash bất biến lưu trữ tại TTP
        if local_root_b != ttp_root:
            # Phát hiện bất thường! Thêm BlockID này vào danh sách bị phá hoại
            tampered_blocks_list.append(block_id)
            
            # ĐƯỢC KÍCH HOẠT: GIẢI THUẬT PHÁP Y (FORENSICS & LOCALIZATION)
            # Tải danh sách giao dịch từ Site A (Bản sạch đối chứng đáng tin cậy)
            txs_a = get_transactions_by_block(DB_A_PATH, block_id)
            
            # Tính mã băm lá (Leaf Hashes) cho từng giao dịch lẻ ở cả 2 site
            hashes_a = [{"TransactionID": tx['TransactionID'], "hash": hash_transaction(tx)} for tx in txs_a]
            hashes_b = [{"TransactionID": tx['TransactionID'], "hash": hash_transaction(tx)} for tx in txs_b]
            
            # Đối chiếu 2 tập băm lá để phân loại kiểu vi phạm
            diff = compare_leaf_hashes(hashes_a, hashes_b)
            
            print(f"\nAudit Result: TAMPERED")
            
            if diff["mismatch"]:
                txs_a_dict = {tx['TransactionID']: tx for tx in txs_a}
                txs_b_dict = {tx['TransactionID']: tx for tx in txs_b}
                
                # ------ KIỂU VI PHẠM 1: SỬA ĐỔI DỮ LIỆU GIAO DỊCH (UPDATE) ------
                for tx_id in diff["modified"]:
                    tx_a = txs_a_dict[tx_id]
                    tx_b = txs_b_dict[tx_id]
                    
                    # Tìm xem trường nào bị thay đổi giá trị
                    for field in ['From_Account', 'To_Account', 'Amount', 'Timestamp']:
                        val_a = tx_a[field]
                        val_b = tx_b[field]
                        if val_a != val_b:
                            if field == 'Amount':
                                # Báo cáo chi tiết đối chiếu số tiền
                                print(f"BlockID: {block_id}")
                                print(f"TransactionID: {tx_id}")
                                print(f"Changed field: {field}")
                                print(f"Site A value: {val_a:.2f}")
                                print(f"Site B value: {val_b:.2f}")
                                print(f"Root Hash from TTP: {ttp_root}")
                                print(f"Recomputed Site B Root Hash: {local_root_b}")
                                print()
                                print(f"Tampered TransactionID: {tx_id}")
                                print(f"Field changed: {field}")
                                print(f"Clean value at Site A: {val_a:.2f}")
                                print(f"Tampered value at Site B: {val_b:.2f}")
                                print(f"BlockID: {block_id}")
                            else:
                                print(f"BlockID: {block_id}")
                                print(f"TransactionID: {tx_id}")
                                print(f"Changed field: {field}")
                                print(f"Site A value: {val_a}")
                                print(f"Site B value: {val_b}")
                                print(f"Root Hash from TTP: {ttp_root}")
                                print(f"Recomputed Site B Root Hash: {local_root_b}")

                # ------ KIỂU VI PHẠM 2: XÓA GIAO DỊCH (DELETE) ------
                for tx_id in diff["deleted"]:
                    print(f"Issue type: row_count_mismatch / deleted_transaction")
                    print(f"Deleted TransactionID: {tx_id}")
                    print(f"BlockID: {block_id}")
                    
                # ------ KIỂU VI PHẠM 3: CHÈN GIAO DỊCH LẬU (INSERT) ------
                for tx_id in diff["injected"]:
                    print(f"Issue type: fake_transaction / inserted_transaction")
                    print(f"Inserted TransactionID: {tx_id}")
                    print(f"BlockID: {block_id}")
            else:
                # Nếu Root Hash lệch nhưng các lá không tìm được ID tương thích (sai lệch về số dòng)
                len_a = len(txs_a)
                len_b = len(txs_b)
                if len_a != len_b:
                    print(f"Issue type: row_count_mismatch / deleted_transaction")
                    print(f"Deleted or inserted transactions led to mismatch")
                    print(f"BlockID: {block_id}")
                    print(f"Site A row count: {len_a}")
                    print(f"Site B row count: {len_b}")
            print("-" * 50)
            
    end_audit_time = time.perf_counter()
    total_time_ms = (end_audit_time - start_audit_time) * 1000
    
    # 4. In tổng hợp kết quả kiểm toán chung ra màn hình
    if not tampered_blocks_list:
        print(f"\nAudit Result: SAFE")
        print(f"Checked blocks: {total_blocks}")
        print(f"Tampered blocks: 0")
    else:
        print(f"\nAudit finished. Tampered blocks detected: {len(tampered_blocks_list)}")
    print(f"Total Audit Time: {total_time_ms:.4f} ms")
    print("==================================================")

if __name__ == '__main__':
    run_audit()
