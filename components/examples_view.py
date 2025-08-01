import flet as ft


class ExamplesView(ft.Column):
    def __init__(self, gallery):
        super().__init__()
        self.gallery = gallery
        self.visible = False
        self.expand = True
        self.control_name_text = ft.Text(theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM)
        self.control_description = ft.Text(theme_style=ft.TextThemeStyle.BODY_MEDIUM)
        self.examples = ft.Column(expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)

        self.controls = [self.examples]

    def display(self, grid_item):
        self.visible = True
        self.examples.controls = []
        self.control_name_text.value = grid_item.title
        self.control_description.value = grid_item.description

        self.examples.controls.append(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    grid_item.example.name,
                                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                    weight=ft.FontWeight.W_500,
                                )
                            ],
                        ),
                        bgcolor=ft.Colors.SECONDARY_CONTAINER,
                        padding=10,
                        border_radius=5,
                    ),
                    ft.Container(
                        content=grid_item.example.example(),
                        clip_behavior=ft.ClipBehavior.NONE,
                    ),
                ],
            )
        )
