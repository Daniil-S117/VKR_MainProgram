import importlib.util
import os
import sys
from os.path import isfile, join
from pathlib import Path

import flet as ft


class ExampleItem:
    def __init__(self):
        self.name = None
        self.file_name = None
        self.order = None
        self.example = None
        # self.source_code = None


class ControlGroup:
    def __init__(self, name, label, icon, selected_icon, index):
        self.name = name
        self.file_name = None
        self.title = None
        self.label = label
        self.icon = icon
        self.selected_icon = selected_icon
        self.index = index
        self.description = None
        self.example = None


class GalleryData:
    def __init__(self):
        self.control_groups = [
            ControlGroup(
                name="filereader",
                label="Выбрать файл",
                icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                selected_icon=ft.Icons.UPLOAD_FILE_OUTLINED,
                index=0,
            ),
            # ControlGroup(
            #     name="camera",
            #     label="Видеокамера",
            #     icon=ft.Icons.VIDEO_CAMERA_BACK_ROUNDED,
            #     selected_icon=ft.Icons.VIDEO_CAMERA_BACK_OUTLINED,
            #     index=1,
            # ),
            ControlGroup(
                name="history",
                label="История",
                icon=ft.Icons.BOOK_OUTLINED,
                selected_icon=ft.Icons.BOOK_OUTLINED,
                index=0,
            ),
            # ControlGroup(
            #     name="analytics",
            #     label="Аналитика",
            #     icon=ft.Icons.ANALYTICS_ROUNDED,
            #     selected_icon=ft.Icons.ANALYTICS_OUTLINED,
            #     index=1,
            # ),
            # ControlGroup(
            #     name="users",
            #     label="Пользователи",
            #     icon=ft.Icons.PERSON,
            #     selected_icon=ft.Icons.PERSON,
            #     index=3,
            # )
        ]
        self.import_modules()
        self.control_groupsOne = self.control_groups[:1]
        self.control_groupsTwo = self.control_groups[1:]
        # self.selected_control_group = self.control_groups[0]

    def get_control(self, control_name):
        for control_group in self.control_groups:
            if control_group.name == control_name:
                return control_group
            # return self.control_groups[0].grid_items[0]

    def list_example_files(self, control_group_dir):
        print(str(Path(__file__).parent), "pages", control_group_dir)
        file_path = os.path.join(
            str(Path(__file__).parent), "pages", control_group_dir)
        example_files = [f for f in os.listdir(file_path) if not f.startswith("_")]
        return example_files

    def import_modules(self):
        for page in self.control_groups:
            file_name = os.path.join("pages", page.name + ".py")
            module_name = file_name.replace("/", ".").replace(".py", "")

            if module_name in sys.modules:
                print(f"{module_name!r} already in sys.modules")
            else:
                file_path = os.path.join(
                    str(Path(__file__).parent), file_name
                )

                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                print(f"{module_name!r} has been imported")
                example_item = ExampleItem()
                example_item.example = module.example

                page.file_name = (
                        module_name.replace(".", "/") + ".py"
                )
                example_item.name = module.name
                page.example = example_item
