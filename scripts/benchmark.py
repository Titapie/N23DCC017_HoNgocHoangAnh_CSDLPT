# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN02-N
#
# Tệp tin: scripts/benchmark.py - Script đo lường hiệu năng cây Merkle
# ==============================================================================
import sys
import os
import time
import json
import random
from datetime import datetime

# Cho phép import thư mục core từ thư mục cha
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.merkle import MerkleTree, serialize_transaction, hash_data

def generate_dummy_transactions(count):
    accounts = [f"ACC{i:03d}" for i in range(1, 100)]
    txs = []
    for i in range(count):
        txs.append({
            "TransactionID": f"TX-BENCH-{i:06d}",
            "From_Account": random.choice(accounts),
            "To_Account": random.choice(accounts),
            "Amount": round(random.uniform(5.0, 10000.0), 2),
            "Timestamp": datetime.now().isoformat(),
            "BlockID": 1
        })
    return txs

def run_benchmark():
    block_sizes = [50, 100, 200, 500, 1000, 2000]
    results = []

    print("==================================================")
    print("        MERKLE TREE PERFORMANCE BENCHMARK         ")
    print("==================================================")

    for size in block_sizes:
        print(f"Profiling block size: {size} transactions...")
        txs = generate_dummy_transactions(size)
        
        # 1. Đo thời gian dựng cây Merkle Tree
        start_build = time.perf_counter()
        tree = MerkleTree(txs)
        end_build = time.perf_counter()
        build_time_ms = (end_build - start_build) * 1000
        
        # 2. Đo thời gian sinh Proof và xác minh
        tx_id = txs[random.randint(0, size - 1)]['TransactionID']
        
        # Lấy Proof anh em của một giao dịch theo chỉ mục ngẫu nhiên
        start_proof = time.perf_counter()
        proof = tree.get_proof_by_index(random.randint(0, size - 1))
        end_proof = time.perf_counter()
        proof_time_ms = (end_proof - start_proof) * 1000
        
        # Đo thời gian xác minh Proof
        leaf_hash = tree.leaves[0].hash
        start_verify = time.perf_counter()
        tree.verify_proof(leaf_hash, proof, tree.get_root_hash())
        end_verify = time.perf_counter()
        verify_time_ms = (end_verify - start_verify) * 1000

        # 3. Tính toán dung lượng dư thừa của cấu trúc Merkle Tree
        # Ước tính dung lượng của các bản ghi giao dịch thô
        raw_data_size = sum(len(serialize_transaction(tx)) for tx in txs)
        
        # Với mô hình của hệ thống, ta chỉ cần lưu trữ Root Hash (64 ký tự hex = 64 bytes)
        # trên TTP độc lập để làm mốc đối chứng toàn vẹn.
        ttp_overhead_bytes = 64  # Kích thước chuỗi Root Hash
        overhead_pct = (ttp_overhead_bytes / raw_data_size) * 100

        results.append({
            "BlockSize": size,
            "BuildTimeMs": round(build_time_ms, 4),
            "ProofTimeMs": round(proof_time_ms, 4),
            "VerifyTimeMs": round(verify_time_ms, 4),
            "RawDataSizeBytes": raw_data_size,
            "RootHashSizeBytes": ttp_overhead_bytes,
            "OverheadPct": round(overhead_pct, 4)
        })
        
        print(f"  Build Time: {build_time_ms:.4f} ms")
        print(f"  Proof Time: {proof_time_ms:.4f} ms")
        print(f"  Verify Time: {verify_time_ms:.4f} ms")
        print(f"  Storage Overhead: {overhead_pct:.6f} %\n")

    # Lưu kết quả đo đạc ra file JSON
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../static/benchmark_results.json'))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print(f"[+] Benchmark results successfully saved to {output_path}")

if __name__ == '__main__':
    run_benchmark()
