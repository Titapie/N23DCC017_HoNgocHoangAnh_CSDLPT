# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN02-N
#
# Tệp tin: nodes/site_a.py - Cung cấp API dịch vụ cho Site A (Bản sạch đối chứng)
# ==============================================================================
import sys
import os
from flask import Flask, request, jsonify

# Bổ sung thư mục cha vào đường dẫn tìm kiếm hệ thống để import package 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import init_db, insert_transactions, get_transactions_by_block, get_all_transactions
from core.merkle import hash_transaction

app = Flask(__name__)
# Đường dẫn vật lý lưu tệp cơ sở dữ liệu SQLite của Site A (Bản sạch đối chứng)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_a.db'))

# Khởi tạo CSDL cho Site A (chế độ 'site' - tạo bảng Banking_Transactions)
init_db(DB_PATH, 'site')

@app.route('/health', methods=['GET'])
def health():
    """
    API kiểm tra trạng thái hoạt động (Health Check) của Site A.
    """
    return jsonify({"status": "healthy", "node": "site_a", "db": DB_PATH})

@app.route('/transaction', methods=['POST'])
def add_transaction():
    """
    API tiếp nhận giao dịch từ Coordinator (phục vụ Eager Replication).
    Ghi đè/Chèn giao dịch đơn lẻ vào cơ sở dữ liệu.
    """
    tx = request.json
    required = ["TransactionID", "From_Account", "To_Account", "Amount", "Timestamp", "BlockID"]
    # Xác thực dữ liệu giao dịch đầu vào
    if not all(k in tx for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Ghi giao dịch vào database vật lý
        insert_transactions(DB_PATH, [tx])
        return jsonify({"message": f"Transaction {tx['TransactionID']} added to Site A"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transactions', methods=['POST'])
def add_transactions_batch():
    """
    API tiếp nhận hàng loạt giao dịch cùng một lúc (hữu ích khi nạp dữ liệu mẫu ban đầu).
    """
    txs = request.json
    if not isinstance(txs, list):
        return jsonify({"error": "Expected list of transactions"}), 400

    try:
        insert_transactions(DB_PATH, txs)
        return jsonify({"message": f"Successfully added {len(txs)} transactions to Site A"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transactions', methods=['GET'])
def get_txs():
    """
    API truy vấn danh sách giao dịch.
    Nếu truyền tham số `block_id`: Chỉ lấy giao dịch trong block đó.
    Nếu không truyền: Trả về toàn bộ giao dịch từ trước tới nay.
    """
    block_id = request.args.get('block_id')
    try:
        if block_id is not None:
            txs = get_transactions_by_block(DB_PATH, int(block_id))
        else:
            txs = get_all_transactions(DB_PATH)
        return jsonify(txs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/leaf-hashes', methods=['GET'])
def get_leaf_hashes_api():
    """
    API truy vấn danh sách mã băm lá (Leaf Hashes) của một block cụ thể.
    Trả về danh sách các cặp {"TransactionID": ..., "hash": ...} phục vụ đối chứng kiểm toán.
    """
    block_id = request.args.get('block_id')
    if block_id is None:
        return jsonify({"error": "Missing block_id"}), 400

    try:
        txs = get_transactions_by_block(DB_PATH, int(block_id))
        hashes = []
        for tx in txs:
            hashes.append({
                "TransactionID": tx['TransactionID'],
                "hash": hash_transaction(tx)
            })
        return jsonify(hashes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Site A chạy trên cổng 5001
    app.run(host='127.0.0.1', port=5001, debug=True)
