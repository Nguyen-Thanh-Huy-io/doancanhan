1. Mục tiêu
Trong quá trình học tập môn Trí tuệ nhân tạo (AI) ở trên trường, em đã được chỉ dạy rất nhiều các nhóm thuật toán khác nhau. Vì vậy để mô phỏng những kiến thức lý thuyết cũng như có những cái nhìn sinh động, chân thật về những nhóm thuật toán thì em đã có thực hiện một đồ án cá nhân nho nhỏ đó là mô phỏng trò chơi 8 puzzle, nơi mà em đã thực hiện giải trò chơi thông qua các nhóm thuật toán khác nhau nhằm đánh giá được hiệu suất cũng như cách vận hành của từng loại
2. Nội dung
Một bài toán tìm kiếm thông thường sẽ đƯợc định nghĩa bởi các thành phần sau xét theo lĩnh vực Trí tuệ nhân tạo và nếu trên khía cách là giải bài toán 8-puzzle thì sau đây là những điều chúng ta cần lưu ý.
**Không gian trạng thái**: Tập hợp tất cả các trạng thái có thể đạt được. Đối với 8-puzzle, mỗi trạng thái là một cách sắp xếp cụ thể của 8 ô số và 1 ô trống trên lưới 3x3.
**Trạng thái ban đầu (Initial State)** : chính là trạng thái xuất phát của bài toán. Trong ứng dụng game trên, chúng ta có thể thiết lập, điều chỉnh trạng thái theo ý muốn hay sử dụng một trạng thái mặc định.
**Hành động (Actions):** Tập hợp các hành động có thể thực hiện để chuyển từ trạng thái này sang trạng thái khác. Với 8-puzzle, hành động là di chuyển ô trống lên, xuống, trái, phải.
**Mô hình chuyển đổi (Transition Model):** Một hàm `RESULT(s, a)` trả về trạng thái kết quả khi thực hiện hành động `a` từ trạng thái `s`.
**Trạng thái đích (Goal State) hoặc Phép thử đích (Goal Test):** Một hoặc nhiều trạng thái mong muốn đạt được, hoặc một hàm kiểm tra xem một trạng thái có phải là trạng thái đích hay không. Trong dự án này, trạng thái đích mong muốn luôn là `[[1, 2, 3], [4, 5, 6], [7, 8, 0]]`.
6.  **Chi phí đường đi (Path Cost):** Một hàm gán chi phí cho một đường đi (chuỗi các hành động). Trong bài toán 8-puzzle cơ bản, mỗi bước di chuyển thường có chi phí là 1 tại vì đây là một ma trận dạng lưới (grid).
2.1. Các thuật toán tim kiếm có thông tin ( Uniformed Search)
* Nhóm thuật toán này sẽ bao gồm các nhóm thuật toán kinh điển như: 
2.1.1. Breadth-First Search (BFS)  - tìm kiếm theo chiều rộng
- Mô tả: Thuật toán duyệt hoặc mở rộng từ những nút nông trước (những nút kế bên nút được xét), sử dụng hàng đợi queue để xử lý các nút chờ được xét.
- Ứng dụng: Trực quan hóa quá trình BFS giải 8-puzzle có thể được thực hiện thông qua giao diện chính (`giaodien.py`).
![Demo](assets/images/bfs.gif)
