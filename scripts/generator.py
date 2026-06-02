# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN01-N
#
# Tệp tin: scripts/generator.py - Script sinh dữ liệu mẫu ban đầu (500 giao dịch)
# ==============================================================================
import sys
import os
import random
from datetime import datetime, timedelta

# Allow importing core package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import init_db, insert_transactions, insert_block_hash
from core.merkle import get_root_hash

DB_A_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_a.db'))
DB_B_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_b.db'))
DB_TTP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/ttp.db'))

def generate_transactions(count=500):
    accounts = [f"ACC{i:03d}" for i in range(1, 21)]
    transactions = []
    
    # Start time
    base_time = datetime.now() - timedelta(days=2)
    
    for i in range(count):
        tx_id = f"TX-{100001 + i}"
        from_acc = random.choice(accounts)
        to_acc = random.choice([acc for acc in accounts if acc != from_acc])
        amount = round(random.uniform(10.0, 5000.0), 2)
        if tx_id == "TX-100150":
            amount = 100.00
        timestamp = (base_time + timedelta(seconds=i * 10)).isoformat()
        
        # BlockID is (i // 100) + 1. e.g., 0-99 is Block 1, 100-199 is Block 2, etc.
        block_id = (i // 100) + 1
        
        transactions.append({
            "TransactionID": tx_id,
            "From_Account": from_acc,
            "To_Account": to_acc,
            "Amount": amount,
            "Timestamp": timestamp,
            "BlockID": block_id
        })
    return transactions

def main():
    print("==================================================")
    print("         GENERATING SEED TRANSACTION LOGS         ")
    print("==================================================")
    
    # 1. Initialize databases
    print("[i] Cleaning old databases if exist...")
    for path in [DB_A_PATH, DB_B_PATH, DB_TTP_PATH]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"  -> Removed: {os.path.basename(path)}")
            except Exception as e:
                print(f"  -> Error removing {os.path.basename(path)}: {e}")
                
    print("[i] Initializing SQLite databases...")
    init_db(DB_A_PATH, 'site')
    init_db(DB_B_PATH, 'site')
    init_db(DB_TTP_PATH, 'ttp')
    
    # 2. Generate 500 transactions
    print("[i] Generating 500 random transactions...")
    txs = generate_transactions(500)
    
    # 3. Write transactions to Site A and Site B (Simulating eager replication)
    print(f"[i] Writing transaction records to Site A: {DB_A_PATH}...")
    insert_transactions(DB_A_PATH, txs)
    
    print(f"[i] Writing transaction records to Site B: {DB_B_PATH}...")
    insert_transactions(DB_B_PATH, txs)
    
    # 4. Generate Merkle Tree for every 100 transactions and write Root Hash to TTP
    print("[i] Building Merkle Trees for blocks and registering Root Hashes at TTP...")
    for block_idx in range(5):
        block_id = block_idx + 1
        block_txs = txs[block_idx * 100 : (block_idx + 1) * 100]
        
        start_tx = block_txs[0]['TransactionID']
        end_tx = block_txs[-1]['TransactionID']
        
        # Calculate Root Hash
        root_hash = get_root_hash(block_txs)
        
        # Insert to TTP
        insert_block_hash(
            DB_TTP_PATH,
            block_id,
            start_tx,
            end_tx,
            root_hash,
            datetime.now().isoformat()
        )
        print(f"  -> Block {block_id}: Transactions {start_tx} to {end_tx} | Root: {root_hash[:16]}...")
        
    print("\n[+] SUCCESS: Databases initialized and seeded with 5 blocks of data!")
    print("==================================================")

if __name__ == '__main__':
    main()
