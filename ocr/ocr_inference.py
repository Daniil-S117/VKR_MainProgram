import math
import os
import sys

import numpy as np
import cv2
from mmocr.apis import MMOCRInferencer

# Добавление пути родительского каталога к системе, чтобы правильно импортировать все модули.
parent_dir = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
sys.path.append(parent_dir)

# pylint: disable=wrong-import-position
from ocr.ocr_reading import OCRReading
from geometry.warp_ellipse import warp_ellipse_to_circle, map_point_original_image, \
    map_point_transformed_image


def ocr(img, visualize=True):
    """
    Обнаружение и распознавание символов на изображении
    :param img: numpy img для выполнения ocr
    :param visualize: bool if для возврата изображения с визуализацией в results dict
    :return: ocr_results_dict с двумя ключами: 'predictions' то, что нас интересует
    и 'visualization' изображение для отладки/понимания.
    """
    ocr_model = MMOCRInferencer(det='DB_r50', rec='SAR')

    readings = []

    # MMOCR, похоже, выбрасывает ошибку, если текст не обнаружен
    try:
        results = ocr_model(img, return_vis=visualize)

        visualization = results['visualization'][0]

        polygons = results['predictions'][0]['det_polygons']

        shapes = []
        for coord_list in polygons:
            shape_array = np.array(coord_list)
            shape_array = shape_array.reshape(-1, 2)
            shapes.append(shape_array)

        scores = results['predictions'][0]['rec_scores']
        texts = results['predictions'][0]['rec_texts']

        assert len(scores) == len(texts) and len(scores) == len(shapes)

        for index, score in enumerate(scores):
            reading = OCRReading(shapes[index], texts[index], score)
            readings.append(reading)

    except IndexError:
        print("ничего не обнаружено")

    if visualize:
        return readings, visualization

    return readings


def ocr_warp(image, zero_point, ellipse_params, plotter, debug, multiple_rot,
             zero_point_rot):
    x0, y0, ap, bp, phi = ellipse_params

    ellipse_center = [x0, y0]

    # Отменить следующую строку, чтобы проверить, правильно ли изменен размер эллипса
    # plotter.plot_just_ellipse(image, ellipse_params, "resize")

    # исказить изображение
    warp_image, transformation_matrix = warp_ellipse_to_circle(
        image, ellipse_center, [ap, bp], phi)

    plotter.plot_any_image(warp_image, "warped")

    # Переместить центр эллипса и нулевую точку на деформированное изображение
    warped_ellipse_center = map_point_transformed_image(
        ellipse_center, transformation_matrix)
    warped_zero_point = map_point_transformed_image(zero_point,
                                                    transformation_matrix)

    # прогон через систему обнаружения ocr с вращением
    if multiple_rot:
        ocr_readings, ocr_visualization, rot_angle = ocr_rotations(
            warp_image, plotter, debug)
    elif zero_point_rot:
        ocr_readings, ocr_visualization, rot_angle = ocr_single_rotation(
            warp_image, warped_zero_point, warped_ellipse_center, plotter,
            debug)
    else:
        ocr_readings, ocr_visualization = ocr(warp_image, visualize=True)

    # пересчет показаний OCR с искаженного изображения на оригинальное
    for ocr_reading in ocr_readings:
        polygon = ocr_reading.polygon
        new_polygon = []
        for idx in range(len(polygon)):
            warped_point = polygon[idx, :]
            original_point = map_point_original_image(warped_point,
                                                      transformation_matrix)
            new_polygon.append(original_point.tolist())
        ocr_reading.set_polygon(np.array(new_polygon))

    if zero_point_rot or multiple_rot:
        return ocr_readings, ocr_visualization, rot_angle
    return ocr_readings, ocr_visualization


def ocr_rotations(img, plotter, debug):
    degree_list = [0, 45, 90, 135, 180, 225, 270, 315]

    max_conf = -1
    max_num_of_numericals = -1
    max_unit_detected = False

    # попробовать разные варианты вращения.
    for degree in degree_list:
        rot_img = rotate(img, degree)
        ocr_readings, ocr_visualization = ocr(rot_img, visualize=True)
        if debug:
            plotter.plot_ocr_visualization(ocr_visualization, degree)

        number_of_numericals = 0
        cumulative_confidence = 0
        unit_detected = False
        for ocr_reading in ocr_readings:
            # учитываются только показания с высокой степенью достоверности
            if ocr_reading.confidence > 0.5:
                cumulative_confidence += ocr_reading.confidence
                if ocr_reading.is_number():
                    number_of_numericals += 1
            if ocr_reading.is_unit():
                unit_detected = True

        # Выбор вращения с наибольшим количеством распознанных числительных.
        # В случае ничьей выбирайте ту, которая распознает единицу.
        # Если ни один из них или оба не распознают, выберите тот, который вызывает наибольшее доверие.
        # pylint: отключить следующий = слишком много булевых выражений
        if (number_of_numericals > max_num_of_numericals
                or (number_of_numericals == max_num_of_numericals
                    and unit_detected and not max_unit_detected)
                or (number_of_numericals == max_num_of_numericals
                    and max_unit_detected == unit_detected
                    and cumulative_confidence > max_conf)):
            max_unit_detected = unit_detected
            max_num_of_numericals = number_of_numericals
            max_conf = cumulative_confidence
            best_ocr_readings = ocr_readings
            best_ocr_visualization = ocr_visualization
            best_degree = degree
            best_rot_img = rot_img

    # Поворот многоугольника, считанных с помощью OCR, обратно к невращающемуся изображению. Поворот каждой точки по
    # отдельности
    height, width = best_rot_img.shape[:2]
    for ocr_reading in best_ocr_readings:
        polygon = ocr_reading.polygon
        new_polygon = []
        for idx in range(len(polygon)):
            point = polygon[idx, :]
            x_rot, y_rot = rotate_point(point[0], point[1], width, height,
                                        best_degree)
            new_polygon.append([x_rot, y_rot])
        ocr_reading.set_polygon(np.array(new_polygon))

    return best_ocr_readings, best_ocr_visualization, best_degree


def ocr_single_rotation(img, zero_point, ellipse_center, plotter, debug):
    # поворот
    desired_angle = 90

    zero_x = zero_point[0]
    zero_y = zero_point[1]
    center_x = ellipse_center[0]
    center_y = ellipse_center[1]

    if debug:
        plotter.plot_point_img(
            img, np.array([[zero_x, zero_y], [center_x, center_y]]),
            "non_rotated_zero_point")

    angle_deg = math.degrees(math.atan2(zero_y - center_y, zero_x - center_x))

    rot_angle = angle_deg - desired_angle
    rot_img = rotate_around_point(img, rot_angle, center_x, center_y)

    rot_zero_x, rot_zero_y = rotate_point_around_center(
        zero_x, zero_y, center_x, center_y, -rot_angle)

    if debug:
        plotter.plot_point_img(
            rot_img, np.array([[rot_zero_x, rot_zero_y],
                               [center_x, center_y]]), "rotated_zero_point")

    ocr_readings, ocr_visualization = ocr(rot_img, visualize=True)

    # Поворот многоугольников, считанных с помощью OCR, обратно к невращающемуся изображению. Поворот каждой точки
    # по отдельности
    for ocr_reading in ocr_readings:
        polygon = ocr_reading.polygon
        new_polygon = []
        for idx in range(len(polygon)):
            point = polygon[idx, :]
            x_rot, y_rot = rotate_point_around_center(point[0], point[1],
                                                      center_x, center_y,
                                                      rot_angle)
            new_polygon.append([x_rot, y_rot])
        ocr_reading.set_polygon(np.array(new_polygon))

    return ocr_readings, ocr_visualization, rot_angle


def rotate(image, angle):
    height, width = image.shape[:2]
    return rotate_around_point(image, angle, width / 2, height / 2)


def rotate_around_point(image, angle, x, y):
    img_width = image.shape[1]
    img_height = image.shape[0]
    rotation_matrix = cv2.getRotationMatrix2D((x, y), angle, 1)
    rotated_image = cv2.warpAffine(image, rotation_matrix,
                                   (img_width, img_height))
    return rotated_image


def rotate_point_around_center(x, y, center_x, center_y, rotation_angle):
    # Переведите точку
    translated_x = x - center_x
    translated_y = y - center_y

    # Повернуть точку
    theta = math.radians(rotation_angle)
    rotated_x = translated_x * math.cos(theta) - translated_y * math.sin(theta)
    rotated_y = translated_x * math.sin(theta) + translated_y * math.cos(theta)

    # Переведите точку обратно
    x_rotated = rotated_x + center_x
    y_rotated = rotated_y + center_y

    return x_rotated, y_rotated


def rotate_point(x, y, image_width, image_height, rotation_angle):
    return rotate_point_around_center(x, y, image_width / 2, image_height / 2,
                                      rotation_angle)
