# HƯỚNG DẪN SỬ DỤNG ALEMBIC MIGRATION

## 1. KHỞI TẠO

**Bước 1: Tạo bản ghi nhận hiện trạng**
```bash
alembic revision --autogenerate -m "baseline_initial"
docker exec backend alembic revision --autogenerate -m "baseline_initial" # Nếu dùng Docker
```

**Bước 1: Tạo version**
```bash
alembic upgrade head
docker exec backend alembic upgrade head # Nếu dùng Docker
```

## 2. CÁC LỆNH QUẢN LÝ

**Quay lui về bản version trước**
```bash
alembic downgrade -1
```

**Xem lịch sử các phiên bản**
```bash
alembic history
```
**Xem phiên bản hiện tại của Database**
```bash
alembic current
```

**Seed bộ đếm Database**
```bash
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT table_name, column_name, pg_get_serial_sequence(table_name, column_name) as seq
              FROM information_schema.columns 
              WHERE column_default LIKE 'nextval%') 
    LOOP
        IF r.seq IS NOT NULL THEN
            EXECUTE format('SELECT setval(%L, (SELECT COALESCE(MAX(%I), 0) FROM %I) + 1, false)', 
                           r.seq, r.column_name, r.table_name);
        END IF;
    END LOOP;
END $$;
```