import sqlite3
from typing import List, Dict, Any

DB_NAME = "gauge_readings.db"


# Создание таблицы
def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT,
            final_reading TEXT,
            datetime_read TEXT,
            empty TEXT, 
            raw_value REAL,
            unit TEXT,
            needle_angle TEXT,
            scale_marks TEXT,
            filename TEXT,
            resolution TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def create_images():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            datetime_read TEXT,
            image BLOB,
            mask BLOB,
            binarized BLOB,
            edges BLOB,
            overlay BLOB,
            filled BLOB
        )
    ''')
    conn.commit()
    conn.close()


def insert_record(data):
    data[7] = ', '.join([str(s) for s in data[7]])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO readings (
            status, 
            final_reading, 
            datetime_read,
            empty, 
            raw_value, 
            unit,
            needle_angle, 
            scale_marks, 
            filename, 
            resolution, 
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()


def insert_images(name, date, images):
    # Гарантируем, что массив имеет ровно 6 элементов, заполняя None при необходимости
    padded_images = list(images) + [None] * (6 - len(images))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO images (
        filename,
        datetime_read,
        image,
        mask,
        binarized,
        edges,
        overlay,
        filled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, date, *padded_images[:6]))
    conn.commit()
    conn.close()


def delete_record(ids: list[int]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM readings WHERE id = ?", [(i,) for i in ids])
    cursor.executemany("DELETE FROM images WHERE id = ?", [(i,) for i in ids])
    conn.commit()
    conn.close()


def fetch_all_records() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM readings')
    columns = [description[0] for description in cursor.description]
    records = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return records


def fetch_selectod_images(reading, datetime_read):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM images WHERE filename = ? AND datetime_read = ?', (reading, datetime_read))
    images = cursor.fetchall()  # список кортежей [(img1,), (img2,), ...]
    conn.close()
    return images


# Загружаем изображение из базы данных и отображаем в диалоге
def get_image(filename, datetime_read, btn):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    match btn:
        case 0:
            cursor.execute(
                "SELECT image FROM images WHERE filename = ? AND datetime_read = ?",
                (filename, datetime_read)
            )
        case 1:
            cursor.execute(
                "SELECT mask FROM images WHERE filename = ? AND datetime_read = ?",
                (filename, datetime_read)
            )
        case 2:
            cursor.execute(
                "SELECT binarized FROM images WHERE filename = ? AND datetime_read = ?",
                (filename, datetime_read)
            )
        case 3:
            cursor.execute(
                "SELECT edges FROM images WHERE filename = ? AND datetime_read = ?",
                (filename, datetime_read)
            )
        case 4:
            cursor.execute(
                "SELECT overlay FROM images WHERE filename = ? AND datetime_read = ?",
                (filename, datetime_read)
            )
        case 5:
            cursor.execute(
                "SELECT filled FROM images WHERE filename = ? AND datetime_read = ?",
                (filename, datetime_read)
            )
    result = cursor.fetchone()
    conn.close()
    return result
