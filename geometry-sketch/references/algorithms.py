# 权威源：本文件是 3.1 算法库的唯一代码权威（薄壳化后 SKILL.md 不再含代码）。
# 直接修改本文件；SKILL.md 只做引用指引。
import math
import sys
import numpy as np

# 强制 UTF-8 输出，避免 Windows GBK 控制台下 print 非 ASCII 字符崩溃
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ============ 基础向量运算 ============

def vec(a, b):
    """向量 AB"""
    return np.array([b[0] - a[0], b[1] - a[1]])

def dist(a, b):
    """两点距离"""
    return np.linalg.norm(vec(a, b))

def midpoint(a, b):
    """AB 中点"""
    return np.array([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2])

def division_point(a, b, ratio):
    """定比分点。ratio = AP/PB，即 P 分 AB 的比例。
    ratio=1 即中点，ratio=2 即靠近 B 的三等分点。"""
    return np.array([
        (a[0] + ratio * b[0]) / (1 + ratio),
        (a[1] + ratio * b[1]) / (1 + ratio)
    ])

def rotate_vec(v, angle_deg):
    """将向量 v 逆时针旋转 angle_deg 度"""
    rad = math.radians(angle_deg)
    cos, sin = math.cos(rad), math.sin(rad)
    return np.array([cos * v[0] - sin * v[1], sin * v[0] + cos * v[1]])

def normalize(v):
    """单位向量"""
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("零向量不能归一化")
    return v / n

# ============ 交点计算 ============

def circle_circle_intersection(c1, r1, c2, r2, side='left'):
    """两圆交点。
    c1, c2: 圆心坐标
    r1, r2: 半径
    side: 'left' 或 'right'，从 c1 看向 c2 时选择左侧还是右侧的交点
    返回交点坐标，无交点时返回 None"""
    d = dist(c1, c2)
    if d > r1 + r2 + 1e-9 or d < abs(r1 - r2) - 1e-9:
        return None  # 无交点
    if d < 1e-12:
        return None  # 同心圆
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h_sq = r1**2 - a**2
    h = math.sqrt(max(0, h_sq))
    mid = np.array([
        c1[0] + a * (c2[0] - c1[0]) / d,
        c1[1] + a * (c2[1] - c1[1]) / d
    ])
    # 从 c1 到 c2 的方向向量
    dx, dy = (c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d
    if side == 'left':
        return np.array([mid[0] - h * dy, mid[1] + h * dx])
    else:
        return np.array([mid[0] + h * dy, mid[1] - h * dx])


def line_intersection(p1, d1, p2, d2):
    """两条直线的交点。d1, d2 均为方向向量（若手头是直线上两点 a,b，方向 = vec(a,b)）。"""
    # p1 + t*d1 = p2 + s*d2
    A = np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]])
    b = np.array([p2[0] - p1[0], p2[1] - p1[1]])
    try:
        t_s = np.linalg.solve(A, b)
        return np.array([p1[0] + t_s[0] * d1[0], p1[1] + t_s[0] * d1[1]])
    except np.linalg.LinAlgError:
        return None  # 平行或重合


def line_circle_intersection(p, d, center, r, side='closer'):
    """直线与圆的交点。直线参数方程 p + t*d。
    side: 'closer' 取离 p 更近的交点, 'farther' 取更远的, 'positive' 取 t>0 的那个"""
    # 将方向向量标准化
    d = normalize(d)
    f = p - center
    a_val = np.dot(d, d)  # = 1 if normalized
    b_val = 2 * np.dot(f, d)
    c_val = np.dot(f, f) - r**2
    disc = b_val**2 - 4 * a_val * c_val
    if disc < -1e-9:
        return None
    disc = max(0, disc)
    sqrt_disc = math.sqrt(disc)
    t1 = (-b_val - sqrt_disc) / (2 * a_val)
    t2 = (-b_val + sqrt_disc) / (2 * a_val)
    if side == 'closer':
        t = t1 if abs(t1) <= abs(t2) else t2
    elif side == 'farther':
        t = t1 if abs(t1) >= abs(t2) else t2
    elif side == 'positive':
        # 取沿 d 正方向的交点；两解都非正时返回 None（p 在圆后方，无前方交点）
        if t1 > 1e-9:
            t = t1
        elif t2 > 1e-9:
            t = t2
        else:
            return None
    else:
        t = t1
    return np.array([p[0] + t * d[0], p[1] + t * d[1]])


def foot_of_perpendicular(p, a, b):
    """点 P 到直线 AB 的垂足"""
    ap = vec(a, p)
    ab = vec(a, b)
    t = np.dot(ap, ab) / np.dot(ab, ab)
    return np.array([a[0] + t * ab[0], a[1] + t * ab[1]])


def parallel_direction(a, b):
    """直线 AB 的单位方向向量（作平行线用）。
    如需过点 P 作平行线并在其上取点 Q 使 PQ=distance：Q = p + distance * parallel_direction(a,b)"""
    return normalize(vec(a, b))


# ============ 角度工具 ============

def angle_between(v1, v2):
    """两向量夹角（弧度）；含零向量时返回 0.0（防除零）"""
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm < 1e-12:
        return 0.0
    dot = np.dot(v1, v2)
    return math.acos(max(-1, min(1, dot / norm)))

def angle_between_deg(v1, v2):
    """两向量夹角（度）"""
    return math.degrees(angle_between(v1, v2))

def angle_at(p, a, b):
    """角 APB（从 PA 到 PB 的有向角，逆时针为正，单位：度）"""
    v1 = vec(p, a)
    v2 = vec(p, b)
    dot = np.dot(v1, v2)
    # 2D 下 np.cross 会崩（它要求 3D 向量），用标量叉积替代，数学语义等价
    cross = v1[0]*v2[1] - v1[1]*v2[0]
    return math.degrees(math.atan2(cross, dot))

def rotate_point(point, center, angle_deg):
    """将 point 绕 center 逆时针旋转 angle_deg 度"""
    v = vec(center, point)
    v_rot = rotate_vec(v, angle_deg)
    return np.array([center[0] + v_rot[0], center[1] + v_rot[1]])


def arc_points(center, radius, theta0, theta1, n=60):
    """圆弧采样点数组（逆时针，theta 弧度）——画弧/扇形用，与 curves 同机制（polyline 渲染）。
    theta1 < theta0 时自动 +2π 保证逆时针；n 为采样点数（含两端）。返回 (N,2) 数组。"""
    if theta1 < theta0:
        theta1 += 2 * math.pi
    th = np.linspace(theta0, theta1, n)
    return np.column_stack([center[0] + radius * np.cos(th), center[1] + radius * np.sin(th)])


# ============ 多边形工具 ============

def polygon_centroid(points):
    """多边形顶点列表的几何中心"""
    pts = np.array(points)
    return np.mean(pts, axis=0)

def scale_distances(points_dict, scale_factor):
    """将所有点坐标按比例缩放（以原点为中心）"""
    # 也可以直接操作 points_dict
    for k in points_dict:
        points_dict[k] = np.array(points_dict[k]) * scale_factor
    return points_dict

# ============ 标记工具（可选） ============

def draw_right_angle_mark(ax, vertex, a, b, size=None):
    """在 vertex 处画直角标记（⊥ 小方块，介于 va 与 vb 之间）。**仅用户明确要求"标直角/标垂直"时调用**，
    默认不画（硬规则 3：等长标记、角度弧线一律不画，直角标记为唯一可选项）。
    size: 小方块边长；None 时取 0.1 × min(边距) 自适应图形尺度。"""
    v = np.array(vertex, dtype=float)
    u1 = np.array(a, dtype=float) - v
    u2 = np.array(b, dtype=float) - v
    n1, n2 = np.linalg.norm(u1), np.linalg.norm(u2)
    if n1 < 1e-12 or n2 < 1e-12:
        return
    e1, e2 = u1 / n1, u2 / n2
    if size is None:
        size = 0.1 * min(n1, n2)
    p1 = v + e1 * size
    p2 = v + e2 * size
    p3 = v + e1 * size + e2 * size
    ax.plot([p1[0], p3[0]], [p1[1], p3[1]], color='black', lw=LW, zorder=5)
    ax.plot([p2[0], p3[0]], [p2[1], p3[1]], color='black', lw=LW, zorder=5)

# ============ 动点 op 求值器（Python 端，与 4.1b JS OP 同语义，勿另写符号约定不同的版本） ============
# 用途：阶段 3 验证默认位置（与 points 对比 <1%）、生成 luts 预计算表。
# 数学语义与 4.1b JS OP 一一对应：rotate 逆时针为正、角度用度；point_on_circle 的 theta 用弧度；
# rotate_cw90/rotate_ccw90 复用同一公式防符号偏差；square_vertex 的 dir=+1 逆时针 / −1 顺时针。
# 2026-08 扩展：seg_intersect = 直线 ab 与直线 cd 的交点（如 P=DE∩CF，两动线段交点类题目需用），
# Python eval_op 与 4.1b JS OP 双端同步（同叉积公式，平行 → NaN）。

def eval_arg(arg, pts, curves=None):
    '''解析 op 参数：数值字面量直返；list 坐标字面量；tuple ('op',[args]) 表达式递归求值；点名查 pts（其值为坐标或嵌套 op 表达式）。
    curves 透传给递归 eval_op（curve_at 需要——否则嵌套表达式/链式 deps 里 curve_at 拿不到曲线数据返回 NaN）。'''
    if isinstance(arg, (int, float)):
        return float(arg)
    if isinstance(arg, (list, tuple)):
        if len(arg) == 2 and isinstance(arg[0], str) and isinstance(arg[1], list):
            return eval_op(arg[0], arg[1], pts, curves)   # ('op', [args...]) 表达式
        return np.array([float(x) for x in arg], dtype=float)  # 坐标字面量
    if arg in pts:
        v = pts[arg]
        if isinstance(v, tuple):
            return eval_op(v[0], v[1], pts, curves)       # 嵌套 deps 链：v 是 op 表达式
        return np.array(v, dtype=float)           # 静态点坐标
    raise ValueError(f"未知参数: {arg}")

def eval_op(op, args, pts, curves=None):
    '''按 op 求值。pts: {点名: 坐标} 或 {点名: ('op', [args...])} 混合（递归）。
    curves（可选）: 曲线点集列表（curve_at op 需要；None 时 curve_at 返回 NaN）。
    与 4.1b JS OP 同语义（符号约定：角度统一逆时针为正；rotate 用度、point_on_circle 用弧度）。'''
    A = [eval_arg(a, pts, curves) for a in args]
    if op == 'symmetry':
        return 2 * A[0] - A[1]                      # symmetry(center, point) = 2*center - point
    if op == 'reflect':                             # 关于直线 ab 的轴对称（垂足法）
        p, a, b = A[0], A[1], A[2]
        ab = b - a
        t = np.dot(p - a, ab) / np.dot(ab, ab)
        h = a + t * ab
        return 2 * h - p
    if op == 'midpoint':
        return (A[0] + A[1]) / 2
    if op == 'ratio_point':
        return (A[0] + A[2] * A[1]) / (1 + A[2])   # ratio = AP/PB
    if op == 'point_on_circle':
        c, rr, th = A[0], A[1], A[2]                # th 弧度
        return np.array([c[0] + rr * math.cos(th), c[1] + rr * math.sin(th)])
    if op == 'point_on_segment':
        a, b, t = A[0], A[1], A[2]
        return a + t * (b - a)
    if op == 'square_vertex':
        a, b, dr = A[0], A[1], A[2]                 # dir=+1 逆时针 / -1 顺时针
        return np.array([b[0] - dr * (b[1] - a[1]), b[1] + dr * (b[0] - a[0])])
    if op == 'translate':
        return A[0] + A[1]
    if op == 'line_through_intersect':              # 过 p 沿 dir 作直线与直线 ab 的交点（叉积；平行 → NaN）
        p, dr, a, b = A[0], A[1], A[2], A[3]
        ab = b - a
        denom = dr[0] * ab[1] - dr[1] * ab[0]      # cross(dir, b-a)
        if abs(denom) < 1e-9:
            return np.array([np.nan, np.nan])
        s = ((a[0] - p[0]) * ab[1] - (a[1] - p[1]) * ab[0]) / denom   # cross(a-p, b-a)/denom
        return np.array([p[0] + s * dr[0], p[1] + s * dr[1]])
    if op == 'seg_intersect':                       # 直线 ab 与直线 cd 的交点（扩展 op 2026-08，Python/JS 双端同步）
        a, b, c, d = A[0], A[1], A[2], A[3]
        rx, ry = b[0] - a[0], b[1] - a[1]
        sx, sy = d[0] - c[0], d[1] - c[1]
        denom = rx * sy - ry * sx                   # cross(r, s)
        if abs(denom) < 1e-9:
            return np.array([np.nan, np.nan])       # 平行无交点
        t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / denom   # cross(c-a, s)/cross(r,s)
        return np.array([a[0] + t * rx, a[1] + t * ry])
    if op == 'circle_line_x':                       # 圆 (center, r=dist(center,other)) 与水平线 y 的交点（扩展 op 2026-08，翻折/圆弧类题通用）
        c, o, yy, sd = A[0], A[1], A[2], A[3]
        r = float(np.linalg.norm(np.asarray(c, dtype=float) - np.asarray(o, dtype=float)))
        dy = yy - c[1]
        if abs(dy) > r + 1e-9:
            return np.array([np.nan, np.nan])       # 水平线在圆外，无交点
        dx = math.sqrt(max(0.0, r * r - dy * dy))
        return np.array([c[0] + sd * dx, yy])       # sd=+1 右侧交点 / -1 左侧交点
    if op == 'rotate':                              # 逆时针为正、度
        c, deg = A[1], A[2]
        rad = math.radians(deg)
        cos, sin = math.cos(rad), math.sin(rad)
        dx, dy = A[0][0] - c[0], A[0][1] - c[1]
        return np.array([c[0] + dx * cos - dy * sin, c[1] + dx * sin + dy * cos])
    if op == 'rotate_cw90':
        c = A[1]
        dx, dy = A[0][0] - c[0], A[0][1] - c[1]
        return np.array([c[0] + dy, c[1] - dx])
    if op == 'rotate_ccw90':
        c = A[1]
        dx, dy = A[0][0] - c[0], A[0][1] - c[1]
        return np.array([c[0] - dy, c[1] + dx])
    if op == 'curve_at':                            # 曲线采样上 x 处点（2026-08，轴上动点→曲线上关联点派生）
        ci, xs = int(A[0]), A[1]
        xs_a = np.asarray(xs)
        x = float(xs_a[0]) if xs_a.ndim == 1 and xs_a.size == 2 else float(xs_a)   # 点名求值后是坐标 → 取 x 分量
        if curves is None or not (0 <= ci < len(curves)):
            return np.array([np.nan, np.nan])
        cv = np.asarray(curves[ci], dtype=float)
        if len(cv) < 2:
            return np.array([np.nan, np.nan])
        # 逐段扫描定位区间（与 JS 端 while 循环一致，不依赖 x 单调升序的 searchsorted 前提）
        x0, y0 = cv[0]; x1, y1 = cv[1]
        for k in range(1, len(cv) - 1):
            if x < cv[k][0]:
                break
            x0, y0 = cv[k]; x1, y1 = cv[k + 1]
        t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0   # 线性插值：x 精度不受采样密度限制
        return np.array([x, y0 + t * (y1 - y0)])
    raise ValueError(f"未知 op: {op}")

