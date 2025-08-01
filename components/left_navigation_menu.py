import flet as ft


class PopupColorItem(ft.PopupMenuItem):
    def __init__(self, color, name):
        super().__init__()
        self.content = ft.Row(
            controls=[
                ft.Icon(name=ft.Icons.COLOR_LENS_OUTLINED, color=color),
                ft.Text(name),
            ],
        )
        self.on_click = self.seed_color_changed
        self.data = color

    def seed_color_changed(self, e):
        self.page.theme = self.page.dark_theme = ft.Theme(color_scheme_seed=self.data)
        self.page.update()


class NavigationItem(ft.Container):
    def __init__(self, destination, item_clicked):
        super().__init__()
        self.ink = True
        self.padding = 10
        self.border_radius = 5
        self.destination = destination
        self.icon = destination.icon
        self.text = destination.label
        self.content = ft.Row([ft.Icon(self.icon), ft.Text(self.text)])
        self.on_click = item_clicked


class NavigationColumn(ft.Column):
    def __init__(self, gallery, item_clicked):
        super().__init__()
        self.expand = False
        self.spacing = 0
        self.scroll = ft.ScrollMode.ADAPTIVE
        self.width = 200
        self.gallery = gallery
        self.selected_index = 0
        self.controls = self.get_navigation_items(item_clicked)

    def get_navigation_items(self, item_clicked):
        navigation_items = []
        for destination in self.gallery:
            navigation_items.append(
                NavigationItem(destination, item_clicked=item_clicked)
            )
        return navigation_items


class Divider(ft.Container):
    def __init__(self):
        super().__init__()
        self.bgcolor = ft.Colors.ON_SECONDARY_CONTAINER
        self.border_radius = ft.border_radius.all(30)
        self.height = 2
        self.margin = ft.margin.all(0)
        self.alignment = ft.alignment.center_right
        self.width = 200


class Headline(ft.Container):
    def __init__(self, value):
        super().__init__()
        self.bgcolor = ft.Colors.PRIMARY_CONTAINER
        self.width = 200
        self.border_radius = 5
        self.padding = 10
        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    value=value,
                    weight=ft.FontWeight.BOLD,
                    size=14,
                ),
            ],
        )


class LeftNavigationMenu(ft.Column):
    def __init__(self, gallery):
        super().__init__()
        self.gallery = gallery
        self.spacing = 5
        self.railOne = NavigationColumn(gallery=gallery.control_groupsOne, item_clicked=self.item_clicked_one)
        self.railTwo = NavigationColumn(gallery=gallery.control_groupsTwo, item_clicked=self.item_clicked_two)
        self.headlineOne = Headline(value="Определение показаний")
        self.headlineTwo = Headline(value="База данных")
        self.headlineThree = Headline(value="Опции")
        self.divider = Divider()
        self.dark_light_text = ft.Text("Светлая тема")
        self.dark_light_icon = ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_2_OUTLINED,
            tooltip="Настройка яркости",
            on_click=self.theme_changed,
        )

        self.controls = [
            self.headlineOne,
            self.railOne,
            self.divider,
            self.headlineTwo,
            self.railTwo,
            self.divider,
            self.headlineThree,
            ft.Column(
                expand=1,
                controls=[
                    ft.Row(
                        controls=[
                            self.dark_light_icon,
                            self.dark_light_text,
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.PopupMenuButton(
                                icon=ft.Icons.COLOR_LENS_OUTLINED,
                                tooltip="Настройка цвета",
                                items=[
                                    PopupColorItem(
                                        color="deeppurple", name="Фиолетовый"),
                                    PopupColorItem(color="indigo", name="Синий"),
                                    PopupColorItem(color="blue", name="Голубой (по умолчанию)"),
                                    PopupColorItem(color="teal", name="Тиловый"),
                                    PopupColorItem(color="green", name="Зелёный"),
                                    PopupColorItem(color="yellow", name="Жёлтый"),
                                    PopupColorItem(color="orange", name="Оранжевый"),
                                    PopupColorItem(color="red", name="Красный"),
                                    PopupColorItem(color="pink", name="Розовый"),
                                ],
                            ),
                            ft.Text("Цвет оформления"),
                        ]
                    ),
                ],
            ),
        ]

    def item_clicked_one(self, e):
        index = e.control.destination.index
        for item in self.railOne.controls + self.railTwo.controls:
            item.bgcolor = None
            item.content.controls[0].name = item.destination.icon
        self.railOne.controls[index].bgcolor = ft.Colors.SECONDARY_CONTAINER
        self.railOne.controls[index].content.controls[0].name = self.railOne.controls[
            index].destination.selected_icon
        print(f"/{e.control.destination.name}")
        self.page.go(f"/{e.control.destination.name}")

    def item_clicked_two(self, e):
        index = e.control.destination.index
        for item in self.railTwo.controls + self.railOne.controls:
            item.bgcolor = None
            item.content.controls[0].name = item.destination.icon
        self.railTwo.controls[index].bgcolor = ft.Colors.SECONDARY_CONTAINER
        self.railTwo.controls[index].content.controls[0].name = self.railTwo.controls[
            index].destination.selected_icon
        self.page.go(f"/{e.control.destination.name}")

    def theme_changed(self, e):
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.dark_light_text.value = "Тёмная тема"
            self.dark_light_icon.icon = ft.Icons.BRIGHTNESS_HIGH
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.dark_light_text.value = "Светлая тема"
            self.dark_light_icon.icon = ft.Icons.BRIGHTNESS_2
        self.page.update()
