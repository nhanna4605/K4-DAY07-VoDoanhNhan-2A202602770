# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Võ Doanh Nhân — MSSV 2A202602770
**Nhóm:** 3c1lop3a
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Cosine similarity đo **góc** giữa hai vector embedding chứ không đo khoảng cách giữa chúng. Điểm gần 1 nghĩa là hai vector chỉ về gần như cùng một hướng trong không gian ngữ nghĩa, tức mô hình cho rằng hai đoạn văn bản **nói về cùng một chuyện**, bất kể chúng dài ngắn khác nhau hay dùng từ ngữ khác nhau. Điểm gần 0 là không liên quan (vuông góc), gần −1 là ngược hướng.

**Ví dụ có độ tương tự CAO:**
- Câu A: *"Sinh viên phải đóng học phí trước ngày 30/9."*
- Câu B: *"Hạn chót nộp tiền học của sinh viên là cuối tháng 9."*
- Tại sao tương đồng: Hai câu **không dùng chung một từ khoá nào đáng kể** — "đóng học phí" vs "nộp tiền học", "trước ngày 30/9" vs "cuối tháng 9" — nhưng diễn đạt đúng một sự kiện. Chọn cặp khác từ vựng là có chủ ý: nếu chọn hai câu trùng từ thì điểm cao chỉ chứng minh mô hình khớp chuỗi, còn ở đây điểm cao mới chứng minh embedding thực sự **mã hoá được nghĩa**.

**Ví dụ có độ tương tự THẤP:**
- Câu A: *"Ký túc xá ưu tiên sinh viên năm nhất ở xa."*
- Câu B: *"Món phở bò Hà Nội cần ninh xương trong sáu tiếng."*
- Tại sao khác: Khác hoàn toàn cả chủ đề (quy định lưu trú vs nấu ăn), trường từ vựng, lẫn mục đích phát ngôn. Không có chiều ngữ nghĩa nào chung nên hai vector gần như vuông góc.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Vì độ dài vector trong text embedding phần lớn phản ánh **độ dài và tần suất từ của đoạn văn**, không phản ánh nghĩa. Một đoạn 50 chữ và một đoạn 500 chữ nói cùng một điều sẽ có vector cùng hướng nhưng khác độ lớn — khoảng cách Euclid sẽ phạt cặp này rất nặng còn cosine thì không, vì cosine chuẩn hoá độ dài đi và chỉ giữ lại hướng. Với retrieval, chunk dài ngắn khác nhau là chuyện thường ngày, nên đo hướng là đúng hơn đo khoảng cách.
>
> Thêm một điểm thực dụng: khi vector đã được chuẩn hoá (`‖v‖ = 1`, đúng trường hợp của `MockEmbedder` và `LocalEmbedder` trong lab này), cosine **rút gọn thành đúng phép dot product**. Đó là lý do `EmbeddingStore.search()` chỉ cần `_dot()` là đủ, không phải chia lại cho norm — nhanh hơn mà kết quả xếp hạng không đổi.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> **Trình bày phép tính:**
> Bước nhảy mỗi lần cắt là `step = chunk_size − overlap = 500 − 50 = 450` ký tự.
> Chunk đầu tiên "tiêu thụ" trọn 500 ký tự; mỗi chunk sau đó chỉ thêm 450 ký tự mới.
> `số chunk = ceil((độ_dài − overlap) / (chunk_size − overlap)) = ceil((10000 − 50) / 450) = ceil(9950 / 450) = ceil(22.11) = 23`
>
> **Đáp án: 23 chunks.**
>
> Kiểm chứng lại bằng chính `FixedSizeChunker` có sẵn trong repo thay vì tin công thức suông:
>
> ```bash
> python -c "from src.chunking import FixedSizeChunker; print(len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)))"
> # → 23   ✅ khớp công thức
> ```

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Step giảm còn `500 − 100 = 400`, nên `ceil((10000 − 100) / 400) = ceil(24.75) = **25 chunks**` — tăng 2 chunk (≈ +8.7%). Đã kiểm lại bằng `FixedSizeChunker(chunk_size=500, overlap=100)` → đúng 25.
>
> Lý do đánh đổi thêm chunk để lấy overlap lớn hơn: cắt cứng theo số ký tự **không biết câu kết thúc ở đâu**, nên một thông tin nằm vắt ngang ranh giới cắt (ví dụ "hạn nộp hồ sơ phúc khảo là **7 ngày** kể từ ngày công bố điểm") sẽ bị xé đôi và **không chunk nào chứa trọn câu trả lời** — cả hai nửa đều mất điểm khi so khớp với câu hỏi. Overlap tạo ra một bản sao của vùng giáp ranh trong chunk kế tiếp, cho mỗi thông tin **hơn một cơ hội** lọt vào top-k. Cái giá phải trả là kho vector phồng lên và top-k dễ bị chiếm bởi các chunk trùng lặp gần giống nhau.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng regex `re.compile(r"(?<=[.!?])\s+")` để cắt. Điểm mấu chốt nằm ở **lookbehind `(?<=...)`**: nếu viết thẳng `re.split(r"[.!?]\s+", text)` thì dấu câu bị coi là một phần của separator và **bị nuốt mất**, mọi chunk trở thành câu cụt không có dấu chấm. Lookbehind khớp vị trí *ngay sau* dấu câu mà không tiêu thụ ký tự nào, nên dấu chấm ở lại với câu. Dùng `\s+` thay vì `[ ]` để phủ trọn 4 trường hợp mà docstring yêu cầu (`". "`, `"! "`, `"? "`, `".\n"`) trong một biểu thức.
>
> Edge case đã xử lý: text rỗng hoặc toàn khoảng trắng trả `[]` (không crash); `.strip()` từng câu và lọc bỏ câu rỗng — cần thiết vì `SAMPLE_TEXT` kết thúc bằng `". "` nên split luôn sinh ra một phần tử rỗng ở cuối; `max(1, ...)` trong `__init__` chặn tham số 0 hoặc âm gây chia nhóm sai.
>
> **Edge case tôi biết là mình CHƯA xử lý được** (nêu ra thay vì giấu đi): regex này không phân biệt được dấu chấm kết câu với dấu chấm trong **chữ viết tắt** (`TS.`, `ThS.`, `v.v.`) và trong **số thập phân** (`2.5 triệu đồng`). Với corpus quy định đại học tiếng Việt, đây là lỗi có thật chứ không lý thuyết: một câu như *"Mức học phí là 12.500.000 đồng/học kỳ"* sẽ bị cắt thành 3 mảnh vụn. Hướng sửa nếu có thêm thời gian: thêm negative lookbehind cho danh sách viết tắt phổ biến, và yêu cầu ký tự sau khoảng trắng phải là chữ hoa thì mới coi là ranh giới câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán thử từng separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]` — cắt bằng ranh giới "to" trước để giữ trọn ngữ nghĩa, chỉ khi mảnh vẫn quá dài mới hạ xuống separator nhỏ hơn. Tôi cài đặt **hai chiều**, vì chỉ làm một chiều là lỗi phổ biến nhất:
>
> - **Chiều đệ quy xuống:** mảnh nào vẫn dài hơn `chunk_size` thì gọi lại `_split(piece, rest)` với danh sách separator còn lại.
> - **Chiều gom lên:** dùng một `buffer`, nối các mảnh nhỏ liền kề cho tới sát `chunk_size` rồi mới chốt thành một chunk. **Thiếu bước này, một file quy định nhiều dòng ngắn (danh sách gạch đầu dòng, bảng biểu) sẽ sinh ra hàng trăm chunk vụn 5–10 ký tự và retrieval hỏng hoàn toàn** — mỗi chunk quá ngắn để mang đủ ngữ cảnh, nhưng vẫn chiếm slot trong top-k.
>
> Một chi tiết tôi phải xử lý riêng: `text.split(separator)` **vứt mất separator**. Với `"\n\n"` thì không sao, nhưng với `". "` thì mất dấu chấm câu. Nên tôi gắn separator trở lại vào cuối mỗi mảnh (trừ mảnh cuối cùng) trước khi gom.
>
> **Base case — có 3 trường hợp dừng:**
> 1. Text rỗng / toàn khoảng trắng → `[]`.
> 2. `len(text) <= chunk_size` → trả luôn `[text.strip()]`, không cắt nữa.
> 3. **Hết separator** → cắt cứng theo `chunk_size` qua `_hard_split()`. Nhánh này là bắt buộc vì test `test_empty_separators_falls_back_gracefully` truyền thẳng `separators=[]`, và vì separator `""` cuối danh sách mặc định cũng phải rơi vào đây — `"abc".split("")` ném `ValueError: empty separator` nên không thể xử lý chung với các separator khác.
>
> Ngoài ra khi một separator không xuất hiện trong text (`split` trả về đúng 1 mảnh), tôi đệ quy thẳng xuống `rest` thay vì loop vô ích.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Tôi **bỏ hẳn nhánh ChromaDB**, chỉ dùng in-memory `list[dict]`. Lý do không phải lười: code khởi tạo gốc gán `self._use_chroma = True` **trước** khi client Chroma được tạo, nên nếu máy chấm bài tình cờ có `chromadb` cài sẵn thì mọi method sẽ rẽ vào nhánh chưa cài đặt và **cả 14 test store sập**. `requirements.txt` cũng không cài chromadb và không test nào cần nó.
>
> Tôi tách **hai helper trước, bốn method công khai sau**, để không lặp cùng một logic bốn lần:
> - `_make_record(doc)` chuẩn hoá 1 `Document` thành 1 record. Hai chi tiết đáng nghĩ: (a) **copy** metadata bằng `dict(doc.metadata or {})` thay vì giữ tham chiếu tới object của caller — nếu không, sửa metadata trong store sẽ sửa luôn object bên ngoài; (b) `metadata.setdefault("doc_id", doc.id)` để record **luôn** có khoá `doc_id`, vì `delete_document` phụ thuộc hoàn toàn vào nó.
> - `_search_records(query, records, top_k)` chạy similarity search trên **một tập record bất kỳ**.
>
> `add_documents` **không tự chunk** — 1 `Document` vào là 1 record ra (test đưa 3 doc và mong `get_collection_size() == 3`). Chunking xảy ra ở tầng ngoài trong `bench.py`, mỗi chunk thành một `Document` riêng.
>
> `search` chỉ là `_search_records(query, self._store, top_k)`. Vì vector đã chuẩn hoá (`‖v‖=1`) nên tôi dùng thẳng `_dot()` — bằng đúng cosine mà không tốn hai phép căn bậc hai cho mỗi record. Kết quả trả về **bỏ khoá `embedding`** đi: vector hàng trăm chiều làm bẩn output khi in ra terminal lúc chạy benchmark.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> **Lọc TRƯỚC, search SAU** — đây là quyết định thiết kế quan trọng nhất của phần này. Nếu làm ngược lại (lấy top-k rồi mới loại bỏ cái không khớp metadata), có thể **còn lại 0 kết quả dù store vẫn còn tài liệu hợp lệ**, vì k slot đã bị chiếm hết bởi tài liệu sai đối tượng. Với corpus L3A, tình huống này rất thực: tài liệu `audience: student` và `audience: faculty` nói về cùng chủ đề thư viện, dùng gần như cùng từ vựng, nên chúng cạnh tranh trực tiếp các slot top-k.
>
> Cả `search()` và `search_with_filter()` đều đi qua **cùng một đường code** `_search_records()`, chỉ khác tập ứng viên đầu vào. Nhờ vậy hai hàm không thể lệch kết quả nhau, và test `test_no_filter_returns_all_candidates` pass hiển nhiên chứ không phải nhờ may mắn.
>
> `delete_document` dựng lại danh sách chỉ giữ record có `metadata['doc_id'] != doc_id`, so sánh độ dài trước/sau để quyết định trả `True` hay `False`. Xoá theo `doc_id` chứ không theo `Document.id` là có chủ ý: ở tầng benchmark một file sinh ra nhiều chunk với id `"file#0"`, `"file#1"`, ... nhưng `doc_id` của chúng đều trỏ về **tên file gốc**, nên một lệnh xoá dọn sạch cả cụm chunk của tài liệu đó.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Ba nhịp: truy xuất top-k → dựng prompt có ngữ cảnh → gọi `llm_fn`. Phần tôi đầu tư nhiều nhất là **cách dựng ngữ cảnh**.
>
> Tôi đánh số từng chunk `[1] [2] [3]` kèm nguồn (`source_url` → `source` → `doc_id` → `id`, lấy cái đầu tiên có sẵn) và kèm luôn `audience` nếu có, rồi trong prompt yêu cầu mô hình **trích dẫn số hiệu đoạn** khi trả lời. Nhờ vậy câu trả lời **truy vết được** về đúng chunk và đúng file — đây là tiêu chí *Source Traceability* trong `docs/EVALUATION.md`. Với corpus là quy định học vụ thì nó không phải tính năng phụ: một câu trả lời về hạn nộp học phí mà không chỉ ra được nó lấy từ văn bản nào, phiên bản nào, thì không dùng được để làm căn cứ.
>
> Hai ràng buộc chống bịa trong prompt: (a) *"Chỉ sử dụng NGỮ CẢNH dưới đây, tuyệt đối không suy đoán"*; (b) *"Nếu ngữ cảnh không đủ, hãy nói rõ là không tìm thấy thông tin"*. Cái thứ hai quan trọng hơn cái thứ nhất — không có nó, mô hình có xu hướng lấp chỗ trống bằng quy định "chung chung" của các trường khác.
>
> Trường hợp store rỗng / không có kết quả: trả thẳng hằng số `EMPTY_CONTEXT_ANSWER`, **không crash và không gọi LLM vô ích** (tiết kiệm cả thời gian lẫn token khi chạy benchmark nhiều lượt).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v

============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: D:\Moitruongaocuaclaude\Lab7\K4-L3A-2A202602770-Vo-Doanh-Nhan
plugins: anyio-4.15.1, langsmith-0.12.4, asyncio-1.4.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42**

Kiểm tra bổ sung — không còn `TODO` hay `NotImplementedError` nào trong `src/`:

```bash
$ grep -rn "NotImplementedError\|TODO" src/
# (không có kết quả)
```

`main.py` chạy được từ đầu đến cuối:

```bash
$ python main.py "Chunking là gì?"
Loaded 5 documents
Embedding backend: mock embeddings fallback
Stored 5 documents in EmbeddingStore
=== EmbeddingStore Search Test ===
1. score=0.150 source=data\rag_system_design.md
2. score=0.027 source=data\python_intro.txt
3. score=0.025 source=data\chunking_experiment_report.md
=== KnowledgeBaseAgent Test ===
Agent answer: [DEMO LLM] Generated answer from prompt preview: ...
```

> Ghi chú môi trường: dòng `Skipping missing file: data/customer_support_playbook.txt` là bình thường — repo không có file đó. Trên Windows cần đặt `PYTHONIOENCODING=utf-8` trước khi chạy `main.py`, nếu không console cp1252 sẽ ném `UnicodeEncodeError` khi in nội dung tiếng Việt (lỗi hiển thị của terminal, không phải lỗi logic).

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi viết **dự đoán trước**, rồi mới chạy `compute_similarity()` trên 5 cặp câu. Tôi chạy **hai backend song song** để so sánh: `gemini-embedding-001` (3072 chiều, đã chuẩn hoá) và `MockEmbedder` (64 chiều, băm MD5).

| Cặp | Câu A | Câu B | Dự đoán | **Gemini** | Mock | Đúng? |
|------|-----------|-----------|---------|--------------|------|-------|
| 1 | Sinh viên phải đóng học phí trước ngày 30/9. | Hạn chót nộp tiền học của sinh viên là cuối tháng 9. | **cao** (paraphrase, khác từ vựng) | **+0.9083** | −0.0888 | ✅ |
| 2 | Thư viện mở cửa từ 7h30 đến 21h hàng ngày. | Giờ phục vụ của thư viện là từ 7 giờ 30 sáng tới 9 giờ tối. | **cao** (paraphrase, đổi cách viết giờ) | **+0.9193** | −0.3189 | ✅ |
| 3 | Sinh viên đăng ký học phần trên cổng học vụ. | Giảng viên nộp điểm cuối kỳ trên cổng học vụ. | **trung bình** (cùng chủ đề, khác đối tượng & hành động) | **+0.7646** | +0.0118 | ✅ |
| 4 | Ký túc xá ưu tiên sinh viên năm nhất ở xa. | Món phở bò Hà Nội cần ninh xương trong sáu tiếng. | **thấp** (không liên quan) | **+0.5389** | −0.0947 | ✅ |
| 5 | Sinh viên được phúc khảo trong 7 ngày sau khi công bố điểm. | Sinh viên **KHÔNG** được phúc khảo sau 7 ngày kể từ khi công bố điểm. | **cao** (gần trùng từ vựng, nhưng **ngược nghĩa**) | **+0.9462** | −0.1639 | ⚠️ đúng số, và đó mới là vấn đề |

Xếp hạng thực tế của Gemini: **cặp 5 (0.946) > cặp 2 (0.919) > cặp 1 (0.908) > cặp 3 (0.765) > cặp 4 (0.539)** — đúng khớp thứ tự cao / cao / trung bình / thấp mà tôi dự đoán. Nhưng hai chi tiết trong bảng làm tôi chú ý hơn cả việc dự đoán đúng.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> **Bất ngờ nhất: cặp 5 — hai câu NGƯỢC NGHĨA NHAU lại đạt điểm CAO NHẤT bảng (+0.9462), cao hơn cả hai cặp paraphrase thật (+0.9083 và +0.9193).**
>
> Hai câu này chỉ khác nhau đúng một chữ "KHÔNG", nhưng nghĩa pháp lý đảo ngược hoàn toàn: một câu *cho phép* phúc khảo trong 7 ngày, một câu *cấm* phúc khảo sau 7 ngày. Mô hình chấm chúng giống nhau hơn cả cặp "đóng học phí" ↔ "nộp tiền học" vốn thực sự đồng nghĩa. Kết luận: **cosine similarity đo độ giống về CHỦ ĐỀ, không đo giá trị chân lý.** Embedding mã hoá "câu này nói về việc phúc khảo trong thời hạn 7 ngày" rất tốt, nhưng từ phủ định gần như không ảnh hưởng tới hướng vector.
>
> Với corpus là quy định học vụ, đây không phải chuyện lý thuyết mà là **rủi ro vận hành thật**: retrieval hoàn toàn có thể trả về đúng điều khoản nhưng sai chiều phủ định, rồi agent trả lời ngược quy định mà vẫn trông "có căn cứ". Đây chính là lý do tôi bắt agent trích dẫn `[1] [2]` trỏ về đúng chunk — để người đọc còn kiểm lại được chứ không phải tin suông.
>
> **Điểm bất ngờ thứ hai: sàn điểm rất cao.** Cặp 4 — "ký túc xá" và "phở bò ninh xương" — không có một chiều ngữ nghĩa nào chung, vậy mà vẫn được **+0.5389** chứ không phải ≈0 như trực giác hình học gợi ý. Nghĩa là với embedding thật, **điểm tuyệt đối gần như vô nghĩa**; 0.54 không phải "hơi liên quan" mà là "hoàn toàn không liên quan". Chỉ có **thứ hạng tương đối giữa các ứng viên trong cùng một truy vấn** mới đọc được. Khi chấm benchmark ở mục 5, tôi vì vậy không đặt ngưỡng cứng kiểu "score > 0.7 là đạt", mà so sánh top-1 với top-2, top-3.
>
> **Đối chiếu với cột Mock:** cùng 5 cặp đó, `MockEmbedder` cho −0.0888, −0.3189, +0.0118, −0.0947, −0.1639 — **nhiễu quanh 0, không tương quan gì với nghĩa**. Hai cặp paraphrase thậm chí ra điểm *âm*, tức mock cho rằng chúng ngược hướng nhau. Lý do: mock băm MD5 rồi sinh số giả ngẫu nhiên, mà hàm băm được thiết kế để đổi một ký tự là đổi toàn bộ digest — hai câu cùng nghĩa nhưng khác một chữ sẽ ra hai vector độc lập hoàn toàn.
>
> Bài học thực tế: **phải kiểm backend embedding trước khi tin bất kỳ con số retrieval nào.** Dòng `Embedding backend: ...` mà `main.py` in ra không phải thông tin trang trí — nó quyết định toàn bộ phần benchmark có ý nghĩa hay không. Tôi cũng đã kiểm `‖v‖ = 1.0` cho vector Gemini trước khi tin rằng `dot product` trong `EmbeddingStore.search()` bằng đúng cosine, thay vì tin tài liệu suông.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của tôi trong gói `src`.

- **Corpus:** `data/thu-vien/` — 10 tài liệu quy định thư viện VinUniversity
- **Chiến lược của tôi:** `HeadingChunker` (chunk theo tiêu đề/mục), `max_chars=900`
- **Backend:** `gemini-embedding-001` (3072 chiều, đã chuẩn hoá)
- **Lệnh chạy:** `python bench.py --strategy heading` → kết quả đầy đủ trong `ket_qua_benchmark.txt`
- 10 tài liệu → **41 chunk**, độ dài chunk min=20 / trung bình=300 / max=887

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được | Score | Liên quan? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How long is my loan period and how many items can I borrow? *(cần `audience=student`)* | `muon-tai-lieu-sinh-vien-dai-hoc#1` — `## Circulation privilege` | +0.7272 | ✅ | Bảng hạn mức sinh viên: 3 cuốn / 2 tuần / gia hạn 1 lần |
| 2 | How much is the overdue fine per day for a normal book? | `phi-phat-qua-han#1` — `## Overdue fines` | +0.7964 | ✅ | 20.000 VND/ngày/tài liệu; course-specific và thiết bị tính theo GIỜ |
| 3 | Can I renew a book that is already overdue? | `muon-tai-lieu-sinh-vien-dai-hoc#2` — `## Renewal conditions` | +0.7563 | ✅ | Không — tài liệu quá hạn không được gia hạn; gia hạn = ½ thời hạn gốc và chỉ khi chưa ai yêu cầu |
| 4 | How long can a group book a study room and how far in advance? | `dat-phong-hoc-nhom#0` — `# Study room booking` | +0.7853 | ✅ | 2h/lượt, 2 lượt/ngày, 4 lượt/tuần, đặt trước tối đa 1 tuần |
| 5 | Which library materials cannot be borrowed and must be read in the library? | `phan-loai-tai-lieu-duoc-muon#0` — bảng phân loại | +0.7284 | ✅ | Reference materials và print journals uncirculated, chỉ đọc tại chỗ |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** → **10/10 điểm** theo thang `docs/SCORING.md` (cả 5 câu đều đạt 2 điểm: gold ở top-1 **và** ngữ cảnh chứa đáp án).

### Tôi chấm hai mức, không chỉ một

Cách chấm ngây thơ — kiểm `doc_id` của tài liệu gold có nằm trong top-3 không — **thổi phồng kết quả**. Một chiến lược hoàn toàn có thể chiếm cả ba slot top-3 từ đúng tài liệu gold mà **không chunk nào chứa câu trả lời**. Nên trong `bench.py` tôi khai báo cho mỗi câu hỏi một **chuỗi đặc trưng bắt buộc** (`must_contain`) và kiểm nó có thật trong ngữ cảnh truy xuất được hay không:

```python
"must_contain": ["2 weeks", "1 month"],     # Q1
"must_contain": ["20,000 VND"],             # Q2
"must_contain": ["cannot be renewed", "no request"],  # Q3
```

Chênh lệch giữa hai cách chấm **hiện ra ngay ở Q3**. Với `RecursiveChunker`, tài liệu gold vẫn lọt top-3 (chấm ngây thơ → 2 điểm), nhưng ngữ cảnh **không hề chứa** chuỗi `"cannot be renewed"` → chấm đúng chỉ được **1 điểm**. Nếu tôi chỉ đếm `doc_id`, tôi đã tự chấm mình 10/10 cho cả bốn chiến lược và không phát hiện được gì.

### Bằng chứng A/B — metadata filter có tác dụng thật

Câu Q1 cố tình **không nêu người hỏi là ai** ("**my** loan period"), trong khi corpus có bốn tài liệu cùng chủ đề, cùng từ vựng `Circulation privilege`, nhưng khác `audience` và **khác đáp án**. Chạy hai lần trên cùng chiến lược heading:

| Hạng | **CÓ** `metadata_filter={"audience":"student"}` | **KHÔNG** filter |
|---|---|---|
| 1 | `muon-tai-lieu-sinh-vien-dai-hoc#1` (+0.7272) `student` | `muon-tai-lieu-sinh-vien-dai-hoc#1` (+0.7272) `student` |
| 2 | `muon-tai-lieu-hoc-vien-sau-dai-hoc#1` (+0.7214) `student` | `muon-tai-lieu-hoc-vien-sau-dai-hoc#1` (+0.7214) `student` |
| 3 | `muon-tai-lieu-hoc-vien-sau-dai-hoc#2` (+0.6965) `student` | **`muon-tai-lieu-giang-vien#1` (+0.7002) `faculty`** ⚠️ |

Không lọc, slot thứ 3 bị **tài liệu giảng viên** chiếm — nó ghi *"5 items, 6 months"*. Một sinh viên đọc câu trả lời có ngữ cảnh đó hoàn toàn có thể kết luận mình được mượn 6 tháng, **sai gấp 12 lần** so với 2 tuần thực tế. Chênh lệch score giữa chunk faculty (+0.7002) và chunk graduate (+0.6965) chỉ là **0.0037** — quá nhỏ để embedding tự phân biệt được. Đây chính là chỗ metadata làm được việc mà similarity không làm được: **phân biệt đúng/sai theo đối tượng, không phải theo chủ đề.**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**

> *(Nhóm không kịp thuyết trình, nên phần này tôi viết theo những gì học được khi đối chiếu kết quả với hai thành viên trong nhóm.)*
>
> **Từ Dương — thứ tôi đã bỏ sót hoàn toàn.** Tôi chỉ giữ backend cố định ở `gemini-embedding-001` rồi đổi chunker để so sánh. Dương làm ngược lại: giữ nguyên chiến lược `fixed` và đổi backend, ra **2/10 với mock so với 9/10 với Gemini**. Tôi chạy lại để kiểm và đúng 2/10 thật — với mock, câu hỏi "tài liệu nào không được mượn" trả về top-1 là tài liệu *hạn mức nhân viên* (+0.2404), tài liệu gold không lọt nổi top-3.
>
> Con số đó làm tôi phải đọc lại kết luận của chính mình. Ba chiến lược chunking của nhóm chênh nhau **1 điểm**, còn mock với embedding thật chênh **7 điểm**. Tức là biến số tôi đã "khoá lại và quên đi" hoá ra quan trọng gấp bảy lần biến số tôi bỏ cả buổi để tinh chỉnh. Bài học là khi so sánh, phải hỏi **biến nào tôi đang giữ cố định và nó có thật sự vô hại không**, chứ không chỉ chăm chăm vào biến mình đang đổi.
>
> **Từ Trí — một câu chỉnh lại cách tôi đọc điểm tổng:** *"cần so sánh chiến lược theo từng loại câu hỏi, không chỉ theo điểm tổng."* Tôi thắng 10/10 so với 9/10 và suýt kết luận HeadingChunker "tốt hơn". Nhìn theo từng câu thì đúng hơn nhiều: cả ba chiến lược hoà nhau ở Q1, Q2, Q4, Q5, toàn bộ khác biệt nằm ở **đúng một câu Q3**. Nếu bộ benchmark không tình cờ có Q3, ba chiến lược sẽ ra điểm y hệt và nhóm sẽ kết luận nhầm rằng chọn chunker thế nào cũng như nhau.
>
> **Từ việc đối chiếu số liệu ba người — điều bất ngờ nhất.** Ba chúng tôi viết `src/` hoàn toàn độc lập, trên ba máy và ba phiên bản Python khác nhau (3.12.10 / 3.10.8 / …), prompt agent khác hẳn nhau, Trí còn giữ nguyên nhánh ChromaDB mà tôi đã bỏ. Vậy mà khi chạy cùng một chiến lược, điểm cosine **trùng nhau đến 4 chữ số thập phân** — Q3 top-1 của Trí và bản `recursive` đối chứng của tôi đều là `+0.6908`. Điều này cho tôi thấy giá trị của việc đặc tả chặt: docstring của lab đủ rõ để ba cài đặt độc lập hội tụ về cùng hành vi, nhờ vậy nhóm chắc chắn được rằng chênh lệch điểm đến từ **lựa chọn chiến lược** chứ không phải từ bug của ai đó.
>
> **Một bài học nhỏ nhưng tốn thời gian thật:** báo cáo của Dương ghi chunk lọt top-3 ở Q3 "chứa `Overdue items cannot be renewed`". Tôi kiểm lại nội dung chunk thì câu đó nằm ở chunk `#0`, còn chunk `#1` lọt top-3 chỉ nói về *recall*. Công cụ báo đúng, phần đọc bằng mắt sai. Nếu nhóm chấm theo kiểu "gold `doc_id` có trong top-3 là được" thì đã tính 2 điểm cho một câu mà ngữ cảnh không hề trả lời được. Đây là lý do tôi thấy việc khai báo `must_contain` đáng công hơn tôi tưởng lúc viết nó.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
