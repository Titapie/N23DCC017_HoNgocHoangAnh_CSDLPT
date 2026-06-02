# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN01-N
#
# Tệp tin: nodes/ttp.py - Cung cấp API dịch vụ Trusted Third Party (TTP)
# ==============================================================================
import sys
import os
from flask import Flask, request, jsonify

# Bổ sung thư mục cha vào đường dẫn tìm kiếm hệ thống để có thể import package 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import init_db, insert_block_hash, get_block_hashes, get_block_hash_by_id

app = Flask(__name__)
# Đường dẫn vật lý lưu tệp cơ sở dữ liệu SQLite của TTP
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/ttp.db'))

# Khởi tạo CSDL cho TTP (chế độ 'ttp' - chỉ tạo bảng Block_Hashes lưu Root Hash bất biến)
init_db(DB_PATH, 'ttp')

@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint kiểm tra trạng thái hoạt động (Health Check) của Node TTP.
    Trả về thông tin kết nối và đường dẫn CSDL SQLite.
    """
    return jsonify({"status": "healthy", "node": "ttp", "db": DB_PATH})

@app.route('/root-hash', methods=['POST'])
def add_root_hash():
    """
    API đăng ký mã băm gốc (Root Hash) cho một Block khi hoàn thành 100 giao dịch.
    Đầu vào (JSON): BlockID, StartTxID, EndTxID, RootHash, Timestamp.
    Đầu ra (JSON): Trạng thái lưu trữ thành công hoặc báo lỗi 500.
    """
    data = request.json
    required = ["BlockID", "StartTxID", "EndTxID", "RootHash", "Timestamp"]
    # Kiểm tra xem yêu cầu gửi lên có đầy đủ các trường bắt buộc không
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Ghi đè hoặc chèn mới Root Hash của block này vào bảng Block_Hashes của TTP
        insert_block_hash(
            DB_PATH,
            int(data['BlockID']),
            data['StartTxID'],
            data['EndTxID'],
            data['RootHash'],
            data['Timestamp']
        )
        return jsonify({"message": f"Successfully stored root hash for Block {data['BlockID']}"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/root-hash/<int:block_id>', methods=['GET'])
def get_root_hash(block_id):
    """
    API truy vấn mã băm gốc (Root Hash) của một block cụ thể theo BlockID.
    Sử dụng để đối chứng trong giải thuật kiểm toán.
    """
    try:
        row = get_block_hash_by_id(DB_PATH, block_id)
        if row:
            return jsonify(row)
        return jsonify({"error": f"Block {block_id} not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/root-hashes', methods=['GET'])
def get_all_root_hashes():
    """
    API lấy toàn bộ danh sách các Root Hash đã đăng ký ở TTP.
    """
    try:
        hashes = get_block_hashes(DB_PATH)
        return jsonify(hashes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Node TTP chạy trên cổng 5003
    app.run(host='127.0.0.1', port=5003, debug=True)
