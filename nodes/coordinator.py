# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN02-N
#
# Tệp tin: nodes/coordinator.py - API Coordinator, Web Dashboard & Eager Replication
# ==============================================================================
import sys
import os
import requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime

# Bổ sung thư mục cha vào đường dẫn hệ thống để có thể import package 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.merkle import MerkleTree, hash_transaction, compare_leaf_hashes

app = Flask(__name__, 
            template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates')),
            static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../static')))

# Định nghĩa địa chỉ mạng vật lý của các Site và Trusted Third Party (TTP)
SITE_A_URL = "http://127.0.0.1:5001"
SITE_B_URL = "http://127.0.0.1:5002"
TTP_URL = "http://127.0.0.1:5003"

@app.route('/')
def index():
    """Giao diện chính Web Dashboard."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Endpoint kiểm tra sức khỏe của Coordinator."""
    return jsonify({"status": "healthy", "node": "coordinator"})

@app.route('/api/health', methods=['GET'])
def check_all_health():
    """
    KIỂM TRA TRẠNG THÁI TOÀN HỆ THỐNG PHÂN TÁN.
    Coordinator sẽ gửi yêu cầu HTTP GET kiểm tra health check tới từng node con 
    (Site A, Site B, TTP) ở phía backend để tránh lỗi chặn CORS trên trình duyệt của Client.
    """
    nodes = {
        "coord": "http://127.0.0.1:5000/health",
        "a": "http://127.0.0.1:5001/health",
        "b": "http://127.0.0.1:5002/health",
        "ttp": "http://127.0.0.1:5003/health"
    }
    results = {}
    for name, url in nodes.items():
        if name == "coord":
            results[name] = True
            continue
        try:
            res = requests.get(url, timeout=1.0)
            results[name] = res.status_code == 200
        except Exception:
            results[name] = False
    return jsonify(results)

@app.route('/api/transaction', methods=['POST'])
def add_transaction_api():
    # API nhan giao dich moi tu nguoi dung, sau do nhan ban sang cac site
    data = request.json
    from_acc = data.get('From_Account')
    to_acc = data.get('To_Account')
    amount = data.get('Amount')

    if not all([from_acc, to_acc, amount]):
        return jsonify({"error": "Missing From_Account, To_Account, or Amount"}), 400

    try:
        # Lay tat ca giao dich tu Site A de dem va tinh ID tiep theo
        res_a = requests.get(f"{SITE_A_URL}/transactions")
        if res_a.status_code != 200:
            return jsonify({"error": "Failed to connect to Site A"}), 500
            
        all_txs = res_a.json()
        current_count = len(all_txs)
        
        # Tao ma giao dich tu dong: TX-100001, TX-100002...
        new_tx_num = 100001 + current_count
        new_tx_id = f"TX-{new_tx_num}"
        timestamp = datetime.now().isoformat()
        
        # Chia block (moi block dung 100 dong giao dich)
        block_id = (current_count // 100) + 1
        
        tx_payload = {
            "TransactionID": new_tx_id,
            "From_Account": from_acc,
            "To_Account": to_acc,
            "Amount": float(amount),
            "Timestamp": timestamp,
            "BlockID": block_id
        }
        
        # Nhan ban ghi dong thoi den ca Site A va B (ROWA)
        res_write_a = requests.post(f"{SITE_A_URL}/transaction", json=tx_payload)
        res_write_b = requests.post(f"{SITE_B_URL}/transaction", json=tx_payload)
        
        # Neu 1 trong 2 site bi loi thi huy luon de bao ve tinh nhat quan
        if res_write_a.status_code != 201 or res_write_b.status_code != 201:
            return jsonify({"error": "Eager replication failed to one or more nodes"}), 500
            
        completed_block_id = None
        root_hash_stored = False
        
        # Nếu block này đạt đúng giao dịch thứ 100 -> Tiến hành đóng block và sinh Merkle Tree
        if (current_count + 1) % 100 == 0:
            completed_block_id = block_id
            
            # Lấy 100 giao dịch của block vừa hoàn thành
            res_block_txs = requests.get(f"{SITE_A_URL}/transactions?block_id={block_id}")
            block_txs = res_block_txs.json()
            
            # Dựng Merkle Tree và tính Root Hash
            tree = MerkleTree(block_txs)
            root_hash = tree.get_root_hash()
            
            start_tx = block_txs[0]['TransactionID']
            end_tx = block_txs[-1]['TransactionID']
            
            # Đăng ký Root Hash lên TTP
            ttp_payload = {
                "BlockID": block_id,
                "StartTxID": start_tx,
                "EndTxID": end_tx,
                "RootHash": root_hash,
                "Timestamp": datetime.now().isoformat()
            }
            res_ttp = requests.post(f"{TTP_URL}/root-hash", json=ttp_payload)
            if res_ttp.status_code == 201:
                root_hash_stored = True

        return jsonify({
            "message": "Transaction recorded successfully",
            "transaction": tx_payload,
            "block_completed": completed_block_id,
            "root_hash_stored": root_hash_stored
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions_proxy():
    """API Proxy trung chuyển truy vấn danh sách giao dịch của Site A hoặc Site B từ Web Dashboard."""
    site = request.args.get('site', 'a').lower()
    block_id = request.args.get('block_id')
    
    target_url = SITE_A_URL if site == 'a' else SITE_B_URL
    url = f"{target_url}/transactions"
    if block_id:
        url += f"?block_id={block_id}"
        
    try:
        res = requests.get(url)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ttp/hashes', methods=['GET'])
def get_ttp_hashes_proxy():
    """API Proxy lấy danh sách Root Hash từ TTP về Web UI."""
    try:
        res = requests.get(f"{TTP_URL}/root-hashes")
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/merkle-tree/<int:block_id>', methods=['GET'])
def get_merkle_tree_visual_api(block_id):
    """
    API Sinh dữ liệu Cây Merkle trực quan để vẽ lên Canvas HTML5 của Frontend.
    Trả về cấu trúc các Layer mã băm của cây để vẽ các đường nối và nút tròn tương tác.
    """
    site = request.args.get('site', 'a').lower()
    target_url = SITE_A_URL if site == 'a' else SITE_B_URL
    
    try:
        res = requests.get(f"{target_url}/transactions?block_id={block_id}")
        if res.status_code != 200:
            return jsonify({"error": "Failed to retrieve block transactions"}), 500
            
        txs = res.json()
        if not txs:
            return jsonify({"error": f"No transactions found for block {block_id}"}), 404
            
        # Khởi tạo cây Merkle Tree để phân tách các tầng
        tree = MerkleTree(txs)
        
        # Lấy cấu trúc phân tầng băm
        layers = []
        current_nodes = tree.leaves
        while True:
            layers.append([n.hash for n in current_nodes])
            if len(current_nodes) == 1:
                break
            next_level = []
            for i in range(0, len(current_nodes), 2):
                left = current_nodes[i]
                if i + 1 < len(current_nodes):
                    right = current_nodes[i + 1]
                else:
                    right = left
                combined = hash_data_dummy(left.hash + right.hash)
                next_level.append(DummyNode(combined))
            current_nodes = next_level
            
        return jsonify({
            "block_id": block_id,
            "root_hash": tree.get_root_hash(),
            "layers": layers,
            "transactions": txs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def hash_data_dummy(data: str) -> str:
    import hashlib
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

class DummyNode:
    def __init__(self, hash_val):
        self.hash = hash_val

@app.route('/api/audit', methods=['GET'])
def get_audit_result_api():
    """
    API KIỂM TOÁN VÀ ĐIỀU TRA SAI KHÁC (AUDIT DETECTOR API).
    Quy trình kiểm toán toàn vẹn:
      1. Lấy toàn bộ Root Hash đã đăng ký bất biến từ TTP.
      2. Với mỗi Block, lấy danh sách giao dịch hiện có từ Site B (nơi nghi bị phá hoại).
      3. Dựng Merkle Tree cục bộ của Site B và tính toán lại Root Hash cục bộ.
      4. SO SÁNH ROOT HASH:
         Nếu Local Root Hash B != Root Hash lưu tại TTP:
           a. Tải bản sao CSDL sạch đối chứng của Site A làm mốc so sánh.
           b. Lấy danh sách Leaf Hashes của cả 2 bên.
           c. Chạy hàm đối chiếu `compare_leaf_hashes` để tìm ra danh sách các TransactionID bị:
              - Sửa (MODIFIED)
              - Xóa (DELETED)
              - Chèn khống (INJECTED)
           d. Đối chiếu chi tiết bản ghi giữa Site A và Site B để bóc tách rõ: 
              tên trường bị thay đổi, giá trị gốc sạch, và giá trị bị sửa đổi phá hoại.
      5. Trả về kết quả pháp y chi tiết để hiển thị giao diện báo động đỏ trực quan.
    """
    try:
        res_ttp = requests.get(f"{TTP_URL}/root-hashes")
        if res_ttp.status_code != 200:
            return jsonify({"error": "Failed to connect to TTP server"}), 500
        ttp_blocks = res_ttp.json()
        
        checked_blocks = 0
        tampered_blocks = []
        forensics = []
        
        for block in ttp_blocks:
            block_id = block['BlockID']
            ttp_root = block['RootHash']
            checked_blocks += 1
            
            res_b = requests.get(f"{SITE_B_URL}/transactions?block_id={block_id}")
            if res_b.status_code != 200:
                continue
            txs_b = res_b.json()
            
            # Tính toán Root Hash cục bộ từ CSDL Site B
            root_b = MerkleTree(txs_b).get_root_hash()
            
            # Nếu phát hiện sai lệch Root Hash so với TTP
            if root_b != ttp_root:
                tampered_blocks.append(block_id)
                
                # Tải CSDL sạch của Site A
                res_a = requests.get(f"{SITE_A_URL}/transactions?block_id={block_id}")
                txs_a = res_a.json() if res_a.status_code == 200 else []
                
                # Trích xuất mã băm lá
                hashes_a = [{"TransactionID": tx['TransactionID'], "hash": hash_transaction(tx)} for tx in txs_a]
                hashes_b = [{"TransactionID": tx['TransactionID'], "hash": hash_transaction(tx)} for tx in txs_b]
                
                # Chạy giải thuật so khớp lá tìm các kiểu thay đổi cụ thể
                diff = compare_leaf_hashes(hashes_a, hashes_b)
                
                block_details = {
                    "BlockID": block_id,
                    "TTP_Root": ttp_root,
                    "SiteB_Root": root_b,
                    "Details": []
                }
                
                txs_a_dict = {tx['TransactionID']: tx for tx in txs_a}
                txs_b_dict = {tx['TransactionID']: tx for tx in txs_b}
                
                # 1. Chi tiết các giao dịch bị sửa đổi dữ liệu (MODIFIED)
                for tx_id in diff["modified"]:
                    tx_a = txs_a_dict[tx_id]
                    tx_b = txs_b_dict[tx_id]
                    diff_fields = {}
                    for field in ['From_Account', 'To_Account', 'Amount', 'Timestamp']:
                        if tx_a[field] != tx_b[field]:
                            diff_fields[field] = {
                                "Original": tx_a[field],
                                "Modified": tx_b[field]
                            }
                    block_details["Details"].append({
                        "Type": "MODIFIED",
                        "TransactionID": tx_id,
                        "Original": tx_a,
                        "Modified": tx_b,
                        "Diff": diff_fields
                    })
                    
                # 2. Chi tiết các giao dịch bị xóa trái phép (DELETED)
                for tx_id in diff["deleted"]:
                    tx_a = txs_a_dict[tx_id]
                    block_details["Details"].append({
                        "Type": "DELETED",
                        "TransactionID": tx_id,
                        "Original": tx_a,
                        "Modified": None,
                        "Diff": {"status": "Deleted from Site B"}
                    })
                    
                # 3. Chi tiết các giao dịch bị chèn lậu (INJECTED)
                for tx_id in diff["injected"]:
                    tx_b = txs_b_dict[tx_id]
                    block_details["Details"].append({
                        "Type": "INJECTED",
                        "TransactionID": tx_id,
                        "Original": None,
                        "Modified": tx_b,
                        "Diff": {"status": "Injected into Site B"}
                    })
                    
                if not diff["mismatch"] and len(txs_a) != len(txs_b):
                    block_details["Details"].append({
                        "Type": "ROW_COUNT_MISMATCH",
                        "TransactionID": "N/A",
                        "Original": {"row_count": len(txs_a)},
                        "Modified": {"row_count": len(txs_b)},
                        "Diff": {"status": f"Site A has {len(txs_a)} rows, Site B has {len(txs_b)} rows"}
                    })
                    
                forensics.append(block_details)
                
        status = "tampered" if tampered_blocks else "clean"
        return jsonify({
            "status": status,
            "checked_blocks": checked_blocks,
            "tampered_blocks_count": len(tampered_blocks),
            "tampered_blocks": tampered_blocks,
            "forensics": forensics
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/seed', methods=['POST'])
def run_seed_via_api():
    """API giúp kích hoạt tiến trình sinh CSDL 500 bản ghi mẫu từ giao diện Web Dashboard."""
    import subprocess
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, '../scripts/generator.py')
    try:
        # Chạy file generator.py bằng Python đang thực thi
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True)
        return jsonify({"message": "Successfully seeded database", "logs": res.stdout}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/benchmark', methods=['POST'])
def run_benchmark_via_api():
    """API chạy đo đạc thời gian sinh cây và dung lượng overhead từ giao diện Web Dashboard."""
    import subprocess
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, '../scripts/benchmark.py')
    try:
        # Chạy file benchmark.py để sinh dữ liệu JSON vẽ đồ thị hiệu năng
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True)
        return jsonify({"message": "Successfully ran benchmark", "logs": res.stdout}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Coordinator chạy trên cổng 5000 phục vụ Dashboard
    app.run(host='127.0.0.1', port=5000, debug=True)
