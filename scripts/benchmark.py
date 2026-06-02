# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN01-N
#
# Tệp tin: scripts/benchmark.py - Script đo lường hiệu năng cây Merkle
# ==============================================================================
import sys
import os
import time
import json
import random
from datetime import datetime

# Allow importing from parent directory
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
        
        # 1. Measure Build Time
        start_build = time.perf_counter()
        tree = MerkleTree(txs)
        end_build = time.perf_counter()
        build_time_ms = (end_build - start_build) * 1000
        
        # 2. Measure Proof Generation and Verification
        tx_id = txs[random.randint(0, size - 1)]['TransactionID']
        
        # Sibling proof by index
        start_proof = time.perf_counter()
        proof = tree.get_proof_by_index(random.randint(0, size - 1))
        end_proof = time.perf_counter()
        proof_time_ms = (end_proof - start_proof) * 1000
        
        # Verification time
        leaf_hash = tree.leaves[0].hash
        start_verify = time.perf_counter()
        tree.verify_proof(leaf_hash, proof, tree.get_root_hash())
        end_verify = time.perf_counter()
        verify_time_ms = (end_verify - start_verify) * 1000

        # 3. Calculate Storage Overhead
        # Approximate size of transaction records in JSON string format
        raw_data_size = sum(len(serialize_transaction(tx)) for tx in txs)
        
        # Merkle Tree overhead: Root Hash is 32 bytes (64 hex characters)
        # Tree leaves and intermediate nodes hashes
        # A tree of N nodes has roughly 2N-1 nodes in total.
        # But we only store the Root Hash (64 bytes in hex) in the TTP!
        # So TTP overhead is 64 bytes.
        # Let's count that.
        ttp_overhead_bytes = 64  # Size of 1 Root Hash string
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

    # Save to JSON
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../static/benchmark_results.json'))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print(f"[+] Benchmark results successfully saved to {output_path}")

if __name__ == '__main__':
    run_benchmark()
