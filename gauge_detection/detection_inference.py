from ultralytics import YOLO


def detection_gauge_face(img, model_path='best.pt'):
    '''
    Использует yolo v8 для получения ограничительной рамки для лица датчика
    :param img: numpy-изображение
    :param model_path: путь к модели обнаружения yolov8
    :return: коробка с наибольшим доверием для дальнейшей обработки и список всех коробок для визуализации
    '''
    model = YOLO(model_path)  # загрузка модели

    results = model(img)  # Выполнение вывода, определения поверхность манометра и стрелку

    # получить список обнаруженных контейнеров, уже отсортированных по степени достоверности
    boxes = results[0].boxes

    if len(boxes) == 0:
        raise Exception("На изображении не обнаружен калибр")

    # Получите наивысший доверительный интервал, который имеет калибровочную грань
    gauge_face_box = boxes[0]

    box_list = []
    for box in boxes:
        box_list.append(box.xyxy[0].int())

    return gauge_face_box.xyxy[0].int(), box_list
