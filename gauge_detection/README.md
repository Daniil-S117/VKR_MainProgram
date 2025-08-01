# Обнаружение манометра

Мы используем yolov8 из ultralytics <https://github.com/ultralytics/ultralytics>
для обнаружения и сегментации торца манометра и иглы манометра.

## Обучение

Установите следующие зависимости для локального обучения, на colab это делается в блокноте.

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

Если данные находятся в формате COCO, вы можете использовать следующий githup-репозиторий для преобразования их в формат YOLO:

Json2Yolo <https://github.com/ultralytics/JSON2YOLO>.

Затем, когда у вас есть изображения и метки, вы можете использовать «filestructure_detection_training.ipynb» для создания правильной структуры данных, как описано ниже.

### Обучение

Теперь вы можете использовать «detection_training_local.py» для локального обучения и «detection_training_colab.ipynb» для обучения на colab.
Обратите внимание, что для обучения на colab я сначала загружаю данные в папку на диске, которую монтирую во время обучения.
Конечно, вы также можете запустить обучение локально.

### Структура папок с данными
Нам нужно, чтобы в папке training (и папке test/val соответственно) было две папки с названиями
labels должна содержать для каждого изображения одноименный файл .txt.
Файл data.yaml должен выглядеть следующим образом:

    train: data/train/images
    val: data/valid/images

    nc: 1
    names: ['Gauge Face']

Yolov8 ожидает, что метки будут находиться в папке с тем же путем, что и изображения, но просто замените метки на изображения.
Тогда структура папки должна выглядеть следующим образом:

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
