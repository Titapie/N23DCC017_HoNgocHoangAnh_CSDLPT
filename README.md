# Merkle Tree Log Integrity: "Immutable Audit Trail" (Đề tài 105)

Đồ án môn học **Cơ sở dữ liệu phân tán** thực hiện giải pháp bảo mật và kiểm toán dữ liệu phân tán sử dụng cấu trúc **Merkle Tree (Cây Hash)** để phát hiện các cuộc tấn công thay đổi dữ liệu từ bên trong (Insider Attack/Rogue DBA) trên nhật ký giao dịch ngân hàng.

---

## 1. Kiến Trúc Hệ Thống
Hệ thống giả lập môi trường phân tán thực tế gồm 4 node microservices chạy trên localhost giao tiếp qua HTTP/REST APIs:
* **Coordinator (Port 5000):** Cổng giao tiếp chính, xử lý giao dịch người dùng và nhân bản đồng bộ (Eager Replication ROWA) đến Site A và Site B. Khi block đủ 100 giao dịch, Coordinator tự động dựng Merkle Tree và đăng ký Root Hash sang TTP. Cung cấp giao diện Web Dashboard quản lý. **Lưu ý:** Node này hiện tại là điểm lỗi duy nhất (SPOF); trong tương lai cần được phát triển áp dụng giao thức đồng thuận phân tán Raft hoặc PBFT để giải quyết tính sẵn sàng cao.
* **Site A (Port 5001):** Lưu trữ CSDL sạch đóng vai trò bản sao đối chứng đáng tin cậy (`data/site_a.db`) dùng để truy vết (forensics) chi tiết TransactionID.
* **Site B (Port 5002):** Chi nhánh lưu trữ CSDL là mục tiêu giả lập tấn công Insider Attack (`data/site_b.db`). Kẻ tấn công can thiệp trực tiếp bằng lệnh SQL bypass API kiểm soát.
* **Trusted Third Party - TTP (Port 5003):** Bên thứ ba trung lập lưu trữ Root Hash bất biến của các block giao dịch (`data/ttp.db`) để kiểm toán tính toàn vẹn chung.

---

## 2. Công Nghệ Sử Dụng
* **Ngôn ngữ:** Python 3.10+
* **Framework:** Flask (Python REST API)
* **CSDL local:** SQLite (chân thực hóa hành vi Insider can thiệp SQL trực tiếp vào tệp DB)
* **Frontend:** HTML5, CSS3 (Glassmorphism design system), Javascript (AJAX, Canvas render cho Merkle Tree), Chart.js (vẽ đồ thị hiệu năng).

---

## 3. Hướng Dẫn Cài Đặt và Khởi Chạy (Trên Windows)

### Bước 1: Khởi tạo và kích hoạt môi trường ảo
```bash
python -m venv .venv
# Trên Windows CMD: .\.venv\bin\activate
# Trên Windows PowerShell: .\.venv\bin\Activate.ps1
```

### Bước 2: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 3: Khởi chạy giao diện Web Dashboard phân tán (Terminal 1)
Để hệ thống hoạt động đầy đủ tính năng phân tán (Site A, Site B, TTP, Coordinator), hãy khởi chạy đồng bộ 4 node ở **Terminal 1**:
```bash
python run_all.py
```
*Lưu ý: Lệnh này chạy ở chế độ chặn (blocking) và sẽ tiếp tục giữ cổng kết nối cho các node. Không đóng terminal này trong suốt quá trình demo.*

### Bước 4: Khởi động luồng chạy thử nghiệm bằng CLI (Terminal 2)
Mở một **Terminal thứ hai** (Terminal 2), di chuyển vào thư mục dự án và kích hoạt môi trường ảo (`.\.venv\bin\activate` hoặc `.\.venv\bin\Activate.ps1`), sau đó thực thi lần lượt các lệnh sau:

1. **Khởi tạo dữ liệu sạch (Database sạch ban đầu):**
   ```bash
   python scripts/generator.py
   ```
2. **Kiểm tra trạng thái toàn vẹn dữ liệu ban đầu:**
   ```bash
   python scripts/detector.py
   ```
3. **Thực hiện tấn công giả lập Update (Sửa Amount của TX-100150 từ 100.00 thành 1000.00):**
   ```bash
   python scripts/attack.py --type update --transaction-id TX-100150 --amount 1000
   ```
4. **Chạy detector để phát hiện và định vị lỗi:**
   ```bash
   python scripts/detector.py
   ```
5. **Thực hiện tấn công giả lập Delete (Xóa giao dịch TX-100120):**
   ```bash
   python scripts/attack.py --type delete --transaction-id TX-100120
   ```
6. **Chạy detector phát hiện lỗi xóa:**
   ```bash
   python scripts/detector.py
   ```
7. **Thực hiện tấn công giả lập Insert (Chèn giao dịch giả mạo TX-FAKE vào Block 3):**
   ```bash
   python scripts/attack.py --type insert --transaction-id TX-FAKE --block 3
   ```
8. **Chạy detector phát hiện lỗi chèn:**
   ```bash
   python scripts/detector.py
   ```
9. **Chạy đo đạc Benchmarks:**
   ```bash
   python scripts/benchmark.py
   ```

### Bước 5: Truy cập Dashboard trên trình duyệt
Sau khi khởi chạy `run_all.py`, bạn có thể truy cập Web UI trực quan tại:
```text
http://127.0.0.1:5000
```
*(Cho phép seeding, thực hiện các kiểu tấn công trực tiếp bằng giao diện và xem hiển thị đồ thị cây Merkle sinh động).*

---

## 4. Expected Output Mẫu (Cho 4 Ca Kiểm Thử)

### Case 1: Normal State (Trạng thái sạch ban đầu)
Chạy lệnh `python scripts/detector.py` trên database sạch:
```text
Audit Result: SAFE
Checked blocks: 5
Tampered blocks: 0
```

### Case 2: Update Attack (Sửa Amount giao dịch TX-100150)
Chạy lệnh `python scripts/detector.py` sau khi sửa amount giao dịch TX-100150 thành 1000:
```text
Audit Result: TAMPERED
BlockID: 2
TransactionID: TX-100150
Changed field: Amount
Site A value: 100.00
Site B value: 1000.00
Root Hash from TTP: 5b002a250f33d97176149a731f2bd487b8ee5227ac5655b0b31c1dbc9645f8de
Recomputed Site B Root Hash: 1291cb7c493e9e254e40db986b8c678ad4c480a2d68165d60ed3de1bb8960788

Tampered TransactionID: TX-100150
Field changed: Amount
Clean value at Site A: 100.00
Tampered value at Site B: 1000.00
BlockID: 2
```

### Case 3: Delete Attack (Xóa giao dịch TX-100120)
Chạy lệnh `python scripts/detector.py` sau khi xóa giao dịch TX-100120 ở Site B:
```text
Audit Result: TAMPERED
Issue type: row_count_mismatch / deleted_transaction
Deleted TransactionID: TX-100120
BlockID: 2
```

### Case 4: Insert Attack (Chèn giao dịch giả mạo TX-FAKE)
Chạy lệnh `python scripts/detector.py` sau khi chèn giao dịch TX-FAKE vào Block 3 ở Site B:
```text
Audit Result: TAMPERED
Issue type: fake_transaction / inserted_transaction
Inserted TransactionID: TX-FAKE
BlockID: 3
```

---

## 5. Cấu Trúc Thư Mục Dự Án
Các tài liệu báo cáo của môn học được lưu trữ tại thư mục `reports/`:
* `reports/project_proposal.md` — Đề xuất dự án.
* `reports/design_document.md` — Tài liệu thiết kế hệ thống chi tiết 2 trang.
* `reports/final_report.md` — Báo cáo đồ án môn học chi tiết bằng tiếng Việt.

