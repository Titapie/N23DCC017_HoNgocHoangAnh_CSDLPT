import sys
import os
from flask import Flask, request, jsonify

# Bổ sung thư mục cha vào đường dẫn tìm kiếm hệ thống để import package 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import init_db, insert_transactions, get_transactions_by_block, get_all_transactions, get_db_connection
from core.merkle import hash_transaction
from datetime import datetime

app = Flask(__name__)
# Đường dẫn vật lý lưu tệp cơ sở dữ liệu SQLite của Site B (Bản chi nhánh nghi ngờ bị tấn công)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_b.db'))

# Khởi tạo CSDL cho Site B (chế độ 'site' - tạo bảng Banking_Transactions)
init_db(DB_PATH, 'site')

@app.route('/health', methods=['GET'])
def health():
    """
    API kiểm tra trạng thái hoạt động (Health Check) của Site B.
    """
    return jsonify({"status": "healthy", "node": "site_b", "db": DB_PATH})

@app.route('/transaction', methods=['POST'])
def add_transaction():
    """
    API tiếp nhận giao dịch từ Coordinator (phục vụ Eager Replication).
    """
    tx = request.json
    required = ["TransactionID", "From_Account", "To_Account", "Amount", "Timestamp", "BlockID"]
    if not all(k in tx for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        insert_transactions(DB_PATH, [tx])
        return jsonify({"message": f"Transaction {tx['TransactionID']} added to Site B"}), 201
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
        return jsonify({"message": f"Successfully added {len(txs)} transactions to Site B"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transactions', methods=['GET'])
def get_txs():
    """
    API truy vấn danh sách giao dịch ở Site B.
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
    API truy vấn danh sách mã băm lá (Leaf Hashes) của một block cụ thể tại Site B.
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

@app.route('/simulate-attack', methods=['POST'])
def simulate_attack_api():
    """
    GIẢ LẬP TẤN CÔNG NỘI BỘ (Insider Attack / Rogue DBA).
    ENDPOINT NÀY CAN THIỆP TRỰC TIẾP LÊN DATABASE SQLITE CỦA SITE B,
    BYPASS HOÀN TOÀN COORDINATOR VÀ CÁC THỦ TỤC BẢO MẬT API.
    
    Các kiểu hành vi tấn công (Action):
      - 'modify': Thay đổi số tiền (Amount) của một giao dịch cụ thể.
      - 'delete': Xóa hẳn một giao dịch cụ thể khỏi database của Site B.
      - 'inject': Chèn một giao dịch giả mạo (Fake Transaction) trực tiếp vào một Block.
    """
    data = request.json
    action = data.get('Action', '').lower()
    tx_id = data.get('TransactionID')
    
    if not action:
        return jsonify({"error": "Action parameter is required"}), 400
        
    try:
        # Kết nối thô trực tiếp tới cơ sở dữ liệu SQLite của Site B
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        
        # ---------------- Ca kiểm thử 1: SỬA ĐỔI DỮ LIỆU (UPDATE) ----------------
        if action == 'modify':
            if not tx_id or 'Amount' not in data:
                conn.close()
                return jsonify({"error": "TransactionID and Amount are required for modify"}), 400
            
            # Kiểm tra xem giao dịch có tồn tại thực sự hay không
            cursor.execute("SELECT Amount FROM Banking_Transactions WHERE TransactionID = ?", (tx_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({"error": f"Transaction {tx_id} not found"}), 404
                
            # Thực hiện thay đổi giá trị số tiền Amount trực tiếp
            cursor.execute("UPDATE Banking_Transactions SET Amount = ? WHERE TransactionID = ?", (float(data['Amount']), tx_id))
            conn.commit()
            conn.close()
            return jsonify({"message": f"Successfully tampered amount of {tx_id} to ${data['Amount']}"}), 200
            
        # ---------------- Ca kiểm thử 2: XÓA DỮ LIỆU (DELETE) ----------------
        elif action == 'delete':
            if not tx_id:
                conn.close()
                return jsonify({"error": "TransactionID is required for delete"}), 400
                
            # Kiểm tra sự tồn tại của giao dịch trước khi xóa
            cursor.execute("SELECT * FROM Banking_Transactions WHERE TransactionID = ?", (tx_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({"error": f"Transaction {tx_id} not found"}), 404
                
            # Thực thi lệnh DELETE trực tiếp
            cursor.execute("DELETE FROM Banking_Transactions WHERE TransactionID = ?", (tx_id,))
            conn.commit()
            conn.close()
            return jsonify({"message": f"Successfully deleted transaction {tx_id}"}), 200
            
        # ---------------- Ca kiểm thử 3: CHÈN KHỐNG DỮ LIỆU (INSERT) ----------------
        elif action == 'inject':
            from_acc = data.get('From_Account', 'ACC999')
            to_acc = data.get('To_Account', 'ACC888')
            amount = float(data.get('Amount', 5000.00))
            block_id = int(data.get('BlockID', 1))
            timestamp = datetime.now().isoformat()
            new_tx_id = tx_id or f"TX-FAKE-{int(datetime.now().timestamp())}"
            
            # Thực thi câu lệnh INSERT giao dịch giả mạo
            cursor.execute('''
                INSERT INTO Banking_Transactions (TransactionID, From_Account, To_Account, Amount, Timestamp, BlockID)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (new_tx_id, from_acc, to_acc, amount, timestamp, block_id))
            conn.commit()
            conn.close()
            return jsonify({"message": f"Successfully injected transaction {new_tx_id} into Block {block_id}"}), 200
            
        else:
            conn.close()
            return jsonify({"error": f"Unknown attack action: {action}"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Site B chạy trên cổng 5002
    app.run(host='127.0.0.1', port=5002, debug=True)
