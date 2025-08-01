import flet as ft


title_tabs = ["Оригинальное изображение", "Обнаружение прибора", "Обнаружения меток & Наложение эллипса",
              "Сегментация иглы", "Распознавание отметок шкалы", "Итоговые показания"]

class NotificationManager:
    _page: ft.Page = None

    @classmethod
    def init(cls, page: ft.Page):
        cls._page = page

    @classmethod
    def show(cls, message: str, signal=True):
        color = ft.Colors.GREEN
        if signal is False:
            color = ft.Colors.RED
        if cls._page:
            cls._page.open(ft.SnackBar(content=ft.Text(message, weight=ft.FontWeight.BOLD), bgcolor=color, duration=10000))
            cls._page.update()
        else:
            print("❗ Страница не инициализируется в NotificationManager.")

    @classmethod
    def image_view(cls, image_string, btn):
        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text(title_tabs[btn], weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            content=ft.Container(
                width=500,
                height=500,
                content=ft.InteractiveViewer(
                    content=ft.Image(src_base64=image_string),
                    expand=True,
                    scale_enabled=True,
                    pan_enabled=True,
                )
            ),
        )
        cls._page.open(dialog)
