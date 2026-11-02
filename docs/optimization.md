# Optimization review

Các điểm dưới đây được tìm ra khi rà soát model (TMDL) và report (PBIR). Mỗi điểm ghi rõ vấn đề, tác động và cách xử lý đề xuất.

| # | Vấn đề | Tác động | Mức |
|---|---|---|---|
| 1 | Auto date/time đang bật | +10 bảng ẩn, tăng dung lượng | Cao |
| 2 | Calculated column dùng `RANKX` trên bảng fact | Refresh chậm (O(n²)) | Cao |
| 3 | Khóa quan hệ khác kiểu dữ liệu | Rủi ro sai kết quả, tốn bộ nhớ | Trung bình |
| 4 | Quan hệ nối bằng tên chương trình (text) | Từ điển lớn, dễ vỡ khi đổi tên | Trung bình |
| 5 | Quan hệ hai chiều | Mơ hồ khi lọc, chậm | Trung bình |
| 6 | Visual tham chiếu tới bảng đã xóa | 30 trường lỗi trên 4 trang | Trung bình |
| 7 | Bảng phụ còn sót lại | Rối model | Thấp |
| 8 | Cột PII / cardinality cao được load | Dung lượng + bảo mật | Trung bình |

---

## 1. Tắt Auto date/time

Model có **10 bảng `LocalDateTable_*`** và một `DateTableTemplate`, do Power BI tự tạo cho mỗi cột kiểu date. Model đã có `dim_date` được đánh dấu là bảng ngày (`dataCategory: Time`), nên các bảng ẩn này là thừa.

**Đề xuất:** File → Options → Current file → Data load → bỏ chọn *Auto date/time*. Các visual đang dùng hierarchy tự động (`.Variation`) phải chuyển sang cột của `dim_date`.

## 2. `session_number_type`: calculated column với `RANKX`

```dax
RANKX(
    FILTER('fact_regular_session',
        [teacher_id] = cur_teacher && [class_code] = cur_class
        && RELATED('dim_date'[week_of_year]) = cur_week),
    [learn_date] & [start_time], cur_date & cur_start_time, ASC, DENSE)
```

Với mỗi dòng, biểu thức quét lại toàn bộ bảng fact nên độ phức tạp là O(n²). Đây là bảng lớn nhất model (buổi học × học sinh), nên đây là nút cổ chai khi refresh.

**Đề xuất:** tính ở tầng SQL bằng window function:

```sql
'Buổi ' || DENSE_RANK() OVER (
    PARTITION BY teacher_id, class_code, TO_CHAR(learn_date, 'IYYY-IW')
    ORDER BY learn_date, start_time)
```

Tương tự, `chairman_teacher_username` (dùng `LOOKUPVALUE`) nên lấy sẵn từ SQL hoặc thay bằng quan hệ.

## 3. Khóa quan hệ khác kiểu dữ liệu

| Cột | Kiểu |
|---|---|
| `dim_teacher[teacher_id]` | string |
| `fact_regular_session[teacher_id]` | double |
| `fact_class_regular[chairman_teacher_id]` | double |
| `fact_schedule_teacher[teacher_id]` | int64 |

Các cột ID dạng số đang được lưu là `double` (`student_id`, `teacher_id`...). **Đề xuất:** chuẩn hóa toàn bộ khóa về `int64` ngay trong câu SQL nguồn.

## 4. Quan hệ nối bằng tên chương trình

`fact_*[study_program_name]` → `dim_study_program[STUDY_PROGRAM_NAME]` nối bằng chuỗi tên dài. Ngoài ra M query còn phải vá tay mô hình lớp của một chương trình (`Table.ReplaceValue`). **Đề xuất:** nối bằng `STUDY_PROGRAM_CODE`, và sửa dữ liệu gốc ở bảng master thay vì vá trong Power Query.

## 5. Quan hệ hai chiều

- `dim_teacher` ↔ `dim_teacher_status` (1:1, both): có thể gộp `work_status` vào `dim_teacher` bằng merge trong Power Query, bỏ hẳn một bảng.
- `dim_study_program` ↔ `dim_kpi` (many-to-many, both, inactive): nên dùng `TREATAS` trong measure KPI thay vì giữ quan hệ.

Ngoài ra có 4 quan hệ `AutoDetected_*` do Power BI tự tạo. Cần rà soát để chắc chắn đúng ý đồ.

## 6. Visual tham chiếu tới bảng đã xóa

Report còn 30 tham chiếu tới các bảng không còn trong model (`fact_student_performance`, `dim_label`, `param_pss`, `dim_rank_ps`...). Chúng nằm chủ yếu ở trang *Dữ liệu theo HS*, ngoài ra rải rác ở các trang *Xếp lớp*, *Mở lớp* và *ACS & Lớp học*. Những visual này hiển thị lỗi. **Đề xuất:** xóa visual hoặc khôi phục bảng.

## 7. Bảng phụ còn sót lại

- `tab` = `INFO.VIEW.RELATIONSHIPS()`: bảng debug dùng khi dựng model.
- `Table` = `Row("Column", BLANK())`: bảng rỗng.
- Biểu thức `_Measure` (Enter data rỗng).

**Đề xuất:** xóa, hoặc chuyển sang một perspective / thư mục ẩn dành cho developer.

## 8. Cột PII và cột có cardinality cao

`fact_arrange_class[phone]` và `dim_teacher[phone]`, `full_name` được load vào model. Cột số điện thoại gần như unique theo từng dòng nên nén rất kém, đồng thời là dữ liệu cá nhân. **Đề xuất:** bỏ khỏi model nếu không dùng để tra cứu. Nếu cần tra cứu, tách sang một bảng chi tiết có RLS.

---

## Checklist khi tối ưu dung lượng model

1. Chạy **VertiPaq Analyzer** (DAX Studio → View Metrics), sắp xếp theo *Total Size*.
2. Xử lý 5 cột lớn nhất trước: bỏ cột, giảm cardinality (tách datetime, làm tròn), đổi kiểu dữ liệu.
3. Tắt Auto date/time.
4. Chuyển calculated column sang SQL / Power Query.
5. Đo lại dung lượng và thời gian refresh.
