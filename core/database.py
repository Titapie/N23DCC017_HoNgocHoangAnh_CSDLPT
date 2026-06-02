# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN02-N
#
# Tệp tin: core/database.py - Khởi tạo và quản lý kết nối cơ sở dữ liệu SQLite
# ==============================================================================
import sqlite3
import os

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Tạo kết nối tới cơ sở dữ liệu SQLite cục bộ tại đường dẫn db_path.
    Cấu hình row_factory = sqlite3.Row để kết quả truy vấn trả về có thể truy cập 
    dưới dạng dictionary (key-value) thay vì tuple thông thường (dễ đọc và xử lý hơn).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str, site_type: str):
    """
    Khởi tạo cấu trúc bảng (schema) cho cơ sở dữ liệu vật lý.
     site_type: 
      - 'site': Dành cho Site A (Bản sạch) và Site B (Bản chi nhánh). 
                Tạo bảng lưu nhật ký giao dịch ngân hàng: `Banking_Transactions`.
      - 'ttp': Dành cho Trusted Third Party. 
               Tạo bảng lưu trữ các Root Hash bất biến của từng khối: `Block_Hashes`.
    """
    # Đảm bảo thư mục cha của tệp database đã tồn tại (nếu chưa có thì tự động tạo)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    if site_type == 'site':
        # Bảng giao dịch tài chính: lưu các trường cơ bản của giao dịch chuyển tiền
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Banking_Transactions (
                TransactionID TEXT PRIMARY KEY, -- Mã giao dịch duy nhất
                From_Account TEXT NOT NULL,      -- Tài khoản chuyển đi
                To_Account TEXT NOT NULL,        -- Tài khoản nhận
                Amount REAL NOT NULL,            -- Số tiền giao dịch
                Timestamp TEXT NOT NULL,         -- Thời gian giao dịch phát sinh
                BlockID INTEGER NOT NULL         -- Số ID của khối giao dịch (nhóm 100 giao dịch/khối)
            )
        ''')
        # Tạo Index trên trường BlockID để tối ưu hóa hiệu năng khi truy vấn dữ liệu theo khối
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_id ON Banking_Transactions(BlockID)')
        
    elif site_type == 'ttp':
        # Bảng của Bên thứ ba trung lập (TTP): Chỉ lưu trữ mã băm gốc (Root Hash) để đối chứng toàn vẹn
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Block_Hashes (
                BlockID INTEGER PRIMARY KEY,     -- Số thứ tự khối giao dịch
                StartTxID TEXT NOT NULL,         -- Mã giao dịch bắt đầu của khối
                EndTxID TEXT NOT NULL,           -- Mã giao dịch kết thúc của khối
                RootHash TEXT NOT NULL,          -- Root Hash mật mã đại diện cho cả khối
                Timestamp TEXT NOT NULL          -- Thời điểm đăng ký Root Hash
            )
        ''')

    conn.commit()
    conn.close()

def insert_transactions(db_path: str, transactions: list):
    """
    Chèn danh sách các giao dịch (transactions) vào bảng `Banking_Transactions` của Site.
    Sử dụng lệnh `INSERT OR REPLACE` để cập nhật lại nếu giao dịch trùng TransactionID đã tồn tại.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    for tx in transactions:
        cursor.execute('''
            INSERT OR REPLACE INTO Banking_Transactions 
            (TransactionID, From_Account, To_Account, Amount, Timestamp, BlockID)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            tx['TransactionID'],
            tx['From_Account'],
            tx['To_Account'],
            tx['Amount'],
            tx['Timestamp'],
            tx['BlockID']
        ))
    conn.commit()
    conn.close()

def get_transactions_by_block(db_path: str, block_id: int) -> list:
    """
    Truy vấn toàn bộ danh sách giao dịch thuộc về một khối (block_id) cụ thể.
    Dữ liệu trả ra được sắp xếp tăng dần theo `TransactionID` để đảm bảo khi xây dựng
    cây Merkle Tree, thứ tự các lá luôn nhất quán (nếu sai thứ tự băm sẽ bị lệch).
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT TransactionID, From_Account, To_Account, Amount, Timestamp, BlockID
        FROM Banking_Transactions
        WHERE BlockID = ?
        ORDER BY TransactionID ASC
    ''', (block_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_transactions(db_path: str) -> list:
    """
    Lấy toàn bộ tất cả giao dịch trong database, sắp xếp tuần tự theo thứ tự BlockID và TransactionID.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT TransactionID, From_Account, To_Account, Amount, Timestamp, BlockID
        FROM Banking_Transactions
        ORDER BY BlockID ASC, TransactionID ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def insert_block_hash(db_path: str, block_id: int, start_tx: str, end_tx: str, root_hash: str, timestamp: str):
    """
    Đăng ký Root Hash bất biến của một khối giao dịch vào cơ sở dữ liệu của TTP.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO Block_Hashes
        (BlockID, StartTxID, EndTxID, RootHash, Timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (block_id, start_tx, end_tx, root_hash, timestamp))
    conn.commit()
    conn.close()

def get_block_hashes(db_path: str) -> list:
    """
    Lấy toàn bộ danh sách Root Hash các khối đang được đăng ký tại TTP.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT BlockID, StartTxID, EndTxID, RootHash, Timestamp FROM Block_Hashes ORDER BY BlockID ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_block_hash_by_id(db_path: str, block_id: int) -> dict:
    """
    Truy vấn Root Hash của một khối cụ thể bằng BlockID tại TTP.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT BlockID, StartTxID, EndTxID, RootHash, Timestamp FROM Block_Hashes WHERE BlockID = ?', (block_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
