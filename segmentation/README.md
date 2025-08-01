# Определение датчика

Мы используем yolov8 от ultralytics <https://github.com/ultralytics/ultralytics>
для сегментации измерительной иглы.

## Обучение

Установите следующие зависимости для локального обучения, в colab это делается в записной книжке.

### Зависимости:
pytorch 1.13.0+cpu

```shell
conda install pytorch torchvision torchaudio cpuonly -c pytorch
```

ultralytics:
```shell
pip install ultralytics
```

### Установочные данные

Если данные находятся в формате COCO, вы можете использовать следующий репозиторий github для преобразования их в формат YOLO:

Json2Yolo <https://github.com/ultralytics/JSON2YOLO>

Затем, когда у вас будут изображения и надписи, вы можете использовать "filestructure_detection_training.ipynb" для создания правильной структуры данных, описанной ниже.

### Обучение

Теперь вы можете использовать "detection_training_local.py" для локального обучения и "detection_training_colab.ipynb" для обучения на colab.
Обратите внимание, что для обучения на colab я сначала загружаю данные в папку на диске, которую подключаю во время обучения.
Конечно, вы также можете запустить обучение локально.

### Структура папок с данными
Нам нужно, чтобы в папке training (и папке test/val соответственно) было две папки с
одинаковыми именами - images и labels. В ярлыках для каждого изображения должен содержаться текстовый файл с таким же именем.
Файл data.yaml должен выглядеть следующим образом:

    train: data/train/images
    val: data/valid/images

    nc: 1
    names: [Gauge Needle']

Yolov8 ожидает, что ярлыки будут находиться в папке с тем же путем, что и изображения, но просто заменит ярлыки на изображения.
В этом случае структура папок должна выглядеть следующим образом:

    --data
        --detection
            --train
                --images
                --labels
            --val
                --images
                --labels
            --test
                --images
                --labels
            data.yaml
        --segmentation
            --train
                --images
                --labels
            --val
                --images
                --labels
            --test
                --images
                --labels
            data.yaml
