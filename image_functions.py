import io
import os
import logging
import datetime
import re
import numpy as np
import cv2
from PIL import Image
from plots import Plotter
from gauge_detection.detection_inference import detection_gauge_face
from ocr.ocr_inference import ocr, ocr_rotations, ocr_single_rotation, ocr_warp
from key_point_detection.key_point_inference import KeyPointInference, detect_key_points
from geometry.ellipse import fit_ellipse, cart_to_pol, get_line_ellipse_point, \
    get_point_from_angle, get_polar_angle, get_theta_middle
from angle_reading_fit.angle_converter import AngleConverter
from angle_reading_fit.line_fit import line_fit, line_fit_ransac
from segmentation.segmenation_inference import get_start_end_line, segment_gauge_needle, \
    get_fitted_line, cut_off_line

from data_base import insert_record, insert_images
from notification_manager import NotificationManager


OCR_THRESHOLD = 0.8
RESOLUTION = (
    448, 448
)  # что оба размера должны быть кратны 14 для определения ключевых точек

# Несколько параметров, которые нужно установить или снять для процесса
WRAP_AROUND_FIX = True
RANSAC = True

WARP_OCR = True

# если random_rotations true, то повороты случайны.
RANDOM_ROTATIONS = False
ZERO_POINT_ROTATION = True

OCR_ROTATION = RANDOM_ROTATIONS or ZERO_POINT_ROTATION
# убедитесь, что оба измерения кратны 14 для обнаружения ключевых точек

detection_model_path = "models/gauge_detection_model.pt"
key_point_model_path = "models/key_point_model.pt"
segmentation_model_path = "models/segmentation_model.pt"


def process_image(image, debug, eval_mode, image_is_raw=False):
    images_list = []
    angle_number_arr = []
    ocr_numbers = []
    needle_degree = '-'
    result_reading = None
    unit = "Неизвестно"
    blob_images = []
    time_reading = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    date_time = datetime.datetime.fromtimestamp(os.path.getctime(image)).strftime("%d.%m.%Y %H:%M:%S")
    image_name = os.path.basename(image)

    if not image_is_raw:
        NotificationManager.show(f"Обработка изображения по указанному пути {image}")
        logging.info("Обработка изображения по указанному пути %s", image)
        image = Image.open(image).convert("RGB")
        image = np.asarray(image)
    else:
        NotificationManager.show(f"Обработка изображения - {image_name}")
        logging.info("Обработка изображений")

    plotter = Plotter(image)

    if debug:
        plotter.save_img()

    # ------------------Обнаружение манометра-------------------------
    if debug:
        print("-------------------")
        print("Обнаружение Манометра")
    NotificationManager.show(f"Обнаружение манометра - {image_name}")
    logging.info("Обнаружение манометра")
    try:
        box, all_boxes = detection_gauge_face(image, detection_model_path)

        if debug:
            plotter.plot_bounding_box_img(all_boxes)

        # обрезание изображения, чтобы получить только манометр
        cropped_img = crop_image(image, box)

        # изменить размер
        cropped_resized_img = cv2.resize(cropped_img,
                                         dsize=RESOLUTION,
                                         interpolation=cv2.INTER_CUBIC)
        images_list.append(image)
        images_list.append(cropped_resized_img)

        if debug:
            plotter.set_image(cropped_resized_img)
            plotter.plot_image('cropped')
        logging.info("Завершение обнаружение манометра")
    except:
        NotificationManager.show(f"Обнаружение манометра не удалось - {image_name}", False)
        print("Обнаружение манометра не удалось")

    # ------------------Сегментация-------------------------

    if debug:
        print("-------------------")
        print("Сегментация")

    logging.info("Начало сегментации")
    NotificationManager.show(f"Сегментации стрелки - {image_name}")

    try:
        needle_mask_x, needle_mask_y = segment_gauge_needle(
            cropped_resized_img, segmentation_model_path)

        needle_line_coeffs, needle_error = get_fitted_line(needle_mask_x,
                                                           needle_mask_y)
        needle_line_start_x, needle_line_end_x = get_start_end_line(needle_mask_x)
        needle_line_start_y, needle_line_end_y = get_start_end_line(needle_mask_y)

        needle_line_start_x, needle_line_end_x = cut_off_line(
            [needle_line_start_x, needle_line_end_x], needle_line_start_y,
            needle_line_end_y, needle_line_coeffs)

        images_list.append(plotter.plot_segmented_line(needle_mask_x, needle_mask_y,
                                                       (needle_line_start_x, needle_line_end_x),
                                                       needle_line_coeffs))
        needle_degree = plotter.find_degree((needle_line_start_x, needle_line_end_x), needle_line_coeffs)

    except AttributeError:
        logging.error("Сегментация не удалась, стрелка не найдена")
        NotificationManager.show(f"Сегментация не удалась, стрелка не найдена - {image_name}", False)
        print("Сегментация не удалась, стрелка не найдена")

    # #------------------Обнаружение Ключевых Точек-------------------------

    if debug:
        print("-------------------")
        print("Обнаружение ключевых точек")

    logging.info("Начало обнаружения ключевых точек")
    NotificationManager.show(f"Начало обнаружения ключевых точек - {image_name}")
    try:
        key_point_inferencer = KeyPointInference(key_point_model_path)
        heatmaps = key_point_inferencer.predict_heatmaps(cropped_resized_img)
        key_point_list = detect_key_points(heatmaps)

        key_points = key_point_list[1]
        start_point = key_point_list[0]
        end_point = key_point_list[2]

        if debug:
            plotter.plot_heatmaps(heatmaps)
            plotter.plot_key_points(key_point_list)

        logging.info("Завершение обнаружение ключевых точек")
    except:
        NotificationManager.show(f"Обнаружение ключевых точек не удалось - {image_name}", False)
        print("Обнаружение ключевых точек не удалось")

    # ------------------Построение Эллипса-------------------------

    if debug:
        print("-------------------")
        print("Построение Эллипса")

    logging.info("Начало построение эллипса")
    NotificationManager.show(f"Построение эллипса - {image_name}")

    try:
        coeffs = fit_ellipse(key_points[:, 0], key_points[:, 1])
        ellipse_params = cart_to_pol(coeffs)
        images_list.append(plotter.plot_ellipse(key_points, ellipse_params, 'key_points'))
        # вычисление нулевой точки

        # Нахождение нижней точки, чтобы установить там ноль для циклического перехода
        if WRAP_AROUND_FIX and start_point.shape == (1, 2) \
                and end_point.shape == (1, 2):
            theta_start = get_polar_angle(start_point.flatten(), ellipse_params)
            theta_end = get_polar_angle(end_point.flatten(), ellipse_params)
            theta_zero = get_theta_middle(theta_start, theta_end)
        else:
            bottom_middle = np.array((RESOLUTION[0] / 2, RESOLUTION[1]))
            theta_zero = get_polar_angle(bottom_middle, ellipse_params)

        zero_point = get_point_from_angle(theta_zero, ellipse_params)

        if debug:
            plotter.plot_zero_point_ellipse(np.array(zero_point),
                                            np.vstack((start_point, end_point)),
                                            ellipse_params)
    except:
        logging.error("Параметры эллипса не являются эллипсом")
        NotificationManager.show(f"Параметры эллипса не являются эллипсом - {image_name}", False)

    logging.info("Завершение подгонки эллипса")

    # ------------------Оптическое распознавание символов-------------------------

    # Важная деталь: мы выполняем распознавание на обрезанном, неизмененном изображении,
    # чтобы не ограничивать разрешение распознавания.

    if debug:
        print("-------------------")
        print("Оптическое распознавание символов")

    logging.info("Начало OCR")
    NotificationManager.show(f"Оптическое распознавание символов - {image_name}")

    cropped_img_resolution = (cropped_img.shape[1], cropped_img.shape[0])

    try:
        if RANDOM_ROTATIONS:
            ocr_readings, ocr_visualization, degree = ocr_rotations(
                cropped_img, plotter, debug)
            logging.info("Повернуть изображение на %s градусов", degree)

        elif WARP_OCR:
            # изменить размер нулевой точки и центра эллипса до исходного разрешения
            res_zero_point = list(
                move_point_resize(zero_point, RESOLUTION, cropped_img_resolution))
            res_ellipse_params = rescale_ellipse_resize(ellipse_params, RESOLUTION,
                                                        cropped_img_resolution)
            # Здесь мы используем вращение вокруг нулевой точки.
            if OCR_ROTATION:
                ocr_readings, ocr_visualization, degree = ocr_warp(
                    cropped_img, res_zero_point, res_ellipse_params, plotter,
                    debug, RANDOM_ROTATIONS, ZERO_POINT_ROTATION)
                logging.info("Повернуть изображение на %s градусов", degree)

            else:
                # pylint: disable-next=unbalanced-tuple-unpacking
                ocr_readings, ocr_visualization = ocr_warp(
                    cropped_img, res_zero_point, res_ellipse_params, plotter,
                    debug, RANDOM_ROTATIONS, ZERO_POINT_ROTATION)
        elif ZERO_POINT_ROTATION:
            # изменить размер нулевой точки и центра эллипса до исходного разрешения
            ellipse_x = ellipse_params[0] * cropped_img.shape[1] / RESOLUTION[1]
            ellipse_y = ellipse_params[1] * cropped_img.shape[0] / RESOLUTION[0]
            zero_point_x = zero_point[0] * cropped_img.shape[1] / RESOLUTION[1]
            zero_point_y = zero_point[1] * cropped_img.shape[0] / RESOLUTION[0]

            ocr_readings, ocr_visualization, degree = ocr_single_rotation(
                cropped_img, (zero_point_x, zero_point_y), (ellipse_x, ellipse_y),
                plotter, debug)
            logging.info("Повернуть изображение на %s градусов", degree)

        else:
            if debug:
                ocr_readings, ocr_visualization = ocr(cropped_img, debug)
            else:
                ocr_readings = ocr(cropped_img, debug)

        # изменить размер обнаруженного ocr до нашего измененного изображения.
        for reading in ocr_readings:
            polygon = reading.polygon
            polygon[:, 0] = polygon[:, 0] * RESOLUTION[1] / cropped_img.shape[1]
            polygon[:, 1] = polygon[:, 1] * RESOLUTION[0] / cropped_img.shape[0]
            reading.set_polygon(polygon)
            reading.reading = extract_numbers(reading.reading)

        plotter.plot_ocr_visualization(ocr_visualization)
        images_list.append(plotter.plot_ocr(ocr_readings, title='полный'))

        # нахождение единицы измерения из обнаруженных показаний.
        unit_readings = []
        for reading in ocr_readings:
            if reading.is_unit():
                unit_readings.append(reading)

        if len(unit_readings) == 0:
            unit = "Неизвестно"
        elif len(unit_readings) == 1:
            unit = unit_readings[0].reading

        # если обнаружено несколько показаний, добавление список этих показаний.
        else:
            unit = None

        # получить список показаний OCR, которые являются числами
        number_labels = []
        for reading in ocr_readings:
            if reading.is_number() and reading.confidence > OCR_THRESHOLD:
                # Add heuristics to filter out serial numbers
                if not (abs(reading.number) > 10000 or
                        (abs(reading.number) > 100 and reading.number % 10 != 0)):
                    number_labels.append(reading)

        # Добавить эвристику для фильтрации серийных номеров
        mean_number_ocr_conf = 0
        for number_label in number_labels:
            mean_number_ocr_conf += number_label.confidence / len(number_labels)

        # сохранить результаты OCR для полной оценки
        if eval_mode:
            ocr_bbox_list = []
            for number_label in number_labels:
                box = number_label.get_bounding_box()
                ocr_bbox_list.append({
                    'x': box[0],
                    'y': box[1],
                    'width': box[2] - box[0],
                    'height': box[3] - box[1],
                })

        if debug:
            plotter.plot_ocr(number_labels, title='номера')
            plotter.plot_ocr(unit_readings, title='единица измерения')
    except UnboundLocalError:
        print("OCR не удалось")
        NotificationManager.show(f"OCR не удалось - {image_name}", False)

    logging.info("Конец OCR")

    # ------------------Проецирование OCR-чисел на эллипс-------------------------

    if debug:
        print("-------------------")
        print("Проецирование")

    logging.info("Проекция на эллипс")
    NotificationManager.show(f"Проекция на эллипс - {image_name}")
    try:
        if len(number_labels) == 0:
            print("Не нашел ни одного номера с помощью ocr")
            logging.error("Не нашел ни одного номера с помощью ocr")
        if len(number_labels) == 1:
            logging.warning("Найдено только 1 число с ocr")

        for number in number_labels:
            theta = get_polar_angle(number.center, ellipse_params)
            number.set_theta(theta)

        if debug:
            plotter.plot_project_points_ellipse(number_labels, ellipse_params)

        # ------------------Проекция стрелки на эллипс-------------------------

        point_needle_ellipse = get_line_ellipse_point(
            needle_line_coeffs, (needle_line_start_x, needle_line_end_x),
            ellipse_params)

        if point_needle_ellipse.shape[0] == 0:
            logging.error("Линия стрелки и эллипс не пересекаются!")
            print("Линия стрелки и эллипс не пересекаются!")

        if debug:
            plotter.plot_ellipse(point_needle_ellipse.reshape(1, 2),
                                 ellipse_params, 'needle_point')

    except:
        print("Проецирование не удалось")
        NotificationManager.show(f"Проецирование не удалось - {image_name}", False)

    # ------------------Построение линии к углам и получение показания стрелки-------------------------
    try:
        # Найти угол стрелки на эллипса
        needle_angle = get_polar_angle(point_needle_ellipse, ellipse_params)

        angle_converter = AngleConverter(theta_zero)

        angle_number_list = []
        for number in number_labels:
            angle_number_list.append(
                (angle_converter.convert_angle(number.theta), number.number))

        angle_number_arr = np.array(angle_number_list)

        if RANSAC:
            reading_line_coeff, inlier_mask, outlier_mask = line_fit_ransac(
                angle_number_arr[:, 0], angle_number_arr[:, 1])
        else:
            reading_line_coeff = line_fit(angle_number_arr[:, 0],
                                          angle_number_arr[:, 1])

        reading_line = np.poly1d(reading_line_coeff)
        needle_angle_conv = angle_converter.convert_angle(needle_angle)
        result_reading = reading_line(needle_angle_conv)

        if debug:
            if RANSAC:
                plotter.plot_linear_fit_ransac(angle_number_arr,
                                               (needle_angle_conv, result_reading),
                                               reading_line, inlier_mask,
                                               outlier_mask)
            else:
                plotter.plot_linear_fit(angle_number_arr,
                                        (needle_angle_conv, result_reading), reading_line)

        print(f"Окончательные показания: {round(result_reading, 3)} {unit}")
        NotificationManager.show(f"Окончательные показания: {round(result_reading, 3)} {unit} - {image_name}")
        images_list.append(plotter.plot_final_reading_ellipse([], point_needle_ellipse,
                                                              round(result_reading, 2), ellipse_params))
    except:
        print("Ошибка на этапе")
        NotificationManager.show(f"Ошибка на этапе - {image_name}", False)

    # ------------------Записать результатов в базу данных-------------------------
    try:
        result_reading = round(result_reading, 3)
        for number in angle_number_arr:
            ocr_numbers.append(number[1])
        if 0 not in ocr_numbers and len(ocr_numbers) != 0:
            ocr_numbers.append(0)
        ocr_numbers.sort()
        if result_reading < min(ocr_numbers) or result_reading < min(ocr_numbers) + 0.1:
            status = "Отключён / Не под давлением"
        elif result_reading > max(ocr_numbers):
            status = "Аварийное давление / Перегрузка"
        else:
            status = "Норма / Рабочее давление"
        final_reading = f"{round(result_reading, 1)} {unit}"
    except:
        status = "Ошибка"
        final_reading = "Неизвестно"

    for i in range(len(images_list)):
        blob_images.append(numpy_to_blob(images_list[i]))
    results = [status, final_reading, time_reading, "", result_reading, unit, needle_degree, ocr_numbers,
               image_name, f"{image.shape[1]}x{image.shape[0]}", date_time]
    insert_record(results)
    insert_images(image_name, time_reading, blob_images)
    return results, images_list


def numpy_to_blob(arr: np.ndarray) -> bytes:
    with io.BytesIO() as buffer:
        np.save(buffer, arr)
        return buffer.getvalue()


def crop_image(img, box, flag=False, two_dimensional=False):
    """
    Обрезание изображения
    :param img: оригинальное изображение
    :param box: в формате xyxy
    :return: обрезанное изображение
    """
    img = np.copy(img)
    if two_dimensional:
        cropped_img = img[box[1]:box[3],
                      box[0]:box[2]]  # image has format [y, x]
    else:
        cropped_img = img[box[1]:box[3],
                      box[0]:box[2], :]  # image has format [y, x, rgb]

    height = int(box[3] - box[1])
    width = int(box[2] - box[0])

    # сохранение пропорций, но делает изображение квадратным
    if height > width:
        delta = height - width
        left, right = delta // 2, delta - (delta // 2)
        top = bottom = 0
    else:
        delta = width - height
        top, bottom = delta // 2, delta - (delta // 2)
        left = right = 0

    pad_color = [0, 0, 0]
    new_img = cv2.copyMakeBorder(cropped_img,
                                 top,
                                 bottom,
                                 left,
                                 right,
                                 cv2.BORDER_CONSTANT,
                                 value=pad_color)

    if flag:
        return new_img, (top, bottom, left, right)
    return new_img


def move_point_resize(point, original_resolution, resized_resolution):
    new_point_x = point[0] * resized_resolution[0] / original_resolution[0]
    new_point_y = point[1] * resized_resolution[1] / original_resolution[1]
    return new_point_x, new_point_y


# здесь предполагается, что оба разрешения квадратные
def rescale_ellipse_resize(ellipse_params, original_resolution,
                           resized_resolution):
    x0, y0, ap, bp, phi = ellipse_params

    # перемещение цента эллипса
    x0_new, y0_new = move_point_resize((x0, y0), original_resolution,
                                       resized_resolution)

    # изменить масштаб оси
    scaling_factor = resized_resolution[0] / original_resolution[0]
    ap_x_new = scaling_factor * ap
    bp_x_new = scaling_factor * bp

    return x0_new, y0_new, ap_x_new, bp_x_new, phi


def extract_numbers(reading):
    if any(char.isdigit() for char in reading):
        """
        Извлекает все числа из строки, заменяя запятые на точки.
        Удаляет всё остальное.
    
        :param text: строка с текстом и числами
        :return: список чисел в строковом виде (десятичные через точку)
        """
        # Заменить запятые на точки
        normalized = reading.replace(',', '.')

        # Найти все числа: целые или десятичные
        reading = ' '.join(re.findall(r'-?\d+\.?\d*', normalized))
    return reading
