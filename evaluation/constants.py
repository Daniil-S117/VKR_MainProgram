# Название файла---------------------------------------------------------
RESULT_FILE_NAME = "result.json"
RESULT_FULL_FILE_NAME = "result_full.json"
ERROR_FILE_NAME = "error.json"

ORIGINAL_IMG_FILE_NAME = "original_image.jpg"

# Ключи в файлах Json-------------------------------------------------
READING_KEY = "показания"
RANGE_KEY = "диапазон"
MEASURE_UNIT_KEY = "единицы измерения"

OCR_NONE_DETECTED_KEY = "Нет считываний OCR с номера"
OCR_ONLY_ONE_DETECTED_KEY = "Найдено только 1 число с ocr"
NOT_AN_ELLIPSE_ERROR_KEY = "Ошибка, эллипс имеет неверные параметры"
SEGMENTATION_FAILED_KEY = "Сегментация не удалась"
NEEDLE_ELLIPSE_NO_INTERSECT = "Линия стрелки и эллипс не пересекаются"

IMG_SIZE_KEY = "размер изображения"
OCR_NUM_KEY = "OCR Числа"
OCR_UNIT_KEY = "OCR Единицы измерения"
NEEDLE_MASK_KEY = "Маска для сегментации иглы"
GAUGE_DET_KEY = "Прибор"
KEYPOINT_START_KEY = "Начальная отметка"
KEYPOINT_END_KEY = "Конечная отметка"
KEYPOINT_NOTCH_KEY = "Ключевая точка Отметки"
ORIGINAL_IMG_KEY = "оригинальное изображение"

OCR_ROTATION_KEY = "Поворот изображений на столько градусов для OCR"

PRED = 'предсказание'
TRUTH = 'истинное_чтение'
ABS_ERROR = 'суммарная абсолютная погрешность'
REL_ERROR = 'суммарная относительная погрешность'
N_FAILED = 'количество неудачных прогнозов'
N_FAILED_OCR = 'количество неудачных OCR, обнаружено менее 2 номеров'
N_FAILED_NO_ELLIPSE = 'количество примеров, в которых эллипс имеет неверные параметры'
N_FAILED_SEG = 'множество примеров, когда сегментация стрелки не удалась'
N_FAILED_ELLIPSE_LINE_NO_INTERSECT = 'количество примеров, эллипс и линия стрелки не пересекаются'

GAUGE_IOU_KEY = 'IoU обнаружения и установления истины'
N_OCR_DETECTED_KEY = 'N аннотированный bbox из OCR имеет IoU не менее 0,5 с предсказанным'
PERCENTAGE_OCR_DETECTED_KEY = 'Процент обнаруженных номеров OCR'
NOTCHES_METRICS_KEY = 'метрики для обнаружения вырезов'
START_METRICS_KEY = 'метрики для обнаружения стартовых надрезов'
END_METRICS_KEY = 'метрики для обнаружения концевых надрезов'
NEEDLE_IOU_KEY = 'IoU сегментации стрелки'

# Другие константы-------------------------------------------------------
FAILED = 'Ошибка'

NOT_FOUND = 'не обнаружено'
MULTIPLE_FOUND = 'множество обнаружений'

UNIT_LIST = ["bar", "mbar", "millibars", "MPa", "psi", "C", "°C", "F", "°F", "%", "кПа", "CICM", "МПА", "KPA"]
