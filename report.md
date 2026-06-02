# BÁO CÁO ĐỒ ÁN MÔN HỌC CƠ SỞ DỮ LIỆU PHÂN TÁN

**Đề tài 105:** Merkle Tree Log Integrity: "Immutable Audit Trail"  
**Giáo viên hướng dẫn:** [Tên Thầy]  
**Sinh viên thực hiện:** [Tên sinh viên] (CyberAuditors)  

---

## 1. Tên đề tài
**Merkle Tree Log Integrity: "Immutable Audit Trail"** (Phát Hiện Và Truy Vết Lỗi Toàn Vẹn Nhật Ký Giao Dịch Bằng Cây Merkle Phân Tán).

---

## 2. Lý do chọn đề tài
Trong các hệ thống tài chính phân tán ngày nay, nhật ký giao dịch ngân hàng (Transaction Log hay Audit Trail) là thành phần tối quan trọng để làm cơ sở pháp lý đối chiếu tài chính. Tuy nhiên, một nguy cơ bảo mật thường trực và nguy hiểm nhất là các cuộc tấn công từ nội bộ (**Insider Attacks**). Quản trị viên cơ sở dữ liệu (DBA) có quyền quản trị tối cao tại hệ thống lưu trữ vật lý của một chi nhánh ngân hàng (Site B) hoàn toàn có thể can thiệp trực tiếp vào tệp CSDL SQLite/MySQL vật lý (ví dụ: dùng câu lệnh `UPDATE` hay `DELETE` thô), thay đổi số tiền giao dịch nhằm mục đích tư lợi cá nhân. 
Việc này hoàn toàn bypass qua tất cả các cơ chế bảo mật cấp ứng dụng (như phân quyền người dùng, API Gateway, SSL). Do đó, cần có một giải pháp phân tán, mã hóa mạnh để liên tục phát hiện, ghi dấu và định vị sai sót một cách bất biến và bảo mật.

---

## 3. Bài toán cần giải quyết
Bài toán đặt ra bao gồm:
1. **Phát hiện sửa đổi dữ liệu (Detection):** Làm sao để Coordinator hoặc kiểm toán viên phát hiện ra dữ liệu tại Site B đã bị can thiệp vật lý dù chỉ sửa đổi 1 ký tự hay 1 byte dữ liệu. (Merkle Tree đóng vai trò phát hiện chứ không tự động ngăn chặn hành vi sửa đổi vật lý).
2. **Tiết kiệm tài nguyên mạng (Bandwidth Efficiency):** Không thể truyền tải định kỳ toàn bộ CSDL hàng triệu bản ghi qua mạng để kiểm tra chéo, vì chi phí băng thông quá lớn.
3. **Định vị lỗi (Forensics & Localization):** Khi phát hiện ra block bị sửa đổi, hệ thống phải chỉ ra được chính xác **TransactionID** nào bị thay đổi, giá trị gốc ban đầu là bao nhiêu và giá trị bị sửa đổi tại Site B là bao nhiêu để làm bằng chứng điều tra.
4. **Bảo mật thông tin khách hàng (Privacy):** Nơi kiểm chứng độc lập trung lập (Trusted Third Party) không được phép đọc và lưu trữ thông tin nhạy cảm của khách hàng (như số tài khoản, số tiền) mà chỉ được lưu trữ dấu vân tay cryptographic của dữ liệu (Root Hash).

---

## 4. Cơ sở lý thuyết

### Distributed DBMS
Hệ quản trị cơ sở dữ liệu phân tán (Distributed DBMS) là phần mềm quản trị một tập hợp các cơ sở dữ liệu có quan hệ logic với nhau, phân tán trên mạng máy tính và cung cấp cơ chế truy cập trong suốt với người dùng (theo Özsu & Valduriez). Dự án này chia nhỏ và phân bổ dữ liệu giao dịch trên các Site độc lập (Site A, Site B).

### Replication
Nhân bản dữ liệu (Replication) nhằm tăng tính sẵn sàng và hiệu năng truy cập. Đồ án hiện thực hóa **Eager Replication** kết hợp giao thức **ROWA (Read-One/Write-All)**. Giao dịch được nhân bản đồng thời đến cả Site A và Site B dưới sự điều phối của Coordinator.

### Consistency
Đảm bảo tính nhất quán của các bản sao (Mutual Consistency) và tính nhất quán giao dịch (Transactional Consistency - 1-Copy Serializability). Khi một site bị can thiệp vật lý bypass qua API, tính nhất quán toàn cục bị phá vỡ và hệ thống cần cơ chế phát hiện.

### Transaction log
Transaction log (Write-Ahead Log - WAL) ghi lại toàn bộ lịch sử thay đổi để đảm bảo thuộc tính bền vững (Durability) của ACID. Merkle Tree được xây dựng dựa trên chính nhật ký giao dịch nối tiếp này (Append-only).

### Data integrity
Đảm bảo dữ liệu không bị thay đổi trái phép hoặc vô tình trong suốt vòng đời. Hệ thống thực thi cơ chế ràng buộc toàn vẹn ngữ nghĩa (Semantic Integrity Control) thông qua giải pháp Auditing (phát hiện lỗi và truy vết).

### Security and privacy
Bảo mật thông tin ngân hàng. Đảm bảo dữ liệu nhạy cảm của khách hàng được che giấu khỏi bên thứ ba nhưng vẫn cho phép kiểm toán tính đúng đắn.

### Hash function
Hàm băm mật mã (SHA-256) biến đổi chuỗi đầu vào bất kỳ thành một chuỗi nhị phân có độ dài cố định (256-bit). Hàm băm có tính chất một chiều (one-way) và chống đụng độ (collision-resistance).

### Merkle Tree
Cây Merkle (Cây Hash) là cấu trúc cây nhị phân trong đó mỗi node lá chứa mã băm của một khối dữ liệu (giao dịch), và mỗi node cha chứa mã băm kết hợp của các node con:
$$ParentHash = \text{SHA256}(LeftHash + RightHash)$$
Root Hash ở đỉnh cây đại diện cho toàn bộ tập dữ liệu dưới nó.

### Trusted Third Party
Bên thứ ba đáng tin cậy (TTP) là thực thể trung lập lưu trữ Root Hash để đối chứng tính toàn vẹn dữ liệu của các site chi nhánh, làm bằng chứng pháp lý.

### Blockchain / immutable ledger
Sổ cái bất biến sử dụng liên kết mã băm nối tiếp để tạo ra nhật ký chỉ cho phép ghi (Append-only), không cho phép sửa hay xóa. Dự án này không phải là một Blockchain hoàn chỉnh mà chỉ sử dụng Merkle Tree - cấu trúc dữ liệu cốt lõi bên trong các block của Blockchain - để phục vụ mục đích kiểm toán toàn vẹn log.

---

## 5. Dataset Specification
* **Tên bảng:** `Banking_Transactions`
* **Schema:**
  * `TransactionID` (TEXT PRIMARY KEY) - Mã giao dịch duy nhất.
  * `From_Account` (TEXT) - Tài khoản chuyển tiền.
  * `To_Account` (TEXT) - Tài khoản nhận tiền.
  * `Amount` (REAL) - Số tiền giao dịch (USD).
  * `Timestamp` (TEXT) - Thời gian phát sinh giao dịch.
  * `BlockID` (INTEGER) - ID của Block chứa giao dịch.
* **Quy mô:** 500 giao dịch mẫu ban đầu được chia đều vào 5 Block (BlockID từ 1 đến 5, mỗi block đúng 100 giao dịch). Đặc biệt, giao dịch `TX-100150` ở Block 2 được khởi tạo mặc định có số tiền là `$100.00` để phục vụ demo tấn công lên `$1000.00`.

---

## 6. System Architecture
Hệ thống gồm 4 node Flask microservices chạy trên localhost giao tiếp qua HTTP/REST APIs:
1. **Coordinator (Port 5000):** Nhận giao dịch từ Client, gán metadata, thực hiện nhân bản đồng bộ (Eager Replication ROWA) đến Site A và B. Khi số lượng giao dịch đạt bội số của 100, Coordinator tự động dựng Merkle Tree và gửi Root Hash đăng ký lên TTP. Cung cấp Dashboard quản lý.
2. **Site A (Port 5001):** Lưu trữ CSDL sạch (`site_a.db`) làm bản sao đối chứng.
3. **Site B (Port 5002):** Lưu trữ CSDL bị can thiệp vật lý (`site_b.db`).
4. **TTP (Port 5003):** Lưu trữ Block ID và các Root Hash bất biến (`ttp.db`).

---

## 7. Thuật toán Merkle Tree
Trong file `core/merkle.py`, thuật toán được triển khai thủ công không sử dụng thư viện ngoài:
* **Chuẩn hóa (Normalization):** Giao dịch được chuyển thành chuỗi định dạng: `f"{TransactionID}|{From_Account}|{To_Account}|{Amount:.2f}|{Timestamp}"`. Việc định dạng `Amount` thành float với 2 chữ số thập phân đảm bảo tính nhất quán của mã băm khi đổi môi trường.
* **Gom cặp:** Ở mỗi tầng, các nút được gom cặp và băm: `hash_data(left_hash + right_hash)`. Nếu số lượng nút lẻ, nút cuối cùng được nhân đôi để đảm bảo tính chất cây nhị phân cân bằng.
* **Merkle Proof:** Tạo chuỗi các nút sibling dọc theo đường đi từ lá lên gốc để chứng minh giao dịch tồn tại trong block một cách nhanh chóng với độ phức tạp $O(\log N)$.

---

## 8. Luồng xử lý hệ thống
```
[Client] ---> POST /api/transaction ---> [Coordinator]
                                                |
                                   (Eager Replication ROWA)
                                        /               \
                                       v                 v
                                 [Site A API]      [Site B API]
                                (Ghi site_a.db)   (Ghi site_b.db)
                                       |                 |
                       Nếu đủ 100 TXs  |                 |
                        Coordinator dựng Merkle Tree     |
                                       |                 |
                                       v                 |
                              [TTP API] (Lưu Root)       |
                                                         |
[Rogue DBA] ------------> Chạy SQL can thiệp vật lý ------> (Ghi đè site_b.db)
```

---

## 9. Insider Attack tại Site B
Kẻ tấn công đóng vai quản trị viên (Rogue DBA) truy cập vật lý máy chủ Site B, mở tệp `site_b.db` và thực hiện các truy vấn:
* **Update (Sửa Amount):** Thay đổi số tiền của một giao dịch từ giá trị thực thành một giá trị khác.
* **Delete (Xóa giao dịch):** Xóa hoàn toàn một bản ghi giao dịch ra khỏi bảng.
* **Insert (Chèn giao dịch giả):** Bơm một giao dịch trái phép vào trong database của Site B.

Do các thay đổi này được thực hiện trực tiếp bằng SQL ở mức database, chúng không đi qua API nghiệp vụ nên không bị phát hiện bởi ứng dụng thông thường.

---

## 10. Tamper Detection
Quy trình phát hiện và truy vết lỗi:
1. **Quét Root Hash:** Detector gửi yêu cầu lấy tất cả Root Hashes từ TTP.
2. **Xác minh Block:** Với mỗi Block $N$, Detector lấy dữ liệu giao dịch từ Site B, dựng lại Merkle Tree cục bộ và so khớp Root Hash tính được với Root Hash lưu tại TTP.
3. **Phát hiện lỗi:** Nếu $Root_B \neq Root_{TTP}$, block đó bị TAMPERED. **Lưu ý:** Việc so sánh Root Hash ở TTP chỉ giúp phát hiện xem block đó có bị sửa đổi dữ liệu hay không (tính toàn vẹn chung) chứ không thể chỉ ra bản ghi cụ thể nào bị lỗi.
4. **Truy vết lỗi (Forensic Trace):** Để định vị chính xác TransactionID bị lỗi, hệ thống bắt buộc phải sử dụng tệp CSDL sạch của **Site A** làm đối chứng:
   * Detector yêu cầu Site A và Site B cung cấp danh sách Leaf Hash của Block $N$.
   * So sánh Leaf Hash của từng TransactionID:
     * Khác hash: Giao dịch bị **sửa đổi (MODIFIED)**. So sánh giá trị để tìm trường bị sửa.
     * Có ở A nhưng không có ở B: Giao dịch bị **xóa (DELETED)**.
     * Có ở B nhưng không có ở A: Giao dịch bị **chèn giả mạo (INJECTED)**.


---

## 11. Phân tích kịch bản sập Node (Failure Scenario)
Trong một hệ thống cơ sở dữ liệu phân tán, việc xử lý sự cố sập node là vô cùng quan trọng để kiểm soát tính toàn vẹn và tính sẵn sàng của dữ liệu. Đồ án của em giả lập hai kịch bản sập node chính:

### 11.1. Trường hợp Site B bị sập (Site B is Offline)
Khi Site B (hoặc Site A) dừng hoạt động do lỗi kết nối mạng hoặc tắt tiến trình microservice:
* **Hành vi Ghi giao dịch (Write Operations):** Hệ thống áp dụng giao thức nhân bản đồng bộ **Eager Replication** kết hợp mô hình nhất quán **ROWA (Read-One/Write-All)**. Giao dịch mới được Coordinator gửi song song đến cả Site A và Site B. Nếu một trong hai site (ví dụ: Site B) bị sập và không phản hồi, Coordinator sẽ nhận lỗi kết nối (ConnectionError) từ thư viện Python `requests`, lập tức hủy giao dịch và trả về mã lỗi `500` cho client. Điều này đảm bảo dữ liệu giữa hai site luôn đồng nhất hoàn toàn (Consistency) và không bị lệch pha, mặc dù phải hy sinh tính sẵn sàng ghi (Write Availability) theo định lý CAP.
* **Hành vi Đọc giao dịch (Read Operations):** Theo nguyên tắc ROWA, để đọc dữ liệu chỉ cần truy vấn một site bất kỳ. Nếu Site B bị sập, Coordinator vẫn có thể chuyển hướng đọc từ Site A để hiển thị danh sách giao dịch trên Dashboard một cách bình thường.
* **Hành vi Kiểm toán (Auditing):** Khi chạy script kiểm toán `detector.py` hoặc bấm nút kiểm toán trên Dashboard, hệ thống cần truy vấn dữ liệu từ Site B. Nếu Site B bị sập, quá trình kiểm toán sẽ báo lỗi kết nối và tạm ngưng.

### 11.2. Trường hợp Trusted Third Party (TTP) bị sập (TTP is Offline)
Khi node TTP (cổng 5003) gặp sự cố ngừng hoạt động:
* **Hành vi Đọc giao dịch (Read Operations):** Người dùng vẫn có thể F5 trang Dashboard và truy vấn danh sách giao dịch một cách bình thường do luồng đọc được phục vụ trực tiếp từ các site bản sao (Site A/B) mà không phụ thuộc vào TTP.
* **Hành vi Ghi giao dịch (Write Operations):** Các giao dịch lẻ (từ số 1 đến 99 của block) vẫn ghi thành công vào Site A và Site B. Tuy nhiên, khi ghi giao dịch thứ 100 (giao dịch hoàn tất đóng Block), Coordinator sẽ tự động dựng cây Merkle và gửi yêu cầu đăng ký Root Hash lên TTP. Do TTP bị sập, quá trình đăng ký này thất bại. Coordinator lập tức hủy giao dịch và trả về mã lỗi `500` cho client. Điều này ngăn chặn việc cập nhật trạng thái nếu không lưu được Root Hash bất biến, tuân thủ nguyên tắc an toàn dữ liệu tuyệt đối.
* **Hành vi Kiểm toán (Auditing):** Cả Web Dashboard và script kiểm toán `detector.py` đều báo lỗi kết nối `Failed to connect to TTP server` do không thể tải danh sách các Root Hash đã đăng ký làm chứng từ đối chiếu.

---

## 12. Benchmark & Metrics
Số liệu thực tế đo đạc từ file `scripts/benchmark.py`:
* **Thời gian dựng cây (Build Time):** Rất ngắn. 0.27 ms cho block 100 giao dịch; 6.08 ms cho block 2000 giao dịch. Tốc độ tăng trưởng tuyến tính $O(N)$.
* **Thời gian xác thực (Verify Time):** Cực kỳ nhanh ($O(\log N)$), chỉ khoảng 0.01 ms.
* **Dung lượng overhead (Storage Overhead):** Rất thấp. Với block 100 dòng (dữ liệu thô ~7 KB), TTP chỉ lưu 64 bytes Root Hash (tỷ lệ overhead ~1%). Kích thước block càng lớn, tỷ lệ overhead càng nhỏ (tiệm cận về 0%).

---

## 13. Đánh giá kết quả
Đồ án đã hiện thực thành công toàn bộ các tính năng phát hiện lỗi toàn vẹn dữ liệu:
* Phát hiện chính xác block bị sửa đổi dữ liệu qua Root Hash tại TTP.
* Truy vết chỉ điểm chính xác TransactionID bị sửa đổi, xóa hoặc chèn trái phép nhờ đối chiếu Leaf Hash với Site A.
* Trực quan hóa cấu trúc Merkle Tree động và biểu đồ hiệu năng trên Web Dashboard.

---

## 14. Hạn chế
* **Single Point of Failure (SPOF):** Node Coordinator hiện tại là điểm lỗi duy nhất trong hệ thống nhận giao dịch mới và điều phối đồng bộ. Nếu Coordinator bị sập, client không thể thực hiện giao dịch mới. Hệ thống hiện tại chưa tự động giải quyết lỗi SPOF này.
* **Bảo mật bản sao sạch:** Giải pháp định vị TransactionID dựa trên giả định Site A là bản sao sạch đáng tin cậy. Nếu kẻ tấn công có quyền truy cập root và sửa đổi đồng bộ cả Site A, Site B và TTP, hệ thống sẽ không thể truy vết.

---

## 15. Hướng phát triển
* Loại bỏ SPOF của Coordinator bằng cách áp dụng giao thức đồng thuận phân tán thực sự như **Raft** hoặc **PBFT (Practical Byzantine Fault Tolerance)** giữa các bản sao để tự động bầu chọn Coordinator mới khi xảy ra sự cố.
* Tích hợp Root Hash vào mạng lưới Blockchain phi tập trung (như Hyperledger Fabric) để đảm bảo tính bất biến tuyệt đối của Root Hash đăng ký.

---

## 16. Kết luận
Đồ án đã giải quyết bài toán phát hiện và truy vết thay đổi dữ liệu trái phép trên nhật ký giao dịch ngân hàng phân tán. Nhờ áp dụng Merkle Tree, chi phí kiểm tra toàn vẹn giảm từ $O(N)$ xuống còn $O(\log N)$, đồng thời bảo vệ quyền riêng tư của khách hàng tại TTP. Sự kết hợp giữa Eager Replication và cơ chế đối chứng Leaf Hash chéo tạo nên một giải pháp phòng ngừa nghiệp vụ và điều tra số liệu tối ưu, đáp ứng đầy đủ các tiêu chuẩn học thuật của môn học.

---

## 17. Tài liệu tham khảo
1. M. Tamer Özsu & Patrick Valduriez, *Principles of Distributed Database Systems*, 4th Edition, Springer, 2020.
2. Bài giảng môn học Cơ sở dữ liệu phân tán (Slide 1, 3, 5, 6, 9).
3. Satoshi Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System", 2008.

