---
name: graphify-context-discovery
description: >-
  Reverse-engineers the codebase context for a module using Graphify Knowledge Graph.
  Extracts entry points, dependency call trees, data models, validation logic, upstream prerequisites,
  and downstream side-effects into module-context.md.
  Mandatory primary tool: Graphify.
---

# Skill: Graphify Context Discovery (Step 1)

## 1. Description & Trigger Conditions
* **Purpose:** Discover and map the complete, unrestricted structural and dependency context of the target module using **Graphify**. Build a deterministic dependency-aware knowledge graph without relying on hallucinated assumptions or artificial depth cutoffs.
* **Core Philosophy:** **Optimize Context Consumption, NOT Discovery Coverage.**
  * Graph Discovery is exhaustive and unrestricted.
  * LLM Context Loading is selective, on-demand, and progressive.
* **Triggers:**
  * Completed `module-intake`.
  * Invoked by `workflow-orchestrator` when entering `CONTEXT_DISCOVERY`.

## 2. Inputs
* **Required:**
  * Target module name and repository path.
  * Initialized `.qa-state.json`.
* **Optional:**
  * Specific entry file paths or suspected symbols.

## 3. Prerequisites
* **Graphify CLI** (`graphify`) or **Graphify MCP** (`graphify-mcp`) installed and operational.
* Target repository source code available locally.

## 4. Architectural Principles: Discovery vs. Context Loading

### 4.1. Unrestricted Dependency Discovery (No Artificial Caps)
* **NO Node Limits:** KHÔNG thiết lập giới hạn cứng về số lượng node mà Graphify được phép khám phá.
* **NO Depth Limits:** KHÔNG giới hạn dependency depth (không dùng depth = 2, 3 hay 5). Khám phá toàn bộ chuỗi phụ thuộc trực tiếp, gián tiếp và xuyên module liên quan đến module kiểm thử.
* **NO Budget-Based Truncation:** KHÔNG cắt bớt dependency graph chỉ vì vượt token budget.
* **NO Arbitrary Stopping:** KHÔNG dừng phân tích khi đã tìm thấy một số lượng function, class hoặc module nhất định.
* **NO Top-K Pruning:** KHÔNG sử dụng cơ chế Top-K để loại bỏ các dependency có liên quan đến nghiệp vụ hoặc rủi ro kiểm thử.
* **Technical Safety Guards Only:** Duy trì các biện pháp kỹ thuật chống lỗi thực tế:
  * Theo dõi `visited_set` và Cycle Detection để ngăn vòng lặp vô tận (cyclic dependencies).
  * Loại trừ các thư mục nhị phân và thư viện bên thứ ba không cần phân tích AST (`node_modules/`, `dist/`, `.git/`, build artifacts).
  * Process timeout guard để phòng ngừa treo tiến trình do file bị khóa hoặc hỏng cú pháp.
* **Persistence:** Toàn bộ đồ thị phụ thuộc được phân tích và lưu trữ trên đĩa cứng cục bộ (`graphify-out/`) để tái sử dụng xuyên suốt toàn bộ vòng đời kiểm thử.

### 4.2. High-Efficiency LLM Context Loading (On-Demand Progressive Disclosure)
* **Never Dump Full Graph:** Tuyệt đối không đưa toàn bộ file `graphify-out/graph.json` hay báo cáo đồ thị thô hàng trăm nghìn tokens vào prompt cùng lúc.
* **On-Demand Subgraph Queries:** LLM chỉ truy xuất các phân đoạn đồ thị hoặc chuỗi gọi hàm (call chains) cần thiết cho tác vụ hiện tại qua lệnh Graphify CLI.
* **Signature-First Protocol:**
  * Ưu tiên nạp TypeScript interfaces, function contracts, export signatures, Zod/Yup validation schemas trước.
  * Chỉ nạp chi tiết thân hàm (function implementation body) khi cần kiểm tra sâu logic rẽ nhánh, biểu thức regex phức tạp, hoặc khối bắt lỗi.
* **Incremental Cache:** Kiểm tra mã băm git commit (`git rev-parse HEAD`) hoặc hash nội dung file. Nếu mã nguồn không đổi, tái sử dụng ngữ cảnh đã cache; nếu có thay đổi, chỉ phân tích lại các file thay đổi và phụ thuộc liên quan.

## 5. Step-by-Step Execution Instructions

1. **Incremental Cache & Hash Verification:**
   * Kiểm tra `.qa-state.json` với git commit hash hiện tại.
   * Nếu mã nguồn module không thay đổi và `module-context.md` đã tồn tại:
     - Tái sử dụng ngữ cảnh AST đã cache; không cần quét lại từ đầu (0 token tiêu hao).
   * Nếu có thay đổi: Phân tích các file thay đổi và toàn bộ mạng lưới dependency mở rộng của chúng.

2. **Graphify Environment Detection:**
   * Chạy `graphify --version` để xác thực công cụ.
   * *Nếu Graphify bị thiếu hoặc lỗi:* Dừng lại ngay lập tức. Báo cáo rõ công cụ thiếu và xin phép người dùng trước khi áp dụng giải pháp tĩnh thay thế. Không bịa đặt kết quả Graphify.

3. **Build / Refresh Exhaustive Knowledge Graph:**
   * Chạy `graphify update <repo-path>` để tạo lập hoặc làm mới toàn bộ đồ thị tri thức trong thư mục `graphify-out/`.
   * Lưu trữ toàn bộ kết quả phân tích dependency xuống đĩa cứng cục bộ.

4. **Trace Full Dependency Chains & Cross-Module Flows:**
   * Xuất phát từ các điểm vào chính (Routes, Pages, Controllers, Event Handlers).
   * Khám phá toàn bộ chuỗi gọi: UI $\rightarrow$ Custom Hooks $\rightarrow$ Domain Services $\rightarrow$ API Clients/RPC $\rightarrow$ Data Models / Database Tables.
   * Khám phá đầy đủ các dependency xuyên module (ví dụ: module Đăng nhập gọi sang User Management, Notification, Rate Limiter, Audit Log).
   * Sử dụng `graphify path "<EntryNode>" "<TargetNode>"` để truy vết liên kết từ đầu vào đến tầng lưu trữ mà không bị giới hạn độ sâu.

5. **Signature-First Extraction & Targeted Ingestion:**
   * Truy xuất hợp đồng dữ liệu, kiểu dữ liệu và schema ràng buộc của các hàm/module liên quan.
   * Truy xuất sâu thân hàm có chọn lọc đối với các vị trí rủi ro cao (xử lý concurrency, lock tài khoản, token session, xử lý ngoại lệ).

6. **Context Classification:**
   * Gắn nhãn tường minh mọi bằng chứng:
     - `[CODE-CONFIRMED]`: Đã xác thực trong AST mã nguồn thực tế.
     - `[DOC-CONFIRMED]`: Được quy định trong tài liệu/spec.
     - `[RUNTIME-CONFIRMED]`: Đã kiểm chứng qua quan sát thực tế (Playwright MCP).
     - `[INFERRED]`: Suy luận theo quy luật nhưng chưa có assertion xác thực.
     - `[UNKNOWN]`: Thiếu thông tin hoặc chưa rõ cài đặt.

7. **Generate Deliverable & State Transition:**
   * Tạo tệp `module-context.md` tại thư mục gốc với bản đồ cấu trúc hoàn chỉnh, liệt kê đầy đủ các chuỗi dependency, validation rules và rủi ro tiềm ẩn.
   * **Đánh dấu Trạng thái Workflow:**
     - Nếu khám phá hoàn tất không gặp trở ngại: Chuyển trạng thái sang `GAP_ANALYSIS` qua `python scripts/state_manager.py transition GAP_ANALYSIS "Completed full Graphify context discovery"`.
     - Nếu khám phá chưa hoàn tất do lỗi kỹ thuật (parser crash, timeout, tài nguyên cạn kiệt): Ghi nhận trạng thái `DISCOVERY_INCOMPLETE` kèm danh sách chi tiết các file/nhánh chưa thể duyệt và lý do kỹ thuật. Tuyệt đối không tự ý báo hoàn thành khi phân tích còn dang dở.

## 6. Expected Outputs
* `module-context.md` bao gồm:
  * Tổng quan phân hệ & Điểm vào (Entry Points).
  * Cây phụ thuộc hoàn chỉnh (Toàn bộ chuỗi gọi Upstream / Downstream và Cross-Module, không cắt ngắn độ sâu).
  * Tái dựng luồng nghiệp vụ & cơ chế chuyển đổi trạng thái (State Transitions).
  * Mô hình dữ liệu, Ràng buộc dữ liệu & Database Schemas.
  * Cơ chế bảo mật, Concurrency, Xử lý lỗi & Giới hạn tần suất (Rate Limiting / Throttling).
  * Bằng chứng truy vết (Đường dẫn tệp, tên hàm, số dòng cụ thể).
* Cập nhật `.qa-state.json` (`GAP_ANALYSIS` hoặc `DISCOVERY_INCOMPLETE`).

## 7. Failure Handling & Incomplete Discovery Protocol
* **Lỗi Parser / Cú pháp:** Báo cáo chính xác file và lỗi cú pháp; đánh dấu `DISCOVERY_INCOMPLETE` đối với nhánh đó và tiếp tục phân tích các nhánh độc lập khác.
* **Treo Tiến trình / Quá thời gian chờ (Timeout):** Ngắt an toàn tiến trình treo, ghi nhận timeout và đánh dấu `DISCOVERY_INCOMPLETE`.
* **Ký hiệu bị cô lập (Missing Symbols):** Dùng `graphify query "<feature-keyword>"` để tìm kiếm theo cụm topo liên kết.
* **Tuyệt đối không kết luận hoàn thành giả:** Không bao giờ tự động báo khám phá đã hoàn tất chỉ vì hết ngân sách token. Mọi trường hợp chưa duyệt hết đều phải gắn nhãn `DISCOVERY_INCOMPLETE`.

## 8. Human Approval Requirements
* Không yêu cầu phê duyệt nếu Graphify hoàn tất thành công.
* Bắt buộc có sự chấp thuận của người dùng nếu rơi vào trạng thái `DISCOVERY_INCOMPLETE` hoặc khi cần chuyển đổi sang phương án tĩnh thay thế.

## 9. Completion Criteria
* `module-context.md` được sinh ra với đầy đủ bằng chứng mã nguồn đã xác thực.
* Tất cả dependency có liên quan đều đã được khám phá, hoặc bất kỳ phần nào chưa thể khám phá đều được ghi nhận minh bạch dưới cờ `DISCOVERY_INCOMPLETE`.
