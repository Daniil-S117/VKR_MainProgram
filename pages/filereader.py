import base64

import flet as ft
from image_functions import process_image
from PIL import Image
from io import BytesIO

name = "Выбор изображения для определения показаний прибора"


def example():
    pb = ft.ProgressBar(expand=True, color="amber", bgcolor="#eeeeee", value=0)
    img_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS_WITH_SAVE_LAYER,
        scrollable=False,
        tab_alignment=ft.TabAlignment.FILL,
        tabs=[],
        expand=True,
        height=500,
    )

    def pick_files_result(e: ft.FilePickerResultEvent):
        filepicker_example.disabled = True
        filepicker_example.update()
        pb.value = None
        pb.update()
        processed_images = []
        if e.files:
            results, new_images = process_image(e.files[0].path,
                                                debug='--debug',
                                                eval_mode='--eval')
            for new_image in new_images:
                new_image = Image.fromarray(new_image)
                buff = BytesIO()
                new_image.save(buff, format="JPEG")
                image_string = base64.b64encode(buff.getvalue()).decode('utf-8')
                processed_image = ft.InteractiveViewer(content=ft.Image(src_base64=image_string),
                                                       scale_enabled=True,
                                                       pan_enabled=True,
                                                       boundary_margin=20, )
                processed_images.append(processed_image)
            edit_table(results)
            fill_tabs(processed_images)
            img_tabs.update()
        pb.value = 0
        pb.update()
        filepicker_example.disabled = False
        filepicker_example.update()

    class PickFiles(ft.Row):
        def __init__(self):
            super().__init__()
            self.pick_files_dialog = ft.FilePicker(on_result=pick_files_result)

            def pick_files(_):
                self.pick_files_dialog.pick_files(allow_multiple=True)

            self.controls = [
                ft.ElevatedButton(
                    expand=True,
                    height=50,
                    on_click=pick_files,
                    content=ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.START_ROUNDED),
                            ft.Text(
                                value="ВЫБРАТЬ ИЗОБРАЖЕНИЕ",
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

    filepicker_example = PickFiles()

    def fill_tabs(images):
        title_tabs = ["Оригинальное изображение", "Обнаружение прибора", "Сегментация стрелки",
                      "Обнаружения меток & Наложение эллипса", "Распознавание отметок шкалы", "Итоговые показания"]

        tabs_icons = [ft.Icons.IMAGE_ROUNDED, ft.Icons.IMAGE_SEARCH_ROUNDED, ft.Icons.SPEED_ROUNDED,
                      ft.Icons.SETTINGS, ft.Icons.NUMBERS_ROUNDED, ft.Icons.ADD_CIRCLE]

        img_tabs.tabs.clear()
        main_content = []
        ind = len(images) - 1
        for i in range(6):
            try:
                main_content.append(
                    ft.Container(
                        content=images[i],
                        expand=True,
                        alignment=ft.alignment.center,
                    )
                )
            except IndexError:
                main_content.append(
                    ft.Container(
                        ft.Text(
                            value="Нет изображения",
                            color="red",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                        expand=True,
                        alignment=ft.alignment.center
                    )
                )
            new_tab = ft.Tab(
                text=str(i + 1),
                icon=tabs_icons[i],
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                alignment=ft.alignment.center,
                                content=ft.Text(title_tabs[i],
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                                text_align=ft.TextAlign.CENTER,
                                                ),
                                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                            ),
                            main_content[i]
                        ]
                    ),
                    alignment=ft.alignment.center
                ),
            )
            img_tabs.tabs.append(new_tab)
        if img_tabs.selected_index != 6:
            img_tabs.selected_index = ind

    img_array = []
    fill_tabs(img_array)

    # Исходные данные таблицы
    table_data = [
        [ft.Text("Статус:", size=20, no_wrap=True), ft.Text("", size=17, weight=ft.FontWeight.BOLD)],
        [ft.Text("Итоговые показания:", size=17), ft.Text("", size=18, weight=ft.FontWeight.BOLD)],
        [ft.Text("Дата/Время\nсчитывания:", size=17), ft.Text("", size=18, weight=ft.FontWeight.BOLD)],
        [ft.Text("Доп. свойства", size=19, weight=ft.FontWeight.BOLD, no_wrap=True), ft.Text("", size=18)],
        [ft.Text("Значения:", size=16), ft.Text("", size=16)],
        [ft.Text("Единица измерения:", size=16), ft.Text("", size=16)],
        [ft.Text("Угол поворота стрелки:", size=16), ft.Text("", size=16)],
        [ft.Text("Отметки на шкале:", size=16), ft.Text("", size=16, no_wrap=False)],
        [ft.Text("Название изображения:", size=16), ft.Text("", size=16, no_wrap=False)],
        [ft.Text("Разрешение изображения:", size=16), ft.Text("", size=16)],
        [ft.Text("Дата создания \nизображения:", size=16), ft.Text("", size=16)],
    ]

    # Функция генерации строк таблицы
    def generate_rows():
        return [
            ft.DataRow(
                cells=[
                    ft.DataCell(param),
                    ft.DataCell(value),
                ]
            ) for param, value in table_data
        ]

    def edit_table(results):
        if results[0] == "Норма / Рабочее давление":
            table_data[0][1].color = ft.Colors.GREEN
        elif results[0] == "Отключён / Не под давлением":
            table_data[0][1].color = ft.Colors.ORANGE
        else:
            table_data[0][1].color = ft.Colors.RED
        for i in range(len(results)):
            table_data[i][1].value = results[i]
        datatable.rows = generate_rows()
        datatable.update()

    datatable = ft.DataTable(
        bgcolor=ft.Colors.SECONDARY_CONTAINER,
        columns=[
            ft.DataColumn(ft.Text("Информация", size=20, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Значение", size=20, weight=ft.FontWeight.BOLD)),
        ],
        heading_row_height=50,
        rows=generate_rows(),
        border=ft.border.all(1, ft.Colors.BLACK),
        border_radius=10,
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.INVERSE_PRIMARY,
                                              stroke_align=ft.BorderSideStrokeAlign.CENTER),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.INVERSE_PRIMARY, stroke_align=ft.BorderSideStrokeAlign.CENTER),
    )

    return ft.Row(
        expand=True,
        controls=[
            ft.Container(
                expand=True,
                content=ft.Column(
                    controls=[
                        img_tabs,
                        pb,
                        filepicker_example
                    ]
                )

            ),
            ft.Container(
                expand=True,
                content=datatable

            ),
        ]
    )
