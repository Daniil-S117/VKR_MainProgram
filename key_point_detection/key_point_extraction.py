import numpy as np
from sklearn.cluster import MeanShift, KMeans
from scipy.spatial.distance import cdist

MEAN_DIST_KEY = "среднее расстояние между предсказанным и истинным"
PCK_KEY = "Процент истин, в которых хотя бы одно предсказание является близким"
NON_ASSIGNED_KEY = "Процент не присвоенных прогнозируемых баллов"


def full_key_point_extraction(heatmaps, threshold=0.5, bandwidth=20):
    key_point_list = []
    for i in range(heatmaps.shape[0]):
        # середина
        if i == 1:
            cluster_centers = extract_key_points(heatmaps[i], threshold,
                                                 bandwidth)
            key_point_list.append(cluster_centers)
        # начало и конец
        else:
            cluster_center = extract_start_end_points(heatmaps[i], threshold)
            key_point_list.append(cluster_center)
    return key_point_list


def extract_start_end_points(heatmap, threshold):
    # нормализуйте тепловую карту к диапазону 0, 1
    heatmap = heatmap / np.max(heatmap)

    coords = np.argwhere(heatmap > threshold)
    # поменяйте местами координаты
    coords[:, [1, 0]] = coords[:, [0, 1]]

    kmeans = KMeans(n_clusters=1, n_init=3)
    kmeans.fit(coords)

    cluster_center = kmeans.cluster_centers_

    return cluster_center


def extract_key_points(heatmap, threshold, bandwidth):

    # нормализуйте тепловую карту к диапазону 0, 1
    heatmap = heatmap / np.max(heatmap)

    # Получите координаты пикселей, значение которых больше 0,5
    coords = np.argwhere(heatmap > threshold)
    # поменяйте местами координаты
    coords[:, [1, 0]] = coords[:, [0, 1]]

    # Выполните кластеризацию со средним сдвигом
    ms = MeanShift(bandwidth=bandwidth, n_jobs=-1)
    ms.fit(coords)

    # Результаты сюжетов
    cluster_centers = ms.cluster_centers_

    return cluster_centers


def key_point_metrics(predicted, ground_truth, threshold=10):
    """
    Получает три различные метрики для оценки предсказанных ключевых точек.
    Для mean_distance каждое предсказание присваивается истинной ключевой точке
    с наименьшим расстоянием до нее, а затем эти расстояния усредняются.
    Для p_non_assigned мы имеем процент предсказанных ключевых точек
    которые не близки ни к одной истинной ключевой точке и поэтому не назначены.
    Для pck мы имеем процент истинных ключевых точек,
    в которых хотя бы одна предсказанная ключевая точка близка к ней.

    Как для p_non_assigned, так и для pck,
    близость двух ключевых_точек означает, что их расстояние меньше порога.
    :param predicted:
    :param ground_truth:
    :param threshold:
    :return:
    """
    distances = cdist(predicted, ground_truth)

    cor_pred_indices = np.argmin(
        distances, axis=1)  # показатели истинности, наиболее близкие к предсказаниям
    cor_true_indices = np.argmin(
        distances, axis=0)  # показатели прогнозов, наиболее близких к истине

    # извлеките соответствующие основные моменты истинности
    corresponding_truth = ground_truth[cor_pred_indices]

    # вычислите евклидовы расстояния между предсказанными точками и соответствующими наземными точками
    pred_distances = np.linalg.norm(predicted[:len(corresponding_truth)] -
                                    corresponding_truth,
                                    axis=1)
    mean_distance = np.mean(pred_distances)

    non_assigned = np.sum(pred_distances > threshold)
    p_non_assigned = non_assigned / len(predicted)

    # извлеките соответствующие прогнозируемые точки
    corresponding_pred = predicted[cor_true_indices]

    gt_distances = np.linalg.norm(ground_truth[:len(corresponding_pred)] -
                                  corresponding_pred,
                                  axis=1)
    correct = np.sum(gt_distances <= threshold)
    pck = correct / len(
        ground_truth
    )  # вычислите PCK как процент правильно предсказанных ключевых точек

    results_dict = {
        MEAN_DIST_KEY: mean_distance,
        PCK_KEY: pck,
        NON_ASSIGNED_KEY: p_non_assigned
    }
    return results_dict
