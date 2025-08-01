import logging

import flet as ft

from components.gallery_view import GalleryView
from gallerydata import GalleryData
from data_base import create_database, create_images
from notification_manager import NotificationManager
gallery = GalleryData()

logging.basicConfig(level=logging.INFO)


def main(page: ft.Page):
    page.title = "Системы мониторинга показаний оборудования"
    page.window.height = 760
    page.window.width = 1440
    page.horizontal_alignment = "stretch"
    page.vertical_alignment = "stretch"
    page.fonts = {
        "Roboto Mono": "RobotoMono-VariableFont_wght.ttf",
        "RobotoSlab": "RobotoSlab[wght].ttf",
    }
    create_database()
    create_images()

    NotificationManager.init(page)

    def get_route_list(route):
        route_list = [item for item in route.split("/") if item != ""]
        return route_list

    def route_change(e):
        route_list = get_route_list(page.route)
        if len(route_list) == 0:
            page.go("/filereader")
        else:
            gallery_view.display_control_examples(route_list[0])

    gallery_view = GalleryView(gallery)

    page.appbar = ft.AppBar(
        leading=ft.Container(padding=5, content=ft.Image(src=f"web-app-analytics-icon.svg",
                                                         fit=ft.ImageFit.CONTAIN)
                             ),
        leading_width=100,
        title=ft.Text("Системы мониторинга показаний оборудования", size=32, weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.Colors.INVERSE_PRIMARY,
        actions=[
            ft.Container(
                padding=5, content=ft.Text(f"Разработчик:\nСушков Д.С. ИИСм-1-23", text_align=ft.TextAlign.CENTER)
            )
        ],
    )

    page.theme_mode = ft.ThemeMode.LIGHT
    page.on_error = lambda e: print("Page error:", e.data)

    page.add(gallery_view)
    page.on_route_change = route_change
    print(f"Initial route: {page.route}")
    page.go(page.route)


ft.app(target=main, assets_dir="assets")
