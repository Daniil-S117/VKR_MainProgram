import argparse
import json
import os
import sys
import cv2
import numpy as np
from PIL import Image

import constants
from eval_plots import EvalPlotter

# Добавление пути к родительскому каталогу в систему, чтобы корректно импортировать все модули
parent_dir = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
sys.path.append(parent_dir)

# pylint: disable=wrong-import-position
from image_functions import crop_image, RESOLUTION
from key_point_detection.key_point_extraction import key_point_metrics, PCK_KEY, \
    MEAN_DIST_KEY, NON_ASSIGNED_KEY

IOU_THRESHOLD = 0.5


# Аннотации label-studio всегда имеют масштаб 0,100, поэтому необходимо изменить масштаб
def convert_bbox_annotation(single_bbox_dict, img_width, img_height):
    single_bbox_dict['x'] *= img_width / 100
    single_bbox_dict['y'] *= img_height / 100
    single_bbox_dict['width'] *= img_width / 100
    single_bbox_dict['height'] *= img_height / 100


def get_annotations_bbox(data):
    """
    Функция для извлечения аннотации из формата label-studio
    """

    annotation_dict = {}

    for data_point in data:

        bbox_annotations = {}
        # Получение имени изображения. У нас есть имя изображения в формате :
        # /data/upload/1/222ae49e-1_cropped_000001_jpg.rf.c7410b0b01b2bc3a6cdff656618a3015.jpg
        # избавьтесь от всего, что находится перед '-'
        idx = data_point['data']['image'].find('-') + 1
        image_name = data_point['data']['image'][idx:]

        img_width = data_point['annotations'][0]['result'][0]['original_width']
        img_height = data_point['annotations'][0]['result'][0][
            'original_height']

        bbox_annotations[constants.IMG_SIZE_KEY] = {
            'width': img_width,
            'height': img_height
        }

        bbox_annotations[constants.OCR_NUM_KEY] = []
        bbox_annotations[constants.OCR_UNIT_KEY] = None

        for annotation in data_point['annotations'][0]['result']:

            # Изображение оригинального размера сохраняется для каждой аннотации отдельно.
            # Проверьте, что все они одинаковы
            assert img_width == annotation['original_width'] and \
                    img_height == annotation['original_height']

            single_bbox_dict = {
                k: annotation['value'][k]
                for k in ('x', 'y', 'width', 'height')
            }
            convert_bbox_annotation(single_bbox_dict, img_width, img_height)

            if annotation['value']['rectanglelabels'][
                    0] == constants.OCR_NUM_KEY:
                bbox_annotations[constants.OCR_NUM_KEY].append(
                    single_bbox_dict)

            if annotation['value']['rectanglelabels'][
                    0] == constants.OCR_UNIT_KEY:
                bbox_annotations[constants.OCR_UNIT_KEY] = single_bbox_dict

            if annotation['value']['rectanglelabels'][
                    0] == constants.GAUGE_DET_KEY:
                bbox_annotations[constants.GAUGE_DET_KEY] = single_bbox_dict

        annotation_dict[image_name] = bbox_annotations

    return annotation_dict


# аннотации label-studio всегда имеют масштаб 0,100, поэтому необходимо изменить масштаб
def convert_keypoint_annotation(single_bbox_dict, img_width, img_height):
    single_bbox_dict['x'] *= img_width / 100
    single_bbox_dict['y'] *= img_height / 100


def get_annotations_keypoint(data):
    """
    Функция для извлечения аннотации из формата label-studio
    """

    annotation_dict = {}

    for data_point in data:

        keypoint_annotations = {}
        # Получите имя изображения. У нас есть имя изображения в формате :
        # /data/upload/1/222ae49e-1_cropped_000001_jpg.rf.c7410b0b01b2bc3a6cdff656618a3015.jpg
        # избавьтесь от всего, что находится перед '-'
        idx = data_point['data']['img'].find('-') + 1
        image_name = data_point['data']['img'][idx:]

        img_width = data_point['annotations'][0]['result'][0]['original_width']
        img_height = data_point['annotations'][0]['result'][0][
            'original_height']

        keypoint_annotations[constants.IMG_SIZE_KEY] = {
            'width': img_width,
            'height': img_height
        }

        keypoint_annotations[constants.KEYPOINT_NOTCH_KEY] = []

        for annotation in data_point['annotations'][0]['result']:

            # Изображение оригинального размера сохраняется для каждой аннотации отдельно.
            # Проверьте, что все они одинаковы
            assert img_width == annotation['original_width'] and \
                    img_height == annotation['original_height']

            single_keypoint_dict = {
                k: annotation['value'][k]
                for k in ('x', 'y')
            }
            convert_keypoint_annotation(single_keypoint_dict, img_width,
                                        img_height)
            keypoint_annotations[constants.KEYPOINT_NOTCH_KEY].append(
                single_keypoint_dict)

            if annotation['value']['keypointlabels'][
                    0] == constants.KEYPOINT_START_KEY:
                keypoint_annotations[
                    constants.KEYPOINT_START_KEY] = single_keypoint_dict.copy(
                    )

            if annotation['value']['keypointlabels'][
                    0] == constants.KEYPOINT_END_KEY:
                keypoint_annotations[
                    constants.KEYPOINT_END_KEY] = single_keypoint_dict.copy()

        annotation_dict[image_name] = keypoint_annotations

    return annotation_dict


def polygon_to_mask(polygon, img_shape):
    mask = np.zeros(img_shape)
    cv2.fillPoly(mask, [np.int32(polygon)], 1)
    return mask


def convert_segmenation_annotation(polygon, img_width, img_height):
    for point in polygon:
        point[0] *= img_width / 100
        point[1] *= img_height / 100
    return polygon_to_mask(polygon, (img_height, img_width))


def get_annotations_segmenatation(data):
    """
    Функция для извлечения аннотации из формата label-studio
    """

    annotation_dict = {}

    for data_point in data:

        segmentation_annotation = {}
        # Получите имя изображения. У нас есть имя изображения в формате :
        # /data/upload/1/222ae49e-1_cropped_000001_jpg.rf.c7410b0b01b2bc3a6cdff656618a3015.jpg
        # избавьтесь от всего, что находится перед '-'
        idx = data_point['data']['image'].find('-') + 1
        image_name = data_point['data']['image'][idx:]

        img_width = data_point['annotations'][0]['result'][0]['original_width']
        img_height = data_point['annotations'][0]['result'][0][
            'original_height']

        segmentation_annotation[constants.IMG_SIZE_KEY] = {
            'width': img_width,
            'height': img_height
        }

        segmentation_annotation[constants.NEEDLE_MASK_KEY] = []

        for annotation in data_point['annotations'][0]['result']:

            # Изображение оригинального размера сохраняется для каждой аннотации отдельно.
            # Проверьте, что все они одинаковы
            assert img_width == annotation['original_width'] and \
                    img_height == annotation['original_height']

            segmenation_annotation = annotation['value']['points']
            segmentation_mask = convert_segmenation_annotation(
                segmenation_annotation, img_width, img_height)
            segmentation_annotation[constants.NEEDLE_MASK_KEY].append(
                segmentation_mask)

        annotation_dict[image_name] = segmentation_annotation

    return annotation_dict


def get_annotations_from_json(bbox_path, key_point_path, segmentation_path):
    """
    возвращает дикту аннотаций с именем каждого изображения в качестве ключа.
    Для каждого из них у нас есть еще один dict, с ключом для каждого результата различных этапов.
    """
    with open(bbox_path, 'r') as file:
        bbox_true_dict = json.load(file)
    with open(key_point_path, 'r') as file:
        keypoint_true_dict = json.load(file)
    with open(segmentation_path, 'r') as file:
        seg_true_dict = json.load(file)

    bbox_dict = get_annotations_bbox(bbox_true_dict)
    key_point_dict = get_annotations_keypoint(keypoint_true_dict)
    seg_dict = get_annotations_segmenatation(seg_true_dict)

    assert set(bbox_dict.keys()) == set(key_point_dict.keys())
    assert set(bbox_dict.keys()) == set(seg_dict.keys())

    full_annotations = {}
    for key in bbox_dict:

        bbox_img_width = bbox_dict[key][constants.IMG_SIZE_KEY]['width']
        bbox_img_height = bbox_dict[key][constants.IMG_SIZE_KEY]['height']
        keypoint_img_width = key_point_dict[key][
            constants.IMG_SIZE_KEY]['width']
        keypoint_img_height = key_point_dict[key][
            constants.IMG_SIZE_KEY]['height']
        assert bbox_img_width == keypoint_img_width  and \
                bbox_img_height == keypoint_img_height

        full_annotations[key] = {
            constants.IMG_SIZE_KEY:
            bbox_dict[key][constants.IMG_SIZE_KEY],
            constants.OCR_NUM_KEY:
            bbox_dict[key][constants.OCR_NUM_KEY],
            constants.OCR_UNIT_KEY:
            bbox_dict[key][constants.OCR_UNIT_KEY],
            constants.GAUGE_DET_KEY:
            bbox_dict[key][constants.GAUGE_DET_KEY],
            constants.KEYPOINT_NOTCH_KEY:
            key_point_dict[key][constants.KEYPOINT_NOTCH_KEY],
            constants.KEYPOINT_START_KEY:
            key_point_dict[key][constants.KEYPOINT_START_KEY],
            constants.KEYPOINT_END_KEY:
            key_point_dict[key][constants.KEYPOINT_END_KEY],
            constants.NEEDLE_MASK_KEY:
            seg_dict[key][constants.NEEDLE_MASK_KEY]
        }

    return full_annotations


def write_json(path, dictionary):
    result = json.dumps(dictionary, indent=4)
    with open(path, "w") as outfile:
        outfile.write(result)


def get_predictions(run_path):
    prediction_results = {}

    for subdir in os.listdir(run_path):

        subdirectory = os.path.join(run_path, subdir)
        if os.path.isdir(subdirectory):

            result_file = os.path.join(subdirectory,
                                       constants.RESULT_FULL_FILE_NAME)
            if os.path.isfile(result_file):
                with open(result_file, 'r') as file:
                    result_dict = json.load(file)
                    result_dict[constants.ORIGINAL_IMG_KEY] = os.path.join(
                        subdirectory, constants.ORIGINAL_IMG_FILE_NAME)
                    prediction_results[subdir] = result_dict

            else:
                prediction_results[subdir] = constants.FAILED
                print("Ошибка: Файл предсказаний не найден! \
                        Конвейер потерпел неудачу до того, как предсказание было сделано")

    outfile_path = os.path.join(run_path, "predictions_full_results.json")
    predictions_json = json.dumps(prediction_results, indent=4)
    with open(outfile_path, "w") as outfile:
        outfile.write(predictions_json)

    return prediction_results


def bb_intersection_over_union(boxA, boxB):
    """
    boxA и boxB здесь имеют формат (x,y, width, height)
    адаптированный из
    https://pyimagesearch.com/2016/11/07/intersection-over-union-iou-for-object-detection/
    """
    # координаты области пересечения.
    xA = max(boxA['x'], boxB['x'])
    yA = max(boxA['y'], boxB['y'])
    xB = min(boxA['x'] + boxA['width'], boxB['x'] + boxB['width'])
    yB = min(boxA['y'] + boxA['height'], boxB['y'] + boxB['height'])

    # вычислить площадь прямоугольника пересечения
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

    # вычислите площадь предсказанного и истинного
    # прямоугольники
    boxAArea = (boxA['width'] + 1) * (boxA['height'] + 1)
    boxBArea = (boxB['width'] + 1) * (boxB['height'] + 1)
    # вычислите пересечение над объединением, взяв площадь пересечения
    # площади и разделив ее на сумму предсказания + истины на местности
    # площадей - площадь пересечения
    iou = interArea / float(boxAArea + boxBArea - interArea)
    # возвращает значение пересечения над объединением
    return iou


def compare_gauge_detecions(annotation, prediction, plotter, eval_dict,
                            gauge_iou_list):
    plotter.plot_bounding_box_img([annotation], [prediction],
                                  'обнаружение манометра')
    iou = bb_intersection_over_union(annotation, prediction)
    eval_dict[constants.GAUGE_IOU_KEY] = iou
    gauge_iou_list.append(iou)


def compute_mask_iou(mask1, mask2):
    # преобразование в булевы массивы
    mask1 = mask1.astype(bool)
    mask2 = mask2.astype(bool)

    # Формула для пересечения над объединением
    intersection = np.logical_and(mask1, mask2)
    union = np.logical_or(mask1, mask2)

    iou = np.sum(intersection) / np.sum(union)
    return iou


def create_mask(x_coords, y_coords, shape):
    mask = np.zeros(shape, dtype=np.int32)
    mask[y_coords, x_coords] = 1
    return mask


def compare_needle_segmentations(annotation, prediction, plotter, eval_dict,
                                 needle_list):
    """
    аннотация имеет формат 2d массива numpy с 0,1
    предсказание представляет собой два списка, x_coord_list и y_coord_list
    Сначала преобразуйте предсказания в тот же формат, что и аннотации.
    """
    annotation_mask = annotation[0]

    indices = np.where(annotation_mask == 1)
    ann_x_coords = indices[1].tolist()
    ann_y_coords = indices[0].tolist()

    pred_x_coords = prediction['x']
    pred_y_coords = prediction['y']
    pred_mask = create_mask(pred_x_coords, pred_y_coords,
                            annotation_mask.shape)

    plotter.plot_segmentation_debug(annotation_mask, pred_mask)
    plotter.plot_segmentation((ann_x_coords, ann_y_coords),
                              (pred_x_coords, pred_y_coords))

    iou = compute_mask_iou(annotation_mask, pred_mask)
    eval_dict[constants.NEEDLE_IOU_KEY] = iou
    needle_list.append(iou)


def compare_ocr_numbers(annotation, prediction, plotter, eval_dict, ocr_list):
    plotter.plot_bounding_box_img(annotation, prediction,
                                  'обнаружение масштабных отметок')

    n_ocr_detected = 0
    n_annotations = len(annotation)
    for annotation_bbox in annotation:
        iou_max = 0
        for prediction_bbox in prediction:
            iou = bb_intersection_over_union(annotation_bbox, prediction_bbox)
            iou_max = max(iou, iou_max)
        if iou_max > IOU_THRESHOLD:
            n_ocr_detected += 1
    eval_dict[constants.N_OCR_DETECTED_KEY] = n_ocr_detected
    eval_dict[
        constants.PERCENTAGE_OCR_DETECTED_KEY] = n_ocr_detected / n_annotations
    ocr_list.append(n_ocr_detected / n_annotations)


def compare_notches(annotation_list, prediction_list, plotter, eval_dict,
                    notch_metrics_list):
    # Приведите точки к правильному формату для функции метрики ключевых точек.
    # Для этого нужен двухмерный массив
    annotation = []
    for annotation_dict in annotation_list:
        annotation.append([annotation_dict['x'], annotation_dict['y']])
    predicted = []
    for prediction_dict in prediction_list:
        predicted.append([prediction_dict['x'], prediction_dict['y']])
    annotation = np.array(annotation)
    predicted = np.array(predicted)

    # построение ключевых точек
    plotter.plot_key_points(annotation, predicted, 'отметки')

    metrics_dict = key_point_metrics(predicted, annotation)
    eval_dict[constants.NOTCHES_METRICS_KEY] = metrics_dict
    notch_metrics_list.append([
        metrics_dict[MEAN_DIST_KEY], metrics_dict[PCK_KEY],
        metrics_dict[NON_ASSIGNED_KEY]
    ])


def compare_single_keypoint(annotation, prediction, plotter, eval_dict,
                            is_start, notch_metrics_list):
    """
    Это для оценки начала и конца насечки. if is_start then start, else end
    """

    # Приведите точки к правильному формату для функции метрики ключевых точек.
    # Для этого нужен двухмерный массив
    annotation = np.array([[annotation['x'], annotation['y']]])
    predicted = np.array([[prediction['x'], prediction['y']]])

    metrics_dict = key_point_metrics(predicted, annotation)

    if is_start:
        plotter.plot_key_points(annotation, predicted, 'отметка начала')
        eval_dict[constants.START_METRICS_KEY] = metrics_dict
    else:
        plotter.plot_key_points(annotation, predicted, 'отметка конца')
        eval_dict[constants.END_METRICS_KEY] = metrics_dict

    notch_metrics_list.append([
        metrics_dict[MEAN_DIST_KEY], metrics_dict[PCK_KEY],
        metrics_dict[NON_ASSIGNED_KEY]
    ])


def is_point_inside(point, crop_box):
    return point['x']>crop_box['x'] and point['x']<crop_box['x']+crop_box['width'] \
        and point['y']>crop_box['y'] and point['y']<crop_box['y']+crop_box['height']


def is_bbox_inside(bbox, crop_box):
    point1 = {'x': bbox['x'], 'y': bbox['y']}
    point2 = {'x': bbox['x'] + bbox['width'], 'y': bbox['y'] + bbox['height']}
    return is_point_inside(point1, crop_box) and is_point_inside(
        point2, crop_box)


def rescale_point(point, crop_box, border):
    if is_point_inside(point, crop_box):
        top, bottom, left, right = border

        x_offset = crop_box['x'] - left
        y_offset = crop_box['y'] - top

        box_width = crop_box['width'] + left + right
        box_height = crop_box['height'] + top + bottom
        rescale_resolution = RESOLUTION

        x_shift = point['x'] - x_offset
        y_shift = point['y'] - y_offset

        point['x'] = x_shift * rescale_resolution[0] / box_width
        point['y'] = y_shift * rescale_resolution[1] / box_height
    else:
        print('ТОЧКА ПОМОЩИ НЕ ВНУТРИ КОРОБКИ')


def rescale_bbox(bbox, crop_box, border):
    if is_bbox_inside(bbox, crop_box):
        top, bottom, left, right = border

        x_offset = crop_box['x'] - left
        y_offset = crop_box['y'] - top

        box_width = crop_box['width'] + left + right
        box_height = crop_box['height'] + top + bottom
        rescale_resolution = RESOLUTION

        x_shift = bbox['x'] - x_offset
        y_shift = bbox['y'] - y_offset

        bbox['x'] = x_shift * rescale_resolution[0] / box_width
        bbox['y'] = y_shift * rescale_resolution[1] / box_height
        bbox['width'] *= rescale_resolution[0] / box_width
        bbox['height'] *= rescale_resolution[0] / box_width


def rescale_needle_segmentation(masks, crop_box):
    mask = masks[0]
    mask = crop_image(mask, crop_box, two_dimensional=True)
    mask = cv2.resize(mask, dsize=RESOLUTION, interpolation=cv2.INTER_NEAREST)
    return mask


def main(bbox_path, key_point_path, segmentation_path, run_path):

    annotations_dict = get_annotations_from_json(bbox_path, key_point_path,
                                                 segmentation_path)
    predictions_dict = get_predictions(run_path)

    assert set(predictions_dict.keys()) == set(annotations_dict.keys())

    full_eval_dict = {}

    gauge_iou_list = []
    needle_iou_list = []
    notch_metrics_list = []
    start_notch_metrics_list = []
    end_notch_metrics_list = []
    ocr_detections_list = []

    for image_name in annotations_dict:

        annotation_dict = annotations_dict[image_name]
        prediction_dict = predictions_dict[image_name]

        if prediction_dict == constants.FAILED:
            print("Пропустить неудачное изображение")
            continue

        # получить соответствующее изображение для участков
        image_path = prediction_dict[constants.ORIGINAL_IMG_KEY]
        image = Image.open(image_path).convert("RGB")
        image = np.asarray(image)

        eval_dict = {}

        eval_path = os.path.join(run_path, image_name, "eval")
        os.makedirs(eval_path, exist_ok=True)
        plotter = EvalPlotter(eval_path, image)

        # сравнение обнаружения манометра
        compare_gauge_detecions(annotation_dict[constants.GAUGE_DET_KEY],
                                prediction_dict[constants.GAUGE_DET_KEY],
                                plotter, eval_dict, gauge_iou_list)

        # Обрезка и изменение масштаба изображения
        pred_gauge_bbox = prediction_dict[constants.GAUGE_DET_KEY]
        pred_gauge_bbox_list = [
            pred_gauge_bbox['x'], pred_gauge_bbox['y'],
            pred_gauge_bbox['x'] + pred_gauge_bbox['width'],
            pred_gauge_bbox['y'] + pred_gauge_bbox['height']
        ]
        cropped_img, border = crop_image(image, pred_gauge_bbox_list, True)
        # изменить размер
        cropped_img = cv2.resize(cropped_img,
                                 dsize=RESOLUTION,
                                 interpolation=cv2.INTER_CUBIC)
        plotter.set_image(cropped_img)
        plotter.plot_image('cropped')

        # Обрезка и изменение масштаба всех аннотаций
        for bbox in annotation_dict[constants.OCR_NUM_KEY]:
            rescale_bbox(bbox, pred_gauge_bbox, border)
        if annotation_dict[constants.OCR_UNIT_KEY] is not None:
            rescale_bbox(annotation_dict[constants.OCR_UNIT_KEY],
                         pred_gauge_bbox, border)
        rescale_point(annotation_dict[constants.KEYPOINT_START_KEY],
                      pred_gauge_bbox, border)
        rescale_point(annotation_dict[constants.KEYPOINT_END_KEY],
                      pred_gauge_bbox, border)
        for point in annotation_dict[constants.KEYPOINT_NOTCH_KEY]:
            rescale_point(point, pred_gauge_bbox, border)
        annotation_dict[constants.NEEDLE_MASK_KEY][0] = \
            rescale_needle_segmentation(annotation_dict[constants.NEEDLE_MASK_KEY],
                      pred_gauge_bbox_list)

        # сравните ключевые моменты
        compare_notches(annotation_dict[constants.KEYPOINT_NOTCH_KEY],
                        prediction_dict[constants.KEYPOINT_NOTCH_KEY], plotter,
                        eval_dict, notch_metrics_list)

        compare_single_keypoint(annotation_dict[constants.KEYPOINT_START_KEY],
                                prediction_dict[constants.KEYPOINT_START_KEY],
                                plotter, eval_dict, True,
                                start_notch_metrics_list)

        compare_single_keypoint(annotation_dict[constants.KEYPOINT_END_KEY],
                                prediction_dict[constants.KEYPOINT_END_KEY],
                                plotter, eval_dict, False,
                                end_notch_metrics_list)

        # Сравните распознавание номеров OCR
        if prediction_dict[constants.OCR_NUM_KEY] == constants.FAILED:
            print("Пропустить неудачное сравнение ocr")
            eval_dict[constants.OCR_NUM_KEY] = constants.FAILED
        else:
            compare_ocr_numbers(annotation_dict[constants.OCR_NUM_KEY],
                                prediction_dict[constants.OCR_NUM_KEY],
                                plotter, eval_dict, ocr_detections_list)

        # Сравните обнаружение единиц OCR

        # сравнение сегментов стрелки
        if prediction_dict[constants.NEEDLE_MASK_KEY] == constants.FAILED:
            print("Пропустить неудачное сравнение стрелки")
            eval_dict[constants.NEEDLE_IOU_KEY] = constants.FAILED
        else:
            compare_needle_segmentations(
                annotation_dict[constants.NEEDLE_MASK_KEY],
                prediction_dict[constants.NEEDLE_MASK_KEY], plotter, eval_dict,
                needle_iou_list)

        # можно сравнить подгонку линии и подгонку эллипса

        # Добавьте eval dict в полный
        full_eval_dict[image_name] = eval_dict

        # Сохраните eval_dict в определенную папку с изображением
        outfile_path = os.path.join(eval_path, "evaluation.json")
        write_json(outfile_path, eval_dict)

    # вычислять средние значения
    gauge_iou_avg = np.average(np.array(gauge_iou_list))
    needle_iou_avg = np.average(np.array(needle_iou_list))
    ocr_detections_avg = np.average(np.array(ocr_detections_list))
    notch_metrics_avg = np.average(np.array(notch_metrics_list), axis=0)
    start_notch_metrics_avg = np.average(np.array(start_notch_metrics_list),
                                         axis=0)
    end_notch_metrics_avg = np.average(np.array(end_notch_metrics_list),
                                       axis=0)

    out_dict = {
        constants.GAUGE_IOU_KEY: gauge_iou_avg,
        constants.NOTCHES_METRICS_KEY: {
            MEAN_DIST_KEY: notch_metrics_avg[0],
            PCK_KEY: notch_metrics_avg[1],
            NON_ASSIGNED_KEY: notch_metrics_avg[2]
        },
        constants.START_METRICS_KEY: {
            MEAN_DIST_KEY: start_notch_metrics_avg[0],
            PCK_KEY: start_notch_metrics_avg[1],
            NON_ASSIGNED_KEY: start_notch_metrics_avg[2]
        },
        constants.END_METRICS_KEY: {
            MEAN_DIST_KEY: end_notch_metrics_avg[0],
            PCK_KEY: end_notch_metrics_avg[1],
            NON_ASSIGNED_KEY: end_notch_metrics_avg[2]
        },
        constants.OCR_NUM_KEY: ocr_detections_avg,
        constants.NEEDLE_IOU_KEY: needle_iou_avg,
        "full_eval": full_eval_dict
    }

    # Сохраните полный диктант eval в json
    outfile_path = os.path.join(run_path, "full_evaluation.json")
    write_json(outfile_path, out_dict)


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bbox_true_path',
                        type=str,
                        required=True,
                        help="Путь к json-файлу с метками для bbox")
    parser.add_argument('--keypoint_true_path',
                        type=str,
                        required=True,
                        help="Путь к json-файлу с метками для ключевых точек")
    parser.add_argument('--segmentation_true_path',
                        type=str,
                        required=True,
                        help="Путь к json-файлу с метками для сегментации")
    parser.add_argument('--run_path',
                        type=str,
                        required=True,
                        help="Путь к папке запуска")
    return parser.parse_args()


if __name__ == "__main__":
    args = read_args()
    main(args.bbox_true_path, args.keypoint_true_path,
         args.segmentation_true_path, args.run_path)
