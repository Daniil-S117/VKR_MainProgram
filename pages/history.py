import base64
import io
import os

from PIL import Image
import flet as ft
import numpy as np
from notification_manager import NotificationManager
from data_base import fetch_all_records, delete_record, get_image
from image_functions import process_image

name = "Обзор базы данных показаний манометров"

DB_NAME = "gauge_readings.db"

column_keys = ["id", "status", "final_reading", "datetime_read", "raw_value",
               "unit", "needle_angle", "scale_marks", "filename", "image"]

column_labels = ["ID", "Статус", "Итоговые\nПоказание", "Дата/Время\nсчитывания", "Значения",
                 "Единицы\nизмерения", "Угол\nстрелки", "Отметки\nшкалы", "Изображения"]

title_tabs = ["Оригинальное изображение", "Обнаружение прибора", "Сегментация стрелки",
              "Обнаружения меток & Наложение эллипса", "Распознавание отметок шкалы", "Итоговые показания"]


# Преобразуем BLOB -> numpy строку
def blob_to_numpy(blob: bytes) -> np.ndarray:
    with io.BytesIO(blob) as buffer:
        return np.load(buffer)


# Загружаем изображение из базы данных и отображаем в диалоге
def open_image_dialog(reading, datetime_read, btn):
    result = get_image(reading, datetime_read, btn)
    img_result = blob_to_numpy(result[0])
    new_image = Image.fromarray(img_result)
    buff = io.BytesIO()
    new_image.save(buff, format="JPEG")
    image_string = base64.b64encode(buff.getvalue()).decode('utf-8')
    NotificationManager.image_view(image_string, btn)


def example():
    pb = ft.ProgressBar(height=2, expand=True, bgcolor="#eeeeee", value=0)
    text_message = ft.Text(value="")

    # Cтруктура данных
    data = fetch_all_records()

    def pick_files_result(e: ft.FilePickerResultEvent):
        nonlocal data
        filepicker_example.disabled = True
        filepicker_example.update()
        if os.path.isdir(e.path):
            lst = os.listdir(e.path)
            procent = 1.00 / len(lst)
            for image_name in os.listdir(e.path):
                pb.value = pb.value + procent
                pb.update()
                img_path = os.path.join(e.path, image_name)
                text_message.value = f"Обработка изображений по пути: {img_path}"
                text_message.update()
                results, new_images = process_image(img_path,
                                                    debug='--debug',
                                                    eval_mode='--eval')
        text_message.value = f"Закончена обработка изображений по пути: {e.path}"
        text_message.update()
        pb.value = 0
        pb.update()
        filepicker_example.disabled = False
        filepicker_example.update()
        data = fetch_all_records()
        render_rows()
        table.update()

    class PickDir(ft.Row):
        def __init__(self):
            super().__init__()
            self.pick_files_dialog = ft.FilePicker(on_result=pick_files_result)

            def pick_files(_):
                self.pick_files_dialog.get_directory_path()

            self.controls = [
                ft.ElevatedButton(
                    expand=True,
                    height=40,
                    on_click=pick_files,
                    content=ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.DRIVE_FILE_MOVE),
                            ft.Text(
                                value="Выбрать папку с изображениями",
                                weight=ft.FontWeight.BOLD
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.INVERSE_PRIMARY
                ),
            ]

        # происходит при добавлении примера на страницу (
        def did_mount(self):
            self.page.overlay.append(self.pick_files_dialog)
            self.page.update()

        # происходит, когда пример удаляется со страницы
        def will_unmount(self):
            self.page.overlay.remove(self.pick_files_dialog)
            self.page.update()

    filepicker_example = PickDir()

    # Флаг сортировки
    sort_asc = {key: True for key in column_keys}
    selected_ids = set()
    checkboxes = []
    select_all_checkbox = ft.Checkbox(value=False)
    table = ft.DataTable(
        expand=True,
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
        border=ft.border.all(2, ft.Colors.SECONDARY_CONTAINER),
        border_radius=10,
        vertical_lines=ft.border.BorderSide(3, ft.Colors.BLUE),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREEN),
        sort_column_index=0,
        sort_ascending=True,
        heading_row_color=ft.Colors.BLACK12,
        heading_row_height=50,
        data_row_max_height=100,
        data_row_color={ft.ControlState.HOVERED: "0x30FF0000"},
        divider_thickness=0,
        column_spacing=15,
        columns=[ft.DataColumn(label=select_all_checkbox)],
        rows=[],
    )

    def toggle_all_rows(e):
        for i, cb in enumerate(checkboxes):
            cb.value = select_all_checkbox.value
            if cb.value:
                selected_ids.add(data[i]['id'])
            else:
                selected_ids.discard(data[i]['id'])
        table.update()

    select_all_checkbox.on_change = toggle_all_rows

    def render_rows():
        table.rows.clear()
        checkboxes.clear()
        for row in data:
            row_checkbox = ft.Checkbox(value=row['id'] in selected_ids)

            def toggle_cb(e, rid=row['id'], cb=row_checkbox):
                if cb.value:
                    selected_ids.add(rid)
                else:
                    selected_ids.discard(rid)

            row_checkbox.on_change = toggle_cb
            checkboxes.append(row_checkbox)

            if str(row['status']) == "Норма / Рабочее давление":
                clr = ft.Colors.GREEN
            elif str(row['status']) == "Отключён / Не под давлением":
                clr = ft.Colors.ORANGE
            else:
                clr = ft.Colors.RED

            table.rows.append(
                ft.DataRow(
                    selected=row['id'] in selected_ids,
                    cells=[
                        ft.DataCell(row_checkbox),
                        ft.DataCell(ft.Text(str(row['id']), text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(ft.Text(str(row['status']), text_align=ft.TextAlign.CENTER, color=clr,
                                            weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(str(row['final_reading']), text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(ft.Text(row['datetime_read'], text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(ft.Text(str(row['raw_value']), text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(ft.Text(str(row['unit']), text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(ft.Text(str(row['needle_angle']), text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(ft.Text(str(row['scale_marks']), text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(
                            content=ft.Column(expand=True, alignment=ft.alignment.center, controls=[
                                ft.Container(content=ft.Text(str(row['filename']), text_align=ft.TextAlign.CENTER),
                                             alignment=ft.alignment.center),
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.IMAGE_ROUNDED, icon_color=ft.Colors.WHITE,
                                        tooltip=title_tabs[0],
                                        on_click=lambda e, r=row['filename'], d=row["datetime_read"]:
                                        open_image_dialog(r, d, 0)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.IMAGE_SEARCH_ROUNDED, icon_color=ft.Colors.BLUE,
                                        tooltip=title_tabs[1],
                                        on_click=lambda e, r=row['filename'], d=row["datetime_read"]:
                                        open_image_dialog(r, d, 1)),
                                    ft.IconButton(
                                        icon=ft.Icons.SPEED_ROUNDED, icon_color=ft.Colors.YELLOW,
                                        tooltip=title_tabs[3],
                                        on_click=lambda e, r=row['filename'], d=row["datetime_read"]:
                                        open_image_dialog(r, d, 2)),
                                    ft.IconButton(
                                        icon=ft.Icons.SETTINGS, icon_color=ft.Colors.GREEN,
                                        tooltip=title_tabs[2],
                                        on_click=lambda e, r=row['filename'], d=row["datetime_read"]:
                                        open_image_dialog(r, d, 3)),
                                    ft.IconButton(
                                        icon=ft.Icons.NUMBERS_ROUNDED, icon_color=ft.Colors.ORANGE,
                                        tooltip=title_tabs[4],
                                        on_click=lambda e, r=row['filename'], d=row["datetime_read"]:
                                        open_image_dialog(r, d, 4)),
                                    ft.IconButton(
                                        icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.RED,
                                        tooltip=title_tabs[5],
                                        on_click=lambda e, r=row['filename'], d=row["datetime_read"]:
                                        open_image_dialog(r, d, 5))
                                ],
                                    spacing=0
                                )
                            ]
                                              )
                        )
                    ],
                )
            )

    def make_sort_handler(field):
        def handler(e):
            reverse = not sort_asc[field]
            sort_asc[field] = reverse
            data.sort(
                key=lambda x: (x[field] is None, x[field]),
                reverse=reverse
            )
            render_rows()
            table.update()

        return handler

    # Создаём колонки с сортировкой
    for i, label in enumerate(column_labels):
        table.columns.append(
            ft.DataColumn(
                label=ft.Text(label, text_align=ft.TextAlign.CENTER),
                heading_row_alignment=ft.MainAxisAlignment.CENTER,
                on_sort=make_sort_handler(column_keys[i]) if column_keys[i] != "image" else None
            )
        )

    def delete_selected(e):
        nonlocal data
        if selected_ids:
            data[:] = [row for row in data if row["id"] not in selected_ids]
            delete_record(list(selected_ids))
            selected_ids.clear()
            select_all_checkbox.value = False
            render_rows()
            table.update()

    render_rows()

    return ft.Column(
        expand=True,
        controls=[
            pb,
            ft.Row(
                controls=[
                    ft.Container(
                        alignment=ft.alignment.center_right,
                        content=ft.ElevatedButton(
                            width=200,
                            height=40,
                            on_click=delete_selected,
                            content=ft.Row(
                                controls=[
                                    ft.Icon(name=ft.Icons.DELETE, color=ft.Colors.WHITE),
                                    ft.Text(
                                        value="Удалить выбранные",
                                        color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.BOLD
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            bgcolor=ft.Colors.RED
                        )
                    ),
                    filepicker_example,
                    text_message
                ]
            ),
            ft.Container(
                expand=True,
                content=table
            )
        ]
    )
