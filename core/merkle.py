# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN02-N
#
# Tệp tin: core/merkle.py - Định nghĩa cấu trúc cây Merkle và sinh Merkle Proof
# ==============================================================================
import hashlib

def hash_data(data: str) -> str:
    # Hàm băm SHA-256 cho chuỗi, trả về hexa 64 ký tự
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def serialize_transaction(tx: dict) -> str:
    # Nối các trường giao dịch thành 1 chuỗi để băm tránh lệch dữ liệu
    # Làm tròn Amount lấy 2 số thập phân (.2f) để thống nhất
    amount_val = float(tx['Amount'])
    return f"{tx['TransactionID']}|{tx['From_Account']}|{tx['To_Account']}|{amount_val:.2f}|{tx['Timestamp']}"

def hash_transaction(tx: dict) -> str:
    # Chuyển giao dịch thành chuỗi và băm để làm nút lá
    try:
        serialized = serialize_transaction(tx)
        return hash_data(serialized)
    except Exception as e:
        # Nếu lỗi thì sắp xếp key rồi nối lại làm backup
        keys = sorted(tx.keys())
        serialized = "|".join(f"{k}:{tx[k]}" for k in keys)
        return hash_data(serialized)

class MerkleNode:
    # Cấu trúc 1 Node trong cây Merkle
    def __init__(self, hash_val: str, left=None, right=None, data=None):
        self.hash = hash_val
        self.left = left
        self.right = right
        self.data = data # Chỉ lưu dữ liệu giao dịch ở nút lá để đối chứng

    def is_leaf(self) -> bool:
        # Nút lá thì không có con trái và con phải
        return self.left is None and self.right is None

class MerkleTree:
    # Class dựng và quản lý Merkle Tree
    def __init__(self, transactions: list):
        self.transactions = transactions
        # Tạo danh sách các nút lá từ giao dịch
        self.leaves = [MerkleNode(hash_transaction(tx), data=tx) for tx in transactions]
        
        if not self.leaves:
            # Nếu rỗng thì để hash rỗng làm root
            self.root = MerkleNode(hash_data(""))
        else:
            # Dựng cây từ dưới lên để lấy root node
            self.root = self._build(self.leaves)

    def _build(self, nodes: list) -> MerkleNode:
        # Thuật toán đệ quy ghép cặp băm từ dưới lên
        if len(nodes) == 1:
            # Còn 1 nút duy nhất thì chính là Root
            return nodes[0]

        next_level = []
        # Gom từng cặp 2 nút để băm lên cha
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            if i + 1 < len(nodes):
                right = nodes[i + 1]
            else:
                # Nếu số nút lẻ thì copy nút cuối cùng ghép cặp (padding)
                right = MerkleNode(left.hash, left=left.left, right=left.right, data=left.data)
            
            # Parent = hash(left + right)
            combined_hash = hash_data(left.hash + right.hash)
            parent = MerkleNode(combined_hash, left=left, right=right)
            next_level.append(parent)

        # Đệ quy lên level cao hơn
        return self._build(next_level)

    def get_root_hash(self) -> str:
        # Lấy Root Hash
        return self.root.hash

    def get_leaf_hashes(self) -> list:
        # Lấy danh sách hash của tất cả nút lá
        return [node.hash for node in self.leaves]

    def get_proof_by_index(self, index: int) -> list:
        # Sinh Merkle Proof để chứng minh giao dịch ở index có nằm trong block hay không
        if index < 0 or index >= len(self.leaves):
            return None

        proof = []
        current_level = self.leaves
        idx = index

        # Duyệt qua các tầng từ lá lên gốc
        while len(current_level) > 1:
            next_level = []
            sibling_hash = None
            direction = None

            # Dựng tầng tiếp theo tạm thời để đi lên
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = MerkleNode(left.hash)

                combined = hash_data(left.hash + right.hash)
                parent = MerkleNode(combined, left=left, right=right)
                next_level.append(parent)

            # Xác định phần tử anh em (sibling) của node hiện tại
            if idx % 2 == 0:
                # Nếu chỉ số chẵn, nút anh em nằm bên phải
                if idx + 1 < len(current_level):
                    sibling_hash = current_level[idx + 1].hash
                else:
                    sibling_hash = current_level[idx].hash
                direction = 'right'
            else:
                # Nếu chỉ số lẻ, nút anh em nằm bên trái
                sibling_hash = current_level[idx - 1].hash
                direction = 'left'

            # Thêm thông tin kiểm chứng của tầng này vào proof
            proof.append({'hash': sibling_hash, 'direction': direction})
            
            # Chuyển lên tầng trên
            current_level = next_level
            idx = idx // 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: list, root_hash: str) -> bool:
        """
        Xác minh một giao dịch (dưới dạng leaf_hash) có nằm trong block hay không.
        Bằng cách áp dụng các node anh em từ Proof để tính toán ngược lên đỉnh.
        Độ phức tạp tính toán rất tối ưu: O(log N).
        """
        current_hash = leaf_hash
        for step in proof:
            sibling = step['hash']
            direction = step['direction']
            if direction == 'left':
                current_hash = hash_data(sibling + current_hash)
            else:
                current_hash = hash_data(current_hash + sibling)
        # So sánh kết quả tính được với Root Hash gốc tại TTP
        return current_hash == root_hash

# Các hàm helper khớp với yêu cầu giao diện của dự án
def build_tree(transactions: list) -> MerkleTree:
    """Hàm dựng và trả về đối tượng MerkleTree từ danh sách giao dịch."""
    return MerkleTree(transactions)

def get_root_hash(transactions: list) -> str:
    """Lấy trực tiếp mã băm gốc Root Hash của một danh sách giao dịch."""
    tree = MerkleTree(transactions)
    return tree.get_root_hash()

def get_leaf_hashes(transactions: list) -> list:
    """Lấy danh sách mã băm nút lá của một danh sách giao dịch."""
    tree = MerkleTree(transactions)
    return tree.get_leaf_hashes()

def compare_leaf_hashes(site_a_hashes: list, site_b_hashes: list) -> dict:
    """
    Hàm đối chứng và so sánh danh sách băm nút lá giữa 2 cơ sở dữ liệu vật lý (Site A và Site B).
    Đầu vào: 
      - site_a_hashes: Danh sách mã băm lá từ Site A (Bản sạch đối chứng).
      - site_b_hashes: Danh sách mã băm lá từ Site B (Bản chi nhánh nghi bị tấn công).
    Trả về một dictionary mô tả chi tiết:
      - modified: Danh sách các TransactionID có dữ liệu bị sửa (Id tồn tại ở cả 2 bên nhưng Hash khác nhau).
      - deleted: Danh sách các TransactionID bị xóa (Có ở Site A nhưng bị mất ở Site B).
      - injected: Danh sách các TransactionID bị chèn khống (Không có ở Site A nhưng đột ngột xuất hiện ở Site B).
      - mismatch: Boolean chỉ thị xem 2 bên có sai khác dữ liệu hay không.
    """
    # Chuyển đổi list dạng dict sang dạng hashmap để tối ưu hóa tìm kiếm O(1)
    hashes_a = {item['TransactionID']: item['hash'] for item in site_a_hashes}
    hashes_b = {item['TransactionID']: item['hash'] for item in site_b_hashes}
    
    modified = []
    deleted = []
    injected = []
    
    # Duyệt qua các giao dịch ở bản sạch Site A
    for tx_id, hash_a in hashes_a.items():
        if tx_id in hashes_b:
            # Nếu giao dịch tồn tại ở cả 2 site nhưng có mã băm khác nhau -> Bị Sửa Đổi (Modified)
            if hash_a != hashes_b[tx_id]:
                modified.append(tx_id)
        else:
            # Nếu giao dịch chỉ có ở bản sạch mà mất ở Site B -> Bị Xóa (Deleted)
            deleted.append(tx_id)
            
    # Duyệt qua các giao dịch ở Site B
    for tx_id in hashes_b.keys():
        if tx_id not in hashes_a:
            # Nếu giao dịch tự dựng xuất hiện ở Site B mà không có ở bản sạch -> Bị Chèn Khống (Injected)
            injected.append(tx_id)
            
    mismatch = len(modified) > 0 or len(deleted) > 0 or len(injected) > 0
    
    return {
        "modified": modified,
        "deleted": deleted,
        "injected": injected,
        "mismatch": mismatch
    }
