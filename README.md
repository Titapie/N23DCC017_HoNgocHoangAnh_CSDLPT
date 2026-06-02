# Merkle Tree Log Integrity: "Immutable Audit Trail" (Đề tài 105)

## THÔNG TIN SINH VIÊN THỰC HIỆN
* **Họ và tên:** Hồ Ngọc Hoàng Anh
* **Mã số sinh viên:** N23DCCN071
* **Lớp:** D23CQCN02-N
* **Môn học:** Cơ sở dữ liệu phân tán
* **Học viện:** Học viện Công nghệ Bưu chính Viễn thông (PTIT)

---

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
Dự án được thiết kế theo cấu trúc mô-đun hóa rõ ràng, phân tách rõ vai trò của các node trong môi trường phân tán:
```text
d:/CSDL_PhanTan/
├── run_all.py                 # Khởi chạy đồng bộ 4 Flask nodes (Terminal 1)
├── core/                      # Thư viện dùng chung
│   ├── __init__.py            # Khởi tạo package
│   ├── database.py            # Cấu hình SQLite DB cho các Site A, B và TTP
│   └── merkle.py              # Hiện thực thuật toán xây dựng Merkle Tree và Merkle Proof
├── nodes/                     # Mã nguồn microservices giả lập phân tán
│   ├── coordinator.py         # Node điều phối giao dịch, replication và Web UI Dashboard (Port 5000)
│   ├── site_a.py              # Node Site A (Bản sạch đối chứng, Port 5001)
│   ├── site_b.py              # Node Site B (Bản chi nhánh nghi ngờ bị tấn công, Port 5002)
│   └── ttp.py                 # Node Trusted Third Party lưu trữ Root Hashes bất biến (Port 5003)
├── scripts/                   # Công cụ CLI bổ trợ và kiểm thử (Terminal 2)
│   ├── generator.py           # Sinh dữ liệu ngân hàng mẫu sạch ban đầu (500 giao dịch)
│   ├── detector.py            # Kiểm toán toàn vẹn, so khớp Root Hash & Leaf Hash để định vị lỗi
│   ├── attack.py              # Giả lập tấn công sửa đổi, xóa hoặc chèn giao dịch vào SQLite Site B
│   ├── benchmark.py           # Đo lường hiệu năng của Merkle Tree trên các kích thước block khác nhau
│   ├── view_db.py             # Xem dữ liệu nhanh của từng database
│   └── convert_md_to_html_doc.py # Xuất báo cáo markdown sang định dạng Word (.doc) chuẩn PTIT
├── static/                    # Tài nguyên tĩnh của Frontend Dashboard
│   ├── css/style.css          # Định kiểu giao diện Glassmorphism và Dark Mode
│   └── js/app.js              # Gửi request API, vẽ Merkle Tree trên Canvas và biểu đồ hiệu năng
├── templates/
│   └── index.html             # Giao diện Web Dashboard chính
├── reports/                   # Thư mục chứa các tài liệu báo cáo học thuật
│   ├── final_report.md        # File Markdown của báo cáo cuối kỳ (6 Chương chuẩn PTIT)
│   ├── Bao_Cao_Do_An_CSDLPT_N23DCCN071.pdf # Báo cáo cuối kỳ bản PDF chính thức
│   ├── Project_proposal.pdf   # Đề xuất dự án bản PDF chính thức
│   └── design_document.pdf    # Tài liệu thiết kế hệ thống bản PDF chính thức
├── requirements.txt           # Danh sách thư viện phụ thuộc (Flask, requests)
└── .gitignore                 # Bỏ qua tệp nhị phân Word (*.doc, *.docx), DB local (*.db) và .venv
```

---

## 6. Cam Kết Học Thuật & Chống Trùng Lặp
* **Tính nguyên bản (Authenticity):** Toàn bộ mã nguồn, cấu trúc thuật toán Merkle Tree và tài liệu báo cáo của đồ án được sinh viên **Hồ Ngọc Hoàng Anh (MSSV: N23DCCN071)** tự thực hiện và cấu trúc hóa độc lập, không sao chép từ bất kỳ nguồn mã nguồn có sẵn nào khác.
* **Cá nhân hóa mã nguồn (Authorship Headers):** Tất cả các file mã nguồn (`.py`, `.js`, `.css`, `.html`) trong dự án đều được chèn khối comment định danh thông tin sinh viên ở đầu tệp tin nhằm mục đích xác nhận bản quyền và phục vụ các công cụ quét trùng lặp mã nguồn của giảng viên.
* **Tài liệu đối chiếu:** Các báo cáo PDF lưu trong thư mục `reports/` được biên soạn dựa trên giáo trình của **Özsu & Valduriez** nhằm đối chiếu lý thuyết một cách học thuật và chặt chẽ nhất.


