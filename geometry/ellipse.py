import numpy as np

# Здесь код для fit_ellipse, cart_to_pol и get_ellipse взят из следующей записи блога:
# https://scipython.com/blog/direct-linear-least-squares-fitting-of-an-ellipse/
# Как описано в блоге, здесь реализована численно стабильная версия
# подгонки эллипса, описанная здесь https://autotrace.sourceforge.net/WSCG98.pdf

# -------------Подгонка эллипса к точкам ---------------


def fit_ellipse(x, y):
    """

    Подставьте коэффициенты a,b,c,d,e,f, представляющие собой эллипс, описываемый
    формулой F(x,y) = ax^2 + bxy + cy^2 + dx + ey + f = 0 к предоставленным
    массивам точек данных x=[x1, x2, ..., xn] и y=[y1, y2, ..., yn].

    На основе алгоритма Халира и Флюссера «Численно устойчивое прямое
    Численно стабильная прямая подгонка эллипсов по методу наименьших квадратов».


    """

    D1 = np.vstack([x**2, x * y, y**2]).T
    D2 = np.vstack([x, y, np.ones(len(x))]).T
    S1 = D1.T @ D1
    S2 = D1.T @ D2
    S3 = D2.T @ D2
    T = -np.linalg.inv(S3) @ S2.T
    M = S1 + S2 @ T
    C = np.array(((0, 0, 2), (0, -1, 0), (2, 0, 0)), dtype=float)
    M = np.linalg.inv(C) @ M
    # pylint: disable=unused-variable
    eigval, eigvec = np.linalg.eig(M)
    con = 4 * eigvec[0] * eigvec[2] - eigvec[1]**2
    ak = eigvec[:, np.nonzero(con > 0)[0]]
    return np.concatenate((ak, T @ ak)).ravel()


def cart_to_pol(coeffs):
    """

    Преобразуйте коэффициенты конической системы (a, b, c, d, e, f) в параметры эллипса
    параметры эллипса, где F(x, y) = ax^2 + bxy + cy^2 + dx + ey + f = 0.
    Возвращаемые параметры: x0, y0, ap, bp, e, phi, где (x0, y0) - это
    центр эллипса; (ap, bp) - полубольшая и полуминимальная оси,
    соответственно; e - эксцентриситет; phi - поворот полубольшой оси
    главной оси относительно оси x.

    """

    # Мы используем формулы из https://mathworld.wolfram.com/Ellipse.html
    # в которых предполагается картезианская форма ax^2 + 2bxy + cy^2 + 2dx + 2fy + g = 0.
    # Поэтому переименуйте и масштабируйте b, d и f соответствующим образом.
    a = coeffs[0]
    b = coeffs[1] / 2
    c = coeffs[2]
    d = coeffs[3] / 2
    f = coeffs[4] / 2
    g = coeffs[5]

    den = b**2 - a * c
    if den > 0:
        raise ValueError('коэффициенты не представляют эллипс: b^2 - 4ac должен'
                         ' быть отрицательным!')

    # Расположение центра эллипса.
    x0, y0 = (c * d - b * f) / den, (a * f - b * d) / den

    num = 2 * (a * f**2 + c * d**2 + g * b**2 - 2 * b * d * f - a * c * g)
    fac = np.sqrt((a - c)**2 + 4 * b**2)
    # Длина полумажорной и полуминорной осей (они не сортируются).
    ap = np.sqrt(num / den / (fac - a - c))
    bp = np.sqrt(num / den / (-fac - a - c))

    # Отсортируйте длины полумажорной и полуминорной осей, но сохраните
    # исходные относительные величины ширины и высоты.
    width_gt_height = True
    if ap < bp:
        width_gt_height = False
        ap, bp = bp, ap

    # Эксцентриситет.
    r = (bp / ap)**2
    if r > 1:
        r = 1 / r

    # Угол поворота главной оси против часовой стрелки относительно оси x.
    if b == 0:
        phi = 0 if a < c else np.pi / 2
    else:
        phi = np.arctan((2. * b) / (a - c)) / 2
        if a > c:
            phi += np.pi / 2
    if not width_gt_height:
        # Убедитесь, что phi - это угол поворота к полуглавной оси.
        phi += np.pi / 2
    phi = phi % np.pi

    return x0, y0, ap, bp, phi


def get_ellipse_pts(params, npts=100, tmin=0, tmax=2 * np.pi):
    """
    Возвращает npts точек на эллипсе, описываемом параметрами = x0, y0, ap,
    bp, e, phi для значений параметрической переменной t между tmin и tmax.

    """

    x0, y0, ap, bp, phi = params
    # Сетка параметрической переменной t.
    t = np.linspace(tmin, tmax, npts)
    x = x0 + ap * np.cos(t) * np.cos(phi) - bp * np.sin(t) * np.sin(phi)
    y = y0 + ap * np.cos(t) * np.sin(phi) + bp * np.sin(t) * np.cos(phi)
    return x, y


# ------------------Проектирование точки в эллипс-----------------------------


def get_polar_angle(point, ellipse_params):
    """Возвращает углы в диапазоне [0, 2*pi)"""
    theta = _get_polar_angle(point, ellipse_params)
    if theta < 0:
        theta = 2 * np.pi + theta
    return theta


def _get_polar_angle(point, ellipse_params):
    """
    Формула взята с сайта
    https://www.petercollingridge.co.uk/tutorials/computational-geometry/finding-angle-around-ellipse/
    Важно: здесь вычисляется не фактический угол
    а тэта в параметризации x = a*cos(тэта), y=b*sin(тэта).
    Смотрите ссылку, если хотите получить фактический угол.
    Возвращает углы в диапазоне [-pi, pi].
    """
    x0, y0, ap, bp, phi = ellipse_params

    # сдвиг точки и эллипса к началу координат
    x_shift = point[0] - x0
    y_shift = point[1] - y0
    point_shift = np.array([x_shift, y_shift])

    # поверните точку и эллипс, чтобы совместить их с осями x и y
    R = np.array([[np.cos(-phi), -np.sin(-phi)], [np.sin(-phi), np.cos(-phi)]])
    point_rotate = R @ point_shift
    x_rotate = point_rotate[0]
    y_rotate = point_rotate[1]

    # найти угол
    theta = np.arctan2(ap * y_rotate, bp * x_rotate)

    return theta


def get_point_from_angle(theta, ellipse_params):
    x0, y0, ap, bp, phi = ellipse_params

    x_p = ap * np.cos(theta)
    y_p = bp * np.sin(theta)
    projected_point = np.array([x_p, y_p])

    # вращаться назад
    R_inv = np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])
    rot_p = R_inv @ projected_point

    # сдвиг назад
    x_proj = rot_p[0] + x0
    y_proj = rot_p[1] + y0

    return x_proj, y_proj


def project_point(point, ellipse_params):
    theta = _get_polar_angle(point, ellipse_params)
    return get_point_from_angle(theta, ellipse_params)


# --------------------Получить ошибку эллипса------------------------------


def get_ellipse_error(points, ellipse_params):
    mean_dist = 0
    n_points = len(points)
    for point in points:
        proj_point = project_point(point, ellipse_params)
        distance = np.linalg.norm(proj_point - point)
        mean_dist += distance / n_points
    return mean_dist


# --------------------Пересечение прямой и эллипса------------------------------


def get_line_ellipse_point(line_coeffs, x, ellipse_params):
    """
    В большинстве случаев у вас есть две точки пересечения.
    Возьмите точку пересечения, которая имеет наименьшее расстояние до начальной
    или конечной точки иглы
    :param line_coeffs:
    :param x: x координаты конечной и начальной точки линии
    :param ellipse_params:
    :return: массив numpy с координатами x и y
    """
    intersection_points = find_line_ellipse_intersection(
        line_coeffs, x, ellipse_params)

    if intersection_points.shape[0] == 2:
        # Проверьте, есть ли на линии ровно одна точка пересечения.
        # Если да, выберите ее, если нет - выберите ближайшую к любой из конечных точек.
        if _inbetween(x[0], x[1], intersection_points[0][0]) and \
            not _inbetween(x[0], x[1], intersection_points[1][0]) :
            return intersection_points[0]
        if _inbetween(x[0], x[1], intersection_points[1][0]) and \
            not _inbetween(x[0], x[1], intersection_points[0][0]) :
            return intersection_points[1]

        line = np.poly1d(line_coeffs)
        y = line(x)
        start_end_points = np.vstack((x, y)).T

        # Вычислите расстояния до начальной/конечной точек и точек пересечения
        distances = np.zeros((2, 2))
        for i in range(2):
            for j in range(2):
                distances[i, j] = np.linalg.norm(start_end_points[i] -
                                                 intersection_points[j])

        min_idx = np.unravel_index(distances.argmin(), distances.shape)[1]
        return intersection_points[min_idx]

    return intersection_points


def _inbetween(start, end, x):
    return start <= x <= end


def find_line_ellipse_intersection(line_coeffs, x, ellipse_params):
    """
    Если точка не существует, возвращается пустой массив с формой (2,0)
    :param line_coeffs:
    :param x: две точки на линии
    :param ellipse_params:
    :return: np-массив с вертикально сложенными x и y
    """

    x0, y0 = ellipse_params[0:2]
    phi = ellipse_params[4]

    line = np.poly1d(line_coeffs)
    y = line(x)

    # сместить центр эллипса к началу координат
    x_shift = x - x0
    y_shift = y - y0
    points_shift = np.vstack((x_shift, y_shift))

    # поверните точку и эллипс, чтобы выровнять их по осям x и y
    R = np.array([[np.cos(-phi), -np.sin(-phi)], [np.sin(-phi), np.cos(-phi)]])
    point_rotate = R @ points_shift
    x_rotate = point_rotate[0, :]
    y_rotate = point_rotate[1, :]

    line_coeffs_rot = np.polyfit(x_rotate, y_rotate, 1)

    # Выполните фактическое пересечение на центрированном эллипсе
    intersection_points_centered = find_intersection_points_centered(
        line_coeffs_rot, ellipse_params)

    # повернуть назад
    R_inv = np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])
    intersection_points = R_inv @ intersection_points_centered

    # сдвиг назад
    x = intersection_points[0, :] + x0
    y = intersection_points[1, :] + y0

    # Выбирайте только те корни, которые имеют пренебрежимо малое мнимое значение
    x_real = x.real[abs(x.imag) < 1e-5]
    y_real = y.real[abs(x.imag) < 1e-5]

    return np.vstack((x_real, y_real)).T


def find_intersection_points_centered(line_coeffs, ellipse_params):
    """
    Решите квадратичную функцию, найденную здесь, чтобы получить точку пересечения прямой и эллипса:
    https://www.emathzone.com/tutorials/geometry/intersection-of-line-and-ellipse.html
    """
    line = np.poly1d(line_coeffs)

    ap, bp = ellipse_params[2:4]

    m = line_coeffs[0]
    c = line_coeffs[1]

    a = np.square(ap) * np.square(m) + np.square(bp)
    b = 2 * np.square(ap) * m * c
    c = np.square(ap) * (np.square(c) - np.square(bp))

    x_intersected = np.roots([a, b, c])
    y_intersected = line(x_intersected)

    return np.vstack((x_intersected, y_intersected))


# --------------------Получите среднюю точку двух углов------------------------------


def get_theta_middle(theta_1, theta_2):
    """
    Возвращает точку на эллипсе, которая находится между двумя другими точками на эллипсе.
    """
    candidate_1 = (theta_2 + theta_1) / 2
    if theta_2 + theta_1 > 2 * np.pi:
        candidate_2 = (theta_2 + theta_1 - 2 * np.pi) / 2
    else:
        candidate_2 = (theta_2 + theta_1 + 2 * np.pi) / 2

    distance_1 = min(abs(candidate_1 - theta_1), abs(candidate_1 - theta_2))
    distance_2 = min(abs(candidate_2 - theta_1), abs(candidate_2 - theta_2))

    if distance_1 < distance_2:
        return candidate_1

    return candidate_2
