# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 3c1lop3a
**Thành viên:** Võ Doanh Nhân (2A202602770) · Ngô Minh Trí · Nguyễn Thanh Dương
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định và dịch vụ **thư viện đại học** — VinUniversity Library (đúng ràng buộc L3A: dịch vụ/quy định đại học).

**Tại sao nhóm chọn chủ đề này?**

> Tiêu chí chọn của nhóm không phải "chủ đề nào hay" mà là **"chủ đề nào cho phép tách `audience` thành nhiều giá trị khác nhau trên cùng một nội dung"**. Ràng buộc L3A yêu cầu ít nhất một benchmark query phải *cần* `metadata_filter={"audience": "student"}` mới trả lời đúng; nếu corpus chỉ toàn `audience: student` thì filter không có gì để lọc và cả phần đánh giá trở nên vô nghĩa.
>
> Quy định thư viện thoả điều kiện đó tốt hơn mọi mảng khác: **cùng một câu hỏi "được mượn bao lâu" có bốn đáp án khác nhau** tuỳ đối tượng — sinh viên đại học 2 tuần, học viên sau đại học 1 tháng, giảng viên 6 tháng, nhân viên 2 tuần. Bốn tài liệu này dùng gần như y hệt từ vựng (`Circulation privilege`, `loan period`, `renewal`) nên embedding **không thể tự phân biệt**, buộc metadata phải làm việc thật.
>
> Ngoài ra nguồn VinUni rất phù hợp về mặt kỹ thuật: văn bản có cấu trúc mục rõ ràng (thuận cho chiến lược chunk theo heading), nhiều con số cụ thể và kiểm chứng được (20.000 VND/ngày, 19 phòng, 2 giờ/lượt) nên gold answer không phải suy đoán.

### Danh sách tài liệu (Data Inventory)

Thu thập bằng `scripts/fetch_public_pages.py` (kiểm `robots.txt`, giãn ≥1 giây/request), sau đó **làm sạch thủ công** để loại menu điều hướng, breadcrumb và footer. Xem `data/thu-vien/sources.csv`.

| # | Tên tài liệu (`doc_id`) | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `muon-tai-lieu-sinh-vien-dai-hoc` | library.vinuni.edu.vn/borrowing-priviledge/ | 2026-09-19 / not-stated | 1.224 | `audience=student`, `user_group=undergraduate`, `category=borrowing` |
| 2 | `muon-tai-lieu-hoc-vien-sau-dai-hoc` | library.vinuni.edu.vn/borrowing-priviledge/ | 2026-09-19 / not-stated | 737 | `audience=student`, `user_group=graduate`, `category=borrowing` |
| 3 | `dat-phong-hoc-nhom` | library.vinuni.edu.vn/room-booking/ | 2026-09-19 / not-stated | 1.176 | `audience=student`, `category=facilities` |
| 4 | `muon-tai-lieu-giang-vien` | policy.vinuni.edu.vn/all-policies/library-policies-for-users/ | 2026-09-19 / POL-LLR-001-V4.0 | 948 | `audience=faculty`, `category=borrowing` |
| 5 | `muon-tai-lieu-nhan-vien-va-giang-vien-lien-ket` | policy.vinuni.edu.vn/all-policies/library-policies-for-users/ | 2026-09-19 / POL-LLR-001-V4.0 | 909 | `audience=staff`, `category=borrowing` |
| 6 | `doi-tuong-khong-duoc-muon` | policy.vinuni.edu.vn/all-policies/library-policies-for-users/ | 2026-09-19 / POL-LLR-001-V4.0 | 698 | `audience=all`, `user_group=visitor-guest-alumni` |
| 7 | `phan-loai-tai-lieu-duoc-muon` | library.vinuni.edu.vn/borrowing-priviledge/ | 2026-09-19 / not-stated | 1.483 | `audience=all`, `category=borrowing` |
| 8 | `phi-phat-qua-han` | library.vinuni.edu.vn/faq/ | 2026-09-19 / not-stated | 1.923 | `audience=all`, `category=fines` |
| 9 | `gio-mo-cua-va-quyen-ra-vao` | library.vinuni.edu.vn/about-us/hours-and-access/ | 2026-09-19 / not-stated | 1.154 | `audience=all`, `category=access` |
| 10 | `quy-dinh-chung-va-an-toan` | policy.vinuni.edu.vn/all-policies/library-policies-for-users/ | 2026-09-19 / POL-LLR-001-V4.0 | 2.151 | `audience=all`, `category=policy` |

**Phân bố `audience`:** `student` = 3 · `all` = 5 · `faculty` = 1 · `staff` = 1 → **4 giá trị khác nhau**, đủ để `metadata_filter` có việc thật.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ. Toàn bộ là trang công khai của VinUniversity, không có nội dung sau đăng nhập.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated`) trong metadata. `sources.csv` khớp 1-1 với 10 file `.md`.
- [x] `robots.txt` của cả `library.vinuni.edu.vn` và `policy.vinuni.edu.vn` đều là `User-agent: * / Disallow:` (cho phép toàn bộ) — đã kiểm trực tiếp trước khi crawl.
- [x] Không bịa `document_version`: chỉ 4 tài liệu lấy từ trang policy mới ghi `POL-LLR-001-V4.0` (số hiệu do chính nguồn nêu), 6 tài liệu còn lại ghi `not-stated`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | enum | `student` / `faculty` / `staff` / `all` | **Trường quan trọng nhất.** Bốn tài liệu hạn mức mượn dùng cùng từ vựng nên embedding không phân biệt được; `audience` là chiều duy nhất tách đúng/sai theo đối tượng hỏi. |
| `user_group` | enum | `undergraduate` / `graduate` / `faculty` / `staff` | Tách mịn hơn `audience`. Cần vì cả sinh viên đại học (2 tuần) lẫn học viên sau đại học (1 tháng) đều là `student` nhưng khác đáp án. |
| `category` | enum | `borrowing` / `fines` / `access` / `facilities` / `policy` | Lọc theo loại câu hỏi. Câu hỏi về tiền phạt không cần lẫn với câu hỏi đặt phòng. |
| `doc_id` | string | `phi-phat-qua-han` | Trỏ về **file gốc** (không phải id chunk `file#3`). Cho phép `delete_document()` xoá cả cụm chunk và cho phép truy vết câu trả lời về đúng tài liệu. |
| `source_url` | url | `https://library.vinuni.edu.vn/faq/` | Agent in kèm trong ngữ cảnh → đáp ứng tiêu chí *Source Traceability*. Với corpus quy định thì truy nguồn là bắt buộc, không phải tuỳ chọn. |
| `document_version` | string | `POL-LLR-001-V4.0` / `not-stated` | Kiểm tra độ mới. Quy định thư viện có thể đổi theo năm học; không có version thì không biết câu trả lời còn hiệu lực không. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(body, chunk_size=900)` trên 3 tài liệu (đã **bỏ frontmatter** trước khi đo, nếu không là đang đo cả khối YAML):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `muon-tai-lieu-sinh-vien-dai-hoc` | FixedSizeChunker (`fixed_size`) | 2 | 656 | ❌ Cắt giữa mục `## Renewal conditions` |
| | SentenceChunker (`by_sentences`) | 4 | 304 | ⚠️ Giữ câu trọn vẹn nhưng tách rời bảng khỏi tiêu đề |
| | RecursiveChunker (`recursive`) | 2 | 610 | ⚠️ Tôn trọng đoạn nhưng vẫn gộp 2 mục khác nhau |
| | **HeadingChunker (của Nhân)** | **5** | **243** | ✅ Mỗi mục quy định là một chunk trọn vẹn |
| `phi-phat-qua-han` | FixedSizeChunker | 3 | 701 | ❌ Bảng phí bị xé giữa hàng |
| | SentenceChunker | 4 | 478 | ⚠️ Bảng Markdown bị coi là một "câu" khổng lồ |
| | RecursiveChunker | 3 | 639 | ⚠️ Giữ bảng nhưng mất tiêu đề mục |
| | **HeadingChunker** | **4** | **479** | ✅ `## Overdue fines` giữ trọn cả bảng phí |
| `quy-dinh-chung-va-an-toan` | FixedSizeChunker | 3 | 777 | ❌ |
| | SentenceChunker | 6 | 356 | ⚠️ |
| | RecursiveChunker | 3 | 715 | ⚠️ |
| | **HeadingChunker** | **6** | **357** | ✅ |

**Đọc bảng:** HeadingChunker cho **chunk nhiều hơn và ngắn hơn** (243–479 ký tự so với 610–777 của recursive/fixed). Thoạt nhìn chunk ngắn có vẻ bất lợi, nhưng với văn bản quy định thì ngược lại: mỗi chunk tương ứng đúng **một điều khoản**, nên khi lọt top-k nó mang theo trọn vẹn quy tắc chứ không phải nửa quy tắc này cộng nửa quy tắc kia.

### Chiến lược của từng thành viên

**Thành viên 1 — Võ Doanh Nhân**
- **Loại chiến lược:** `HeadingChunker` — **custom**, chunk theo tiêu đề/mục (vai bắt buộc của nhóm theo ràng buộc L3A)
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản quy định được **người soạn** chia sẵn theo mục (`## Overdue fines`, `## Renewal conditions`), mỗi mục đã là một đơn vị ngữ nghĩa trọn vẹn. Cắt theo ranh giới đó giữ nguyên ý định của tác giả, thay vì cắt theo số ký tự vô tình xé đôi một điều khoản. Chi tiết dễ bỏ sót mà tôi có xử lý: khi một mục dài quá `max_chars` phải hạ xuống recursive, tôi **gắn lại tiêu đề vào từng mảnh con** — không có bước này, mảnh thứ hai trở đi chỉ còn `"20,000 VND / day"` mà mất ngữ cảnh "đây là phí gì".
- **Code snippet:**
```python
class HeadingChunker:
    HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.M)

    def __init__(self, max_chars: int = 900) -> None:
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        starts = [m.start() for m in self.HEADING.finditer(text)]
        if not starts:
            return self._fallback.chunk(text)      # khong co heading -> ha xuong recursive
        if starts[0] > 0:
            starts.insert(0, 0)                    # giu phan mo dau truoc heading dau tien

        sections = []
        for i, start in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else len(text)
            if text[start:end].strip():
                sections.append(text[start:end].strip())

        chunks = []
        for section in sections:
            if len(section) <= self.max_chars:
                chunks.append(section)
                continue
            lines = section.splitlines()
            heading = lines[0].strip() if self.HEADING.match(lines[0]) else ""
            body = "\n".join(lines[1:]) if heading else section
            for piece in self._fallback.chunk(body):
                # GAN LAI TIEU DE vao tung manh con
                chunks.append(f"{heading}\n\n{piece}".strip() if heading else piece)
        return [c for c in chunks if c.strip()]
```

**Thành viên 2 — Ngô Minh Trí**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=900)` — dùng class có sẵn, tinh chỉnh tham số
- **Mô tả & lý do chọn:** *(chờ thành viên bổ sung)* — Kết quả đối chứng do Nhân chạy sẵn bằng `python bench.py --strategy recursive` đã có trong `ket_qua_benchmark.txt` để Trí đối chiếu.
- **Code snippet (nếu custom):** không, dùng class trong `src/chunking.py`

**Thành viên 3 — Nguyễn Thanh Dương**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=900, overlap=150)` — đường cơ sở có overlap
- **Mô tả & lý do chọn:** *(chờ thành viên bổ sung)* — Kết quả đối chứng chạy bằng `python bench.py --strategy fixed`, đã có trong `ket_qua_benchmark.txt`.
- **Code snippet (nếu custom):** không, dùng class trong `src/chunking.py`

> **Ghi chú trung thực về tiến độ nhóm:** tính đến thời điểm nộp, Trí và Dương chưa gửi lại kết quả chạy của mình. Để phần so sánh vẫn có số liệu thật thay vì bỏ trống, Nhân đã chạy **cả bốn chiến lược trên cùng corpus, cùng 5 query, cùng backend embedding** — chỉ đổi đúng một dòng chọn chunker như quy ước. Các con số dưới đây vì vậy là so sánh *giữa các chiến lược*, chưa phải so sánh *giữa các máy của từng người*.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Số chunk | Độ dài TB | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|---------|-----------|----------------------|-----------|----------|
| Võ Doanh Nhân | **HeadingChunker** | **41** | **300** | **10/10** | Mỗi chunk = một điều khoản trọn vẹn; thắng Q3 nhờ giữ nguyên mục `## Renewal conditions` | Phụ thuộc văn bản có heading; corpus không cấu trúc sẽ phải rơi về recursive |
| Ngô Minh Trí | RecursiveChunker | 20 | 618 | 9/10 | Chunk dài, ngữ cảnh dày, ít phân mảnh | Gộp nhiều mục vào một chunk → Q3 lấy nhầm tài liệu tiền phạt |
| Nguyễn Thanh Dương | FixedSizeChunker (overlap 150) | 20 | 694 | 9/10 | Overlap cứu được thông tin nằm vắt ngang ranh giới | Cắt giữa bảng Markdown, chunk mất tính đọc được |
| *(đối chứng)* | SentenceChunker | 23 | 536 | 9/10 | Câu luôn trọn vẹn | Coi cả bảng Markdown là "một câu" khổng lồ (max 1.063 ký tự, vượt cả giới hạn) |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> **HeadingChunker thắng, nhưng chênh lệch chỉ đúng 1 điểm và nằm gọn ở một câu hỏi — chính chỗ đó mới đáng nói.**
>
> Bốn chiến lược đều đạt 2/2 ở Q1, Q2, Q4, Q5. Khác biệt duy nhất là **Q3: *"Can I renew a book that is already overdue?"***. Với recursive và fixed, top-1 và top-2 đều là tài liệu `phi-phat-qua-han` (+0.6908, +0.6674) — **đúng chủ đề "quá hạn" nhưng không chứa quy tắc gia hạn**; tài liệu gold chỉ lọt hạng 3, và chunk lọt được lại là đoạn nói về *recall* chứ không phải *renewal*. Ngữ cảnh trả về **không hề chứa** chuỗi `"cannot be renewed"`, nên agent không có căn cứ để trả lời "Không".
>
> HeadingChunker thắng vì mục `## Renewal conditions` trong tài liệu gốc chứa **cả hai vế** — "renewal period is half of the original loan period... only allowed if there has been no request" **và** "Overdue items cannot be renewed" — và chunker giữ nguyên cả mục làm một chunk. Ba chiến lược kia cắt ở ranh giới ~900 ký tự rơi vào giữa hai vế đó.
>
> **Bài học tổng quát hơn điểm số:** với văn bản quy định, ranh giới ngữ nghĩa **đã được người soạn đánh dấu sẵn bằng heading**. Chiến lược nào tôn trọng dấu đó thì thắng; chiến lược nào áp một con số ký tự tuỳ ý lên trên thì thỉnh thoảng cắt trúng chỗ hiểm. Nếu đổi sang chủ đề không có cấu trúc mục (email hỗ trợ, transcript hội thoại), HeadingChunker sẽ tự rơi về recursive và lợi thế biến mất — đây không phải chiến lược tốt phổ quát, mà là chiến lược **khớp với hình dạng của dữ liệu**.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> Đúng 5 câu, đa dạng dạng hỏi, gold answer **trích được từ tài liệu**, không suy đoán quy định của trường. Khai báo trong `bench.py` để mọi thành viên chạy cùng một bộ.

| # | Câu hỏi (Query) | Dạng | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|------|-------------------------------|--------------------------|
| 1 | *How long is my loan period and how many items can I borrow?* **(cần `metadata_filter={"audience":"student"}`)** | tra số liệu | Sinh viên đại học: **3 cuốn, 2 tuần**, gia hạn 1 lần. Học viên sau đại học: **5 cuốn, 1 tháng**, gia hạn 1 lần. **Không phải 6 tháng** — đó là hạn mức giảng viên. | `muon-tai-lieu-sinh-vien-dai-hoc#1`, `muon-tai-lieu-hoc-vien-sau-dai-hoc#1` (mục `## Circulation privilege`) |
| 2 | *How much is the overdue fine per day for a normal book?* | tra số liệu | **20.000 VND / ngày quá hạn / tài liệu** với tài liệu thường. Tài liệu course-specific và thiết bị tính **20.000 VND / GIỜ**. | `phi-phat-qua-han#1` (mục `## Overdue fines`) |
| 3 | *Can I renew a book that is already overdue?* | hỏi điều kiện (có/không) | **Không.** Tài liệu quá hạn không được gia hạn. Gia hạn chỉ được phép khi chưa có người khác yêu cầu, và thời hạn gia hạn bằng **một nửa** thời hạn mượn gốc. | `muon-tai-lieu-sinh-vien-dai-hoc#2` (mục `## Renewal conditions`) |
| 4 | *How long can a group book a study room and how far in advance?* | hỏi quy trình + giới hạn | Tối đa **2 giờ/lượt, 2 lượt/ngày, 4 lượt/tuần** tính chung mọi phòng. Đặt trước tối đa **1 tuần**. Nhóm phải có ít nhất 2 người. Không đến trong **10 phút** đầu thì mất lượt. | `dat-phong-hoc-nhom#0`, `#2` |
| 5 | *Which library materials cannot be borrowed and must be read in the library?* | liệt kê | **Reference materials và print journals** không được mượn (uncirculated), chỉ đọc tại thư viện. Sách Course Reserve mượn được nhưng chỉ **02 giờ**, 01 cuốn/người/lượt. | `phan-loai-tai-lieu-duoc-muon#0` (bảng phân loại) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).
>
> **Nhóm chấm ở hai mức, không chỉ một.** Kiểm `doc_id` gold có trong top-3 là chưa đủ — một chiến lược có thể chiếm cả ba slot từ đúng tài liệu mà không chunk nào chứa câu trả lời. Nên mỗi query khai báo thêm một **chuỗi đặc trưng bắt buộc** (`must_contain`) và `bench.py` kiểm chuỗi đó có thật trong ngữ cảnh truy xuất được hay không.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Loan period (cần filter) | Cả 4 đều 2/2 | ✅ top-1, score +0.7272 | Nhưng **chỉ khi có filter** — xem A/B bên dưới |
| 2 | Overdue fine | Cả 4 đều 2/2 | ✅ top-1, score +0.7964 | Score cao nhất bộ; câu hỏi có từ khoá đặc trưng "overdue fine" |
| 3 | Renew when overdue | **Chỉ HeadingChunker đạt 2/2** | ✅ heading top-1 (+0.7563) / ❌ recursive & fixed chỉ 1 điểm | **Câu phân loại chiến lược.** Xem phân tích lỗi mục 4 |
| 4 | Study room booking | Cả 4 đều 2/2 | ✅ top-1, score +0.7853 | Tài liệu riêng biệt, không cạnh tranh với ai |
| 5 | Materials cannot borrow | Cả 4 đều 2/2 | ✅ top-1, score +0.7284 | |

**Tổng điểm theo chiến lược:** HeadingChunker **10/10** · RecursiveChunker 9/10 · FixedSizeChunker 9/10 · SentenceChunker 9/10.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> **Có, và chỉ ở Q1 — nhưng ở đó nó quyết định đúng/sai chứ không phải hay/dở.** Chạy A/B trên cùng chiến lược heading:
>
> | Hạng | **CÓ** `metadata_filter={"audience":"student"}` | **KHÔNG** filter |
> |---|---|---|
> | 1 | `muon-tai-lieu-sinh-vien-dai-hoc#1` (+0.7272) `student` | `muon-tai-lieu-sinh-vien-dai-hoc#1` (+0.7272) `student` |
> | 2 | `muon-tai-lieu-hoc-vien-sau-dai-hoc#1` (+0.7214) `student` | `muon-tai-lieu-hoc-vien-sau-dai-hoc#1` (+0.7214) `student` |
> | 3 | `muon-tai-lieu-hoc-vien-sau-dai-hoc#2` (+0.6965) `student` | **`muon-tai-lieu-giang-vien#1` (+0.7002) `faculty`** ⚠️ |
>
> Không lọc, slot thứ 3 bị tài liệu **giảng viên** chiếm — nó ghi *"5 items, 6 months"*. Sinh viên đọc câu trả lời dựa trên ngữ cảnh đó có thể kết luận mình được mượn 6 tháng, **sai gấp 12 lần** so với 2 tuần thực tế.
>
> Con số đáng chú ý nhất: chênh lệch score giữa chunk faculty (+0.7002) và chunk graduate (+0.6965) chỉ là **0.0037**. Hai tài liệu này nói cùng chủ đề, dùng cùng từ vựng, chỉ khác đối tượng áp dụng — embedding **không có cách nào** phân biệt được ở mức chênh lệch đó. Đây chính xác là khoảng trống mà metadata lấp vào: **similarity phân biệt theo chủ đề, metadata phân biệt theo đối tượng.**
>
> Ở Q2–Q5 filter không cần thiết vì mỗi câu chỉ có một tài liệu ứng viên thật sự. Nhóm coi đó là kết quả đúng chứ không phải thiếu sót — lọc khi không cần chỉ làm tăng nguy cơ loại nhầm.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Hai cách chấm cho kết quả khác nhau, và cách dễ hơn thì sai.** Nếu chỉ kiểm `doc_id` gold có trong top-3, cả bốn chiến lược đều 10/10 và buổi lab không học được gì. Kiểm thêm chuỗi đặc trưng trong ngữ cảnh mới lộ ra Q3 phân loại được chiến lược. Chênh lệch giữa hai cách chấm là phát hiện đáng giá nhất của nhóm.
2. **Metadata filter cứu đúng một câu, nhưng là câu mà sai thì hậu quả lớn nhất.** Hai chunk cách nhau 0.0037 điểm cosine mà một cái đúng một cái sai hoàn toàn với người hỏi — similarity không thể tự giải quyết, phải có chiều dữ liệu khác.
3. **Chunker tốt nhất là chunker khớp hình dạng dữ liệu, không phải chunker "xịn" nhất.** HeadingChunker thắng vì văn bản quy định có heading; đổi sang transcript hội thoại là nó tự rơi về recursive và mất sạch lợi thế.

**Phân tích lỗi (Failure Analysis) — bắt buộc ≥1 ca**

**Ca lỗi: Q3 — *"Can I renew a book that is already overdue?"* với `RecursiveChunker` và `FixedSizeChunker`.**

- **Hỏng thế nào:** top-3 trả về `phi-phat-qua-han#0` (+0.6908), `phi-phat-qua-han#1` (+0.6674), `muon-tai-lieu-sinh-vien-dai-hoc#1` (+0.6630). Hai vị trí đầu là tài liệu **tiền phạt**, vị trí thứ ba tuy đúng tài liệu gold nhưng chunk lọt được lại nói về *recall* chứ không phải *renewal*. Ngữ cảnh không chứa `"cannot be renewed"` → agent không có căn cứ trả lời "Không".
- **Tại sao:** câu hỏi chứa từ `"overdue"`, và tài liệu `phi-phat-qua-han` **dày đặc từ đó** ("overdue fine", "overdue items", "30 days after the due date"). Cosine đo **độ giống chủ đề**, không đo **mật độ thông tin trả lời được** — nên chunk nói rất nhiều về "quá hạn" nhưng không trả lời được câu hỏi vẫn thắng chunk chứa đúng một câu đáp án. Cộng thêm việc cắt ở ~900 ký tự rơi đúng vào giữa hai vế của mục `## Renewal conditions`, tách rời "gia hạn = ½ thời hạn, chỉ khi chưa ai yêu cầu" khỏi "tài liệu quá hạn không được gia hạn".
- **Đề xuất cải thiện:** (a) chunk theo heading để mục quy định không bị xé — đã chứng minh hiệu quả, đưa Q3 từ 1 lên 2 điểm; (b) nếu phải giữ chunker theo kích thước thì tăng `overlap` lên ≥ 250 để vùng giáp ranh được nhân bản; (c) về lâu dài, similarity đơn thuần không đủ cho câu hỏi dạng có/không — cần thêm một bước re-rank kiểm xem chunk có chứa **mệnh đề trả lời được** hay không, chứ không chỉ có cùng chủ đề.

**Một quan sát dữ liệu ngoài lề nhưng đáng ghi:** hai nguồn chính thức của cùng một trường **mâu thuẫn nhau về giờ mở cửa** — trang `library.vinuni.edu.vn` ghi thứ 2–6 mở lúc **8:45**, trong khi văn bản `POL-LLR-001-V4.0` trên `policy.vinuni.edu.vn` ghi **8:00**. Nhóm **cố ý không tự chọn một con số**, mà giữ cả hai trong hai tài liệu riêng kèm `source_url` và `document_version` của chúng. Đây là lý do thực tế để bắt agent trích dẫn nguồn: khi nguồn mâu thuẫn, việc đúng không phải chọn hộ người đọc mà là chỉ ra cả hai và cho biết mỗi con số đến từ đâu.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng corpus, cùng 5 câu hỏi, cùng backend embedding, bốn chiến lược chỉ chênh nhau **1 điểm trên 10** — và toàn bộ chênh lệch nằm ở **một câu duy nhất**. Điều đó nói rằng phần lớn câu hỏi trong lab này "dễ" với mọi chiến lược, vì mỗi câu chỉ có một tài liệu ứng viên thật sự. Chiến lược chunking chỉ trở nên quan trọng đúng ở chỗ **hai tài liệu cạnh tranh nhau, hoặc câu trả lời nằm sát ranh giới cắt**. Nếu nhóm chỉ viết 5 câu hỏi "dễ" thì sẽ kết luận nhầm rằng chọn chunker thế nào cũng như nhau.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> **Một:** thiết kế câu hỏi khó hơn ngay từ đầu. 4/5 câu của nhóm chỉ có một tài liệu ứng viên nên không phân loại được chiến lược. Lần sau nhóm sẽ cố ý viết nhiều câu mà **hai tài liệu cùng cạnh tranh**, như Q1 đã làm với `audience`.
>
> **Hai:** họp chốt corpus và bộ query **trước** khi ai đó bắt đầu code, thay vì để một người dựng sẵn rồi chia lại. Lần này do không họp kịp, phần so sánh giữa các thành viên phải thay bằng so sánh giữa các chiến lược chạy trên cùng một máy — vẫn có số liệu thật nhưng mất đi góc nhìn "mỗi người hiểu dữ liệu khác nhau thì chọn tham số khác nhau".
>
> **Ba:** bổ sung tài liệu tiếng Việt. Corpus hiện tại toàn tiếng Anh vì nguồn VinUni công khai là tiếng Anh, trong khi câu hỏi thật của sinh viên sẽ đặt bằng tiếng Việt. Nhóm chưa kiểm được chất lượng truy xuất **xuyên ngôn ngữ**, dù `gemini-embedding-001` là mô hình đa ngữ và về lý thuyết làm được.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | — (chấm tại buổi demo) |
| **Tổng phần nhóm** | **34 / 35 + demo** |

> Tự trừ 1 điểm ở Strategy Design vì phần "so sánh giữa các thành viên" hiện là so sánh giữa các chiến lược do một người chạy, chưa có số liệu độc lập từ Trí và Dương.
