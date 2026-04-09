import os
from datetime import datetime, date
from io import BytesIO
from zoneinfo import ZoneInfo

import psycopg
from openpyxl import Workbook

DATABASE_URL = os.getenv('DATABASE_URL', '')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tashkent')
WORK_START = os.getenv('WORK_START', '09:00')


def now_local() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL kiritilmagan.')
    return psycopg.connect(DATABASE_URL)


def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    user_id BIGINT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    username TEXT,
                    phone TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    full_name TEXT NOT NULL,
                    work_date DATE NOT NULL,
                    action TEXT NOT NULL,
                    event_time TIMESTAMPTZ NOT NULL,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    photo_file_id TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS employee_state (
                    user_id BIGINT PRIMARY KEY,
                    state TEXT,
                    action TEXT,
                    phone TEXT,
                    full_name TEXT,
                    photo_file_id TEXT,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS admin_state (
                    admin_id BIGINT PRIMARY KEY,
                    state TEXT,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
        conn.commit()


def set_employee_state(user_id: int, state: str | None = None, action: str | None = None,
                       phone: str | None = None, full_name: str | None = None,
                       photo_file_id: str | None = None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if state is None:
                cur.execute('DELETE FROM employee_state WHERE user_id=%s', (user_id,))
            else:
                cur.execute(
                    '''
                    INSERT INTO employee_state (user_id, state, action, phone, full_name, photo_file_id, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,NOW())
                    ON CONFLICT (user_id)
                    DO UPDATE SET state=EXCLUDED.state,
                                  action=COALESCE(EXCLUDED.action, employee_state.action),
                                  phone=COALESCE(EXCLUDED.phone, employee_state.phone),
                                  full_name=COALESCE(EXCLUDED.full_name, employee_state.full_name),
                                  photo_file_id=COALESCE(EXCLUDED.photo_file_id, employee_state.photo_file_id),
                                  updated_at=NOW()
                    ''',
                    (user_id, state, action, phone, full_name, photo_file_id),
                )
        conn.commit()


def get_employee_state(user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT state, action, phone, full_name, photo_file_id FROM employee_state WHERE user_id=%s', (user_id,))
            row = cur.fetchone()
    return row


def set_admin_state(admin_id: int, state: str | None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if state is None:
                cur.execute('DELETE FROM admin_state WHERE admin_id=%s', (admin_id,))
            else:
                cur.execute(
                    '''
                    INSERT INTO admin_state (admin_id, state, updated_at)
                    VALUES (%s,%s,NOW())
                    ON CONFLICT (admin_id)
                    DO UPDATE SET state=EXCLUDED.state, updated_at=NOW()
                    ''',
                    (admin_id, state),
                )
        conn.commit()


def get_admin_state(admin_id: int) -> str | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT state FROM admin_state WHERE admin_id=%s', (admin_id,))
            row = cur.fetchone()
    return row[0] if row else None


def register_pending_employee(user_id: int, full_name: str, username: str | None, phone: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO employees (user_id, full_name, username, phone, status, updated_at)
                VALUES (%s,%s,%s,%s,'pending',NOW())
                ON CONFLICT (user_id)
                DO UPDATE SET full_name=EXCLUDED.full_name,
                              username=EXCLUDED.username,
                              phone=EXCLUDED.phone,
                              updated_at=NOW()
                ''',
                (user_id, full_name, username, phone),
            )
        conn.commit()


def approve_employee(user_id: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE employees SET status=%s, updated_at=NOW() WHERE user_id=%s', ('approved', user_id))
            ok = cur.rowcount > 0
        conn.commit()
    return ok


def remove_employee(user_id: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE employees SET status=%s, updated_at=NOW() WHERE user_id=%s', ('removed', user_id))
            ok = cur.rowcount > 0
        conn.commit()
    return ok


def is_employee_approved(user_id: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT status FROM employees WHERE user_id=%s', (user_id,))
            row = cur.fetchone()
    return bool(row and row[0] == 'approved')


def get_pending_employees():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT user_id, full_name, username, phone
                FROM employees
                WHERE status='pending'
                ORDER BY created_at DESC
                '''
            )
            return cur.fetchall()


def get_active_employees():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT user_id, full_name, username, phone
                FROM employees
                WHERE status='approved'
                ORDER BY full_name ASC
                '''
            )
            return cur.fetchall()


def record_attendance(user_id: int, action: str, latitude: float, longitude: float, photo_file_id: str):
    now = now_local()
    work_date = now.date()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT full_name FROM employees WHERE user_id=%s', (user_id,))
            row = cur.fetchone()
            full_name = row[0] if row else 'Noma’lum'
            cur.execute(
                '''
                INSERT INTO attendance (user_id, full_name, work_date, action, event_time, latitude, longitude, photo_file_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ''',
                (user_id, full_name, work_date, action, now, latitude, longitude, photo_file_id),
            )
        conn.commit()
    return full_name, now


def latest_today_event(user_id: int):
    d = now_local().date()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT action, event_time
                FROM attendance
                WHERE user_id=%s AND work_date=%s
                ORDER BY id DESC LIMIT 1
                ''',
                (user_id, d),
            )
            return cur.fetchone()


def get_daily_rows(work_date: date):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT e.user_id, e.full_name, e.username, e.phone,
                       MIN(CASE WHEN a.action='checkin' THEN a.event_time END) AS first_in,
                       MAX(CASE WHEN a.action='checkout' THEN a.event_time END) AS last_out
                FROM employees e
                LEFT JOIN attendance a ON a.user_id=e.user_id AND a.work_date=%s
                WHERE e.status='approved'
                GROUP BY e.user_id, e.full_name, e.username, e.phone
                ORDER BY e.full_name ASC
                ''',
                (work_date,),
            )
            return cur.fetchall()


def create_daily_excel(work_date: date) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = 'Kunlik hisobot'
    ws.append(['Sana', 'Xodim', 'Username', 'Telefon', 'Kelgan', 'Ketgan', 'Holat'])
    for user_id, full_name, username, phone, first_in, last_out in get_daily_rows(work_date):
        status = 'Kelmagan'
        if first_in and last_out:
            status = 'Kelgan/Ketgan'
        elif first_in:
            status = 'Kelgan'
        ws.append([
            str(work_date), full_name, f'@{username}' if username else '-', phone or '-',
            first_in.strftime('%H:%M') if first_in else '-',
            last_out.strftime('%H:%M') if last_out else '-',
            status
        ])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio


def create_month_excel(year: int, month: int) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = 'Oylik hisobot'
    ws.append(['Xodim', 'Kelgan kun', 'Ketgan kun'])
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT e.full_name,
                       COUNT(DISTINCT CASE WHEN a.action='checkin' THEN a.work_date END) AS days_in,
                       COUNT(DISTINCT CASE WHEN a.action='checkout' THEN a.work_date END) AS days_out
                FROM employees e
                LEFT JOIN attendance a ON a.user_id=e.user_id
                    AND EXTRACT(YEAR FROM a.work_date)=%s
                    AND EXTRACT(MONTH FROM a.work_date)=%s
                WHERE e.status='approved'
                GROUP BY e.full_name
                ORDER BY e.full_name ASC
                ''',
                (year, month),
            )
            for row in cur.fetchall():
                ws.append(list(row))
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio
