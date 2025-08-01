import argparse
import json
import os

import cv2
import matplotlib.pyplot as plt

import numpy as np
import torch

IMAGE_DIR = 'images'
LABEL_DIR = 'labels'


def get_data_from_json(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return data


def get_annotations(data):
    annotation_list = []
    for data_point in data:

        key_point_annotation = {}

        # Получите имя изображения. У нас есть имя изображения в формате :
        # /data/upload/1/222ae49e-1_cropped_000001_jpg.rf.c7410b0b01b2bc3a6cdff656618a3015.jpg
        # избавьтесь от всего, что находится перед '-'
        idx = data_point['data']['img'].find('-') + 1
        key_point_annotation['img_name'] = data_point['data']['img'][idx:]

        key_point_annotation['start'] = []
        key_point_annotation['end'] = []
        key_point_annotation['middle'] = []

        for annotation in data_point['annotations'][0]['result']:

            if annotation['value']['keypointlabels'][0] == 'Start Notch':
                key_point_annotation['start'].append(
                    {k: annotation['value'][k]
                     for k in ('x', 'y')})

            if annotation['value']['keypointlabels'][0] == 'End Notch':
                key_point_annotation['end'].append(
                    {k: annotation['value'][k]
                     for k in ('x', 'y')})

            if annotation['value']['keypointlabels'][0] == 'Inbetween Notch':
                key_point_annotation['middle'].append(
                    {k: annotation['value'][k]
                     for k in ('x', 'y')})

        annotation_list.append(key_point_annotation)

    return annotation_list


def add_gaussian_to_heatmap(heatmap, x, y, sigma=8, visualize=False):
    """
    Генерирует двумерную гауссову точку в месте x,y в тензоре t.

    x должно быть в диапазоне (-1, 1), чтобы соответствовать выводу PointScaler в fastai.

    sigma - стандартное отклонение сгенерированного двумерного гаусса.
    """
    h, w = heatmap.shape

    # Пиксель тепловой карты на один выходной пиксель

    tmp_size = sigma * 3

    # Левый верхний
    x1, y1 = int(x - tmp_size), int(y - tmp_size)

    # Внизу справа
    x2, y2 = int(x + tmp_size + 1), int(y + tmp_size + 1)

    size = 2 * tmp_size + 1
    tx = np.arange(0, size, 1, np.float32)
    ty = tx[:, np.newaxis]
    center = size // 2

    # Гаусс не нормализован, мы хотим, чтобы значение центра было равно 1
    gaussian = torch.tensor(
        np.exp(-((tx - center)**2 + (ty - center)**2) / (2 * sigma**2)))

    # Определите границы исходного гаусса
    g_x_min, g_x_max = max(0, -x1), min(x2, w) - x1
    g_y_min, g_y_max = max(0, -y1), min(y2, h) - y1

    # Диапазон изображений
    img_x_min, img_x_max = max(0, x1), min(x2, w)
    img_y_min, img_y_max = max(0, y1), min(y2, h)

    scale = 255 if visualize else 1

    # добавьте гаусс к тепловой карте, взяв максимальное значение
    heatmap[img_y_min:img_y_max, img_x_min:img_x_max] = \
        np.maximum(scale * gaussian[g_y_min:g_y_max, g_x_min:g_x_max],
                   heatmap[img_y_min:img_y_max, img_x_min:img_x_max])

    return heatmap


# key_point_list - список диктов с координатами 'x' и 'y', по 1 для каждой ключевой точки
# вывод тепловой карты
def generate_heatmap(key_point_list, img=None, size=(448, 448)):
    # Инициализация пустой тепловой карты
    if img is not None:
        heatmap = img
        visualize = True
    else:
        heatmap = torch.zeros(size)
        visualize = False

    # Для каждой ключевой точки добавьте к тепловой карте гауссово ядро, центрированное вокруг нее

    for key_point in key_point_list:
        heatmap = add_gaussian_to_heatmap(heatmap,
                                          key_point['x'] * size[0] / 100,
                                          key_point['y'] * size[1] / 100,
                                          visualize=visualize)

    return heatmap.numpy()


def heatmap_from_key_points(annotation, size):
    size = (size, size)
    heatmap_start = generate_heatmap(annotation['start'], size=size)
    heatmap_middle = generate_heatmap(annotation['middle'], size=size)
    heatmap_end = generate_heatmap(annotation['end'], size=size)

    heatmap = np.stack((heatmap_start, heatmap_middle, heatmap_end), axis=0)
    return heatmap


def main():
    args = read_args()
    json_path = args.annotation
    base_path = args.directory

    img_directory = os.path.join(base_path, IMAGE_DIR)
    label_directory = os.path.join(base_path, LABEL_DIR)

    if not os.path.exists(label_directory):
        os.makedirs(label_directory)

    data = get_data_from_json(json_path)
    annotations = get_annotations(data)

    fig = plt.figure(figsize=(10, 15))
    fig.subplots_adjust(left=0.05,
                        right=0.95,
                        bottom=0.05,
                        top=0.95,
                        wspace=0.1,
                        hspace=0.1)
    rows = int(len(annotations) / 20) + 1
    columns = 2

    plot_idx = 1
    for i, annotation in enumerate(annotations):
        heatmap = heatmap_from_key_points(annotation, args.size)
        if i % 13 == 0:
            img_path = os.path.join(img_directory, annotation['img_name'])
            image = cv2.imread(img_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            heatmap_show = generate_heatmap(annotation['middle'],
                                            torch.tensor(gray))
            fig.add_subplot(rows, columns, plot_idx)
            plt.axis('off')
            plt.imshow(heatmap_show)
            plot_idx += 1

        filename = annotation['img_name'][:-4] + '.npy'
        path = os.path.join(label_directory, filename)
        np.save(path, heatmap)
        i += 1
    plt.show()


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation',
                        type=str,
                        required=True,
                        help="json-файл с аннотациями")
    parser.add_argument('--directory',
                        type=str,
                        required=True,
                        help="Каталог, в котором находятся изображения и ярлыки")
    parser.add_argument('--size',
                        type=int,
                        required=True,
                        help="Формат тепловой карты - размер x размер")

    return parser.parse_args()


if __name__ == '__main__':
    main()
