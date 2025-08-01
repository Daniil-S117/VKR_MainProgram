import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from image_functions import process_image

_detection_model_path = "models/gauge_detection_model.pt"
_base_path = "results"


def open_image():
    file_path = filedialog.askopenfilename(title="Open Image File",
                                           filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")])

    if file_path:
        new_image = process_image(file_path,
                                  debug='--debug',
                                  eval_mode='--eval')
        print(type(new_image))
        display_image(new_image)


def display_image(image):
    #image = Image.open(file_path)
    photo = ImageTk.PhotoImage(image=Image.fromarray(image))
    print(type(photo))
    image_label.config(image=photo)
    image_label.photo = photo
    status_label.config(text=f"Image loaded: {image}")


root = tk.Tk()
root.title("Система мониторинга оборудования")
text_widget = tk.Text(root, wrap=tk.WORD, height=15, width=35)
open_button = tk.Button(root, text="Открыть изображение", command=open_image)
open_button.pack(padx=20, pady=10)
image_label = tk.Label(root)
image_label.pack(padx=20, pady=20)
status_label = tk.Label(root, text="", padx=20, pady=10)
status_label.pack()
root.mainloop()
