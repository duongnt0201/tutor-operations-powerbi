"""Generate synthetic sample data for the Tutor Operations Power BI project.

Every value produced here is random and fictional. The script only mirrors the
schema and the status codes the DAX measures rely on, so the report renders
meaningful-looking numbers after a refresh.

Usage:
    python scripts/generate_sample_data.py            # writes to data/sample/
    python scripts/generate_sample_data.py --out DIR
"""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 2026
START = date(2025, 1, 1)
END = date(2026, 10, 31)

GRADES = [("GRADE_0", "Lớp mầm", 0, "Khác", 3)] + \
    [(f"GRADE_{i}", f"Lớp {i}", i, "Tiểu học", 1) for i in range(1, 6)] + \
    [(f"GRADE_{i}", f"Lớp {i}", i, "THCS", 2) for i in range(6, 10)] + \
    [(f"GRADE_{i}", f"Lớp {i}", i, "Khác", 3) for i in range(10, 12)]
LEVELS = [("LEVEL_A", "Level A", 1), ("LEVEL_B", "Level B", 2), ("LEVEL_C", "Level C", 3),
          ("LEVEL_D", "Level D", 4), ("LEVEL_E", "Level E", 5)]
PROGRAMS = [  # name, max students, code, type, product, sessions/week, model
    ("Tutor Basic (1-4)", 4, "TUTOR_BASIC_14", "REGULAR", "TUTOR", 2, "1-4"),
    ("Tutor Pro Dual (1-4)", 4, "TUTOR_PRO_DUAL_14", "REGULAR", "TUTOR", 2, "1-4"),
    ("Tutor Pro (1-2)", 2, "TUTOR_PRO_12", "REGULAR", "TUTOR", 2, "1-2"),
    ("Tutor Pro Vip Dual (1-1)", 1, "TUTOR_VIP_DUAL_11", "REGULAR", "TUTOR", 3, "1-1"),
]
PROGRAM_WEIGHTS = [45, 30, 15, 10]
TEACHER_LEVELS = ["A+", "A", "B", "C", "D"]
START_TIMES = ["09:00", "10:00", "15:00", "16:00", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
TIME_WEIGHTS = [3, 3, 4, 5, 12, 10, 16, 14, 14, 8, 6]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

rng = random.Random(SEED)


def pick(options, weights=None):
    return rng.choices(options, weights=weights, k=1)[0]


def rand_date(a=START, b=END):
    return a + timedelta(days=rng.randint(0, (b - a).days))


def d(x):
    return x.isoformat() if x else ""


def write(out, name, header, rows):
    with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name}.csv  {len(rows):>7,} rows")


def month_starts():
    m = date(START.year, START.month, 1)
    while m <= END:
        yield m
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)


def main(out):
    out.mkdir(parents=True, exist_ok=True)

    # ---------------- dimensions ----------------
    write(out, "dim_grade", ["code", "name", "sort", "level", "level_sort"], GRADES)
    write(out, "dim_level", ["CODE", "NAME", "VALUE"], LEVELS)
    write(out, "dim_study_program", ["STUDY_PROGRAM_NAME", "MAX_STUDENT_IN_CLASS", "STUDY_PROGRAM_CODE", "TYPE",
                                     "PRODUCT_TYPE_CODE", "SESSIONS_PER_WEEK", "PROGRAM_MODEL"], PROGRAMS)

    teachers = []
    for i in range(1, 181):
        tid = 10000 + i
        teachers.append(dict(id=tid, username=f"tutor_{i:04d}", level=pick(TEACHER_LEVELS, [10, 25, 35, 20, 10]),
                             group="Backup" if i % 7 == 0 else "Regular"))
    write(out, "dim_teacher", ["teacher_id", "teacher_username", "full_name", "gender", "region", "phone", "level_teacher"],
          [(t["id"], t["username"], f"Gia sư {t['id'] - 10000:03d}", pick(["F", "M"], [70, 30]),
            pick(["Miền Bắc", "Miền Trung", "Miền Nam"]), f"0900{t['id'] - 10000:06d}", t["level"]) for t in teachers])
    write(out, "dim_teacher_status", ["teacher_code", "work_status"],
          [(t["username"], pick(["Đang làm việc", "Sắp nghỉ"], [94, 6])) for t in teachers])
    write(out, "dim_kpi", ["month_of_report", "program_model", "level_teacher", "KPI"],
          [(d(m), pm, lv, round(rng.uniform(0.82, 0.95), 2))
           for m in month_starts() for pm in ("1-4", "1-2", "1-1") for lv in TEACHER_LEVELS])

    regular = [t for t in teachers if t["group"] == "Regular"]
    backup = [t for t in teachers if t["group"] == "Backup"]

    # ---------------- classes ----------------
    classes, class_rows = [], []
    for i in range(1, 1201):
        prog = pick(PROGRAMS, PROGRAM_WEIGHTS)
        created = rand_date(START, END - timedelta(days=5))
        opening = created + timedelta(days=rng.randint(1, 10))
        status = pick(["Đang học", "Chờ khai giảng", "Kết thúc", "Hủy"], [55, 8, 30, 7])
        if opening > END:
            status = "Chờ khai giảng"
        t = pick(regular)
        changed = rng.random() < 0.12
        before = pick(regular) if changed else None
        terminated = rng.random() < 0.08
        c = dict(code=f"CL{i:05d}", program=prog, grade=pick(GRADES)[0], level=pick(LEVELS)[0],
                 start=pick(START_TIMES, TIME_WEIGHTS), teacher=t, opening=opening, status=status,
                 students=[200000 + rng.randint(1, 9999) for _ in range(rng.randint(1, prog[1]))])
        classes.append(c)
        class_rows.append((c["code"], d(created), status, len(c["students"]), c["grade"], c["level"], prog[0], c["start"],
                           t["username"], before["username"] if before else "", before["id"] if before else "",
                           d(opening + timedelta(days=rng.randint(0, 60))),
                           before["id"] if terminated and before else "", pick(["Giáo viên xin nghỉ", "Học sinh yêu cầu", "Khác"]) if terminated else "",
                           d(opening + timedelta(days=rng.randint(5, 90))) if terminated else "",
                           int(changed), int(terminated), 2 if changed else 1, t["id"], d(opening)))
    write(out, "fact_class_regular",
          ["class_code", "date_create", "class_status", "number_of_students", "grade_code", "level_code",
           "study_program_name", "start_time", "chairman_teacher_username", "before_chairman_teacher_username",
           "before_chairman_teacher_id", "learn_date", "terminated_teacher_id", "terminated_type",
           "terminated_create_date", "has_change_teacher", "has_terminated_ticket", "chairman_teacher_order",
           "chairman_teacher_id", "class_openning_date"], class_rows)

    # ---------------- arrange class (orders) ----------------
    arrange = []
    n = 0
    for c in classes:
        for sid in c["students"]:
            n += 1
            ptc = c["opening"] - timedelta(days=rng.randint(1, 20))
            created = ptc + timedelta(days=rng.randint(0, 2))
            done = rng.random() < 0.88
            arrange.append((f"TA{n:06d}", c["code"], "DONE" if done else pick(["PENDING", "CANCELED"]),
                            pick(["AUTO", "MANUAL"], [60, 40]), d(created),
                            d(created + timedelta(days=rng.randint(0, 4))) if done else "",
                            pick(["NEW", "RENEW", "CHANGE_CLASS"], [70, 20, 10]), f"OD{n:07d}", d(ptc),
                            d(c["opening"]), sid, pick(GRADES)[3], c["grade"], c["level"], f"0911{n:06d}",
                            rng.randint(8, 22), DOW[created.weekday()], c["start"], c["program"][0],
                            d(c["opening"] - timedelta(days=rng.randint(0, 3))),
                            pick(["SUCCESS", "NO_ANSWER", "BUSY", "UNKNOWN"], [70, 15, 8, 7]),
                            pick(["Gói 3 tháng", "Gói 6 tháng", "Gói 12 tháng"]), pick(["NEW", "RENEWAL"], [75, 25]),
                            pick(["0.Bán mới", "1.Nâng cấp", "3.Gia hạn"], [65, 10, 25])))
    write(out, "fact_arrange_class",
          ["task_arrange_class_id", "class_code", "arrange_status", "arrange_class_method", "arrange_create_date",
           "arrange_success_date", "arrange_type", "order_id", "ptc_date", "first_learn_date", "student_id",
           "grade_program", "grade_code", "level_code", "phone", "arrange_create_hour", "day_of_week",
           "start_time", "study_program", "class_create_date", "call_status", "package_name", "order_type",
           "new_package_category"], arrange)

    # ---------------- sessions ----------------
    sessions = []
    for c in classes:
        if c["status"] == "Chờ khai giảng":
            continue
        weeks = rng.randint(4, 14)
        per_week = c["program"][5]
        day = c["opening"]
        for s_no in range(1, weeks * per_week + 1):
            if day > END:
                break
            s_type = "FIRST_TIME" if s_no == 1 else pick(["LEARN_SCHEDULE", "MAKE_UP_LESSON"], [94, 6])
            is_backup = int(rng.random() < 0.07)
            teacher = pick(backup) if is_backup else c["teacher"]
            sess_status = pick(["DONE", "DONE_1", "DONE_2", "FAILED_TEACHER", "FAILED_SYSTEM", "FAILED_OTHER"],
                               [80, 6, 3, 5, 3, 3])
            absence = pick(["", "Nghỉ phép", "Ngoài phép", "Bỏ ca"], [0, 55, 30, 15]) if is_backup else ""
            t_on_time = int(rng.random() < 0.93)
            for sid in c["students"]:
                st = "SUCCESS" if sess_status.startswith("DONE") and rng.random() < 0.9 else \
                    pick(["FAILED_STUDENT_NO_LEARNED", "RESCHEDULED", "FAILED_TECHNICAL", "FAILED_TEACHER",
                          "FAILED_SYSTEM", "FAILED_MINISTRY", "REMOVED_STUDENT"], [40, 25, 10, 10, 8, 4, 3])
                s_on_time = int(rng.random() < 0.85)
                sessions.append((c["code"], sid, d(day), s_on_time, rng.randint(0, 10) if s_on_time else -rng.randint(1, 15),
                                 f"{c['code']}-S{s_no:03d}", s_no, sess_status, st, s_type,
                                 int(sess_status.startswith("DONE")), t_on_time,
                                 rng.randint(0, 10) if t_on_time else -rng.randint(1, 15),
                                 c["grade"], teacher["id"], c["level"], c["teacher"]["id"], is_backup,
                                 c["program"][0], c["start"], absence,
                                 pick(["APPROVED", "REJECTED"], [85, 15]) if absence else ""))
            day += timedelta(days=rng.choice([2, 3, 4]) if per_week > 1 else 7)
    write(out, "fact_regular_session",
          ["class_code", "student_id", "learn_date", "is_student_on_time", "student_early_in_minutes",
           "class_session_code", "session_number", "session_status", "student_status", "session_type",
           "is_success_session", "is_teacher_on_time", "teacher_early_in_minutes", "grade_code", "teacher_id",
           "level_code", "chairman_teacher_id", "is_backup", "study_program_name", "start_time", "absence_type",
           "absence_status"], sessions)

    # ---------------- teacher schedules ----------------
    sched = []
    n = 0
    for t in teachers:
        for m in month_starts():
            for _ in range(rng.randint(3, 8)):
                n += 1
                sd = m + timedelta(days=rng.randint(0, 27))
                if sd > END:
                    continue
                st = pick(START_TIMES, TIME_WEIGHTS)
                h, mi = map(int, st.split(":"))
                status = pick(["ASSIGNED", "MONITOR_BACKUP", "OPEN", "CANCELED", "WAITING_CANCELLATION_CONFIRMATION"],
                              [55, 8, 27, 7, 3])
                assigned = status in ("ASSIGNED", "MONITOR_BACKUP")
                sched.append((f"SC{n:07d}", d(m), d(sd), d(sd - timedelta(days=rng.randint(1, 7))) if assigned else "",
                              status, DOW[sd.weekday()], st, f"{h + 1:02d}:{mi:02d}", int(rng.random() < 0.3),
                              pick(["WEEKLY", "ONE_TIME"], [85, 15]), t["id"], t["username"], t["group"],
                              pick(["ACTIVE", "INACTIVE"], [92, 8]),
                              f"SS{n:07d}" if assigned else "", pick(classes)["code"] if assigned else "",
                              int(h >= 18), int(19 <= h <= 20), d(sd - timedelta(days=rng.randint(7, 20)))))
    write(out, "fact_schedule_class",
          ["id", "month_of_report", "schedule_date", "assigned_date", "schedule_status", "day_of_week", "start_time",
           "end_time", "is_schedule_required", "schedule_type", "teacher_id", "teacher_username", "tutor_group",
           "monthly_teacher_status", "session_code", "class_code", "evening_shift", "peak_shift", "date_create"], sched)

    st_rows = []
    for i in range(1, 4001):
        t = pick(teachers)
        st_rows.append((f"ST{i:06d}", t["id"], pick(["CONFIRMED", "SENT_CONFIRM", "REJECTED"], [70, 18, 12]),
                        t["group"], d(rand_date()), pick(["ACTIVE", "INACTIVE"], [92, 8]), f"REQ{i:06d}"))
    write(out, "fact_schedule_teacher", ["id", "teacher_id", "status", "tutor_group", "date_create", "teacher_status", "code"],
          st_rows)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data" / "sample"))
    a = p.parse_args()
    print(f"Writing synthetic data to {a.out}")
    main(Path(a.out))
