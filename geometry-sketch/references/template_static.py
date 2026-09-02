# 权威源：本文件是 4.1 静态模板（精确/示意/坐标系）的唯一代码权威（薄壳化后 SKILL.md 不再含代码）。
# 直接修改本文件；SKILL.md 只做引用指引。
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys

# 强制 UTF-8 输出，避免 Windows GBK 控制台下 print 非 ASCII 字符崩溃
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ============ 全局样式设置 ============
plt.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.3,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
})

# ============ 颜色常量 ============
# 所有线条统一黑色、等宽
COLOR_LINE = '#000000'
COLOR_LABEL = '#000000'
COLOR_POINT = '#000000'
LW = 1.5

# ============ 🧩 数据定义区（唯一需要模型填空的地方） ============
# 所有变量名固定，勿改名。填空处填具体值，可选处无则留空列表。
output_dir = None   # 输出目录（2026-08 交付规则）：用户提供目标文件夹时填该路径（中间脚本+目标 PNG/HTML 全放其中）；
                    # None = Agent 自行决定（模板兜底当前目录下 geometry_sketch/，勿写死固定路径）
points = {
    # 填空: 'A': np.array([0.0, 0.0]), 'B': np.array([6.0, 0.0]), ...
}
circles = {
    # 可选: 'O': 5.0,  圆心点名 -> 半径
}
segments = [
    # 填空: ('A','B'), ('B','C'), ('C','A'), ...  每条要画的线段
    # ⚠ 目标线段必画：题目所求值表达式中的"两点距离"对应连线（如"求某点甲到某点乙距离的最小值"
    #    → 连接 点甲-点乙），即使题干没说"连接"也要加入 segments
]
required_segments = [
    # 可选: 题面**所有**要求出现的线段，一条不漏——图形边/连接线/目标线段/距离约束线段/
    #   角的两边（∠ABC→BA、BC）/几何要素线段（高线/中线/角平分线/对称轴/折痕/直径等）/
    #   关系载体线段（∥/⊥/共线/相等关系的线段），如 ('A','B'), ('B','C'), ('C','A')
    #   ⚠ 与 segments 同粒度：落点拆线场景写**拆分段**（DC 拆成 (D,E),(E,C) → 写 (D,E),(E,C)，不写 (D,C)）
    #   ⚠ 完整性检测（2026-08，先于孤点补连）：缺失的条目自动补入 segments 并报 [FAIL]（提示模型自查漏画）——
    #   防"正方形只画 3 边"/"角只画一边"/"高线漏画"等线条不完整
]
dashed_segments = [
    # 可选: ('A','D'), ...  用户要求虚线的线段（默认空）
    # ⚠ 虚线段必须**同时进 segments + dashed_segments**（2026-08）：segments 供孤点检测计数
    #   （只连虚线的端点否则被判孤点自动补连多余实线），dashed_segments 供虚线渲染；
    #   绘图执行区 0b 互斥自动把 segments 中的虚线段移除（防叠画），两处同放安全
]
isolated_exempt = [
    # 可选: 'X', ...  用户明确要求不连接的端点/合法链端（如翻折像点只连一条线）——**孤点检测跳过不补连，
    #   标签保留**（2026-08 语义分离：独立于 label_exempt；核心点如所求值载体可安全使用，不丢标签）
]
label_exempt = [
    # 可选: 'X', ...  辅助点/**不标标签**的点（2026-08 新增，语义与 isolated_exempt 分离）——
    #   PNG auto_label 与 HTML label 生成均跳过；需同时不补连的辅助点：isolated_exempt + label_exempt 都填。
    #   ⚠ 仅辅助点可放：题面核心点（图形边/连接线/目标线段端点，即出现在 required_segments 的点）勿放——
    #   双端（PNG+HTML）缺标签，保存前检查会 [WARN]
]
right_angle_marks = [
    # 可选: 直角标记（硬规则 3，**仅用户明确要求"标直角/标垂直"时填**）：
    #   [顶点, 边上一点甲, 边上一点乙]，如 ["A", "B", "D"]
    #   ⚠ PNG 与 HTML 双端口径一致（2026-08）：绘图执行区与 generate_html 共用本数据源，
    #     尺寸用动点模板同公式（0.1×min 短边，clamp 到 0.8%~1.7% 图形跨度）
]
curves = [
    # 可选: 函数曲线点集（反比例/指数/幂/三角等任意函数都由模型采样成折线点集），如
    #   np.array([[-6.0, -0.667], [-5.5, -0.727], ...])
    # 采样规则: x 范围 = 目标显示范围（轴/内容基准），勿无限延伸；
    #   相邻点间距 ≤ 显示跨度的 2% 且点数 ≥ 100（保证平滑）；
    #   **x 单调递增**（函数曲线采样惯例，2026-08：curve_at 插值依赖升序；多值/回折曲线拆分多段）；
    #   渐近线附近 y 爆炸的点跳过（如反比例 x→0 处）
]
axes = False  # 坐标系题设为 True（阶段 0 检测触发）：画 x/y 轴 + 原点 O，轴不参与线段/最长边/孤点检测
# =================================================================

def _restore_full_edges(points, segments):
    """恢复被拆线拆断的完整边（虚线拆线/落点拆线把完整边拆成多段，如 AB → (A,D)+(D,B)）：
    合并**共享端点且中间点在两端点之间**的连续段（|a-x|+|x-b|=|a-b|，拆线的精确特征，
    不误合并延长线交点），迭代处理链式拆分（A-D、D-D'、D'-B）。
    返回完整边列表——**仅用于最长边水平基准检测**（硬规则 #5"整图最长线段"），不修改 segments。"""
    segs = [list(s) for s in segments]
    changed = True
    while changed:
        changed = False
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                s1, s2 = segs[i], segs[j]
                a = b = x = None
                if s1[1] == s2[0]:
                    x, a, b = s1[1], s1[0], s2[1]
                elif s1[0] == s2[1]:
                    x, a, b = s1[0], s1[1], s2[0]
                elif s1[0] == s2[0]:
                    x, a, b = s1[0], s1[1], s2[1]
                elif s1[1] == s2[1]:
                    x, a, b = s1[1], s1[0], s2[0]
                if x is not None and abs(dist(points[a], points[x]) + dist(points[x], points[b])
                                         - dist(points[a], points[b])) < 1e-6:
                    segs[i] = [a, b]
                    segs.pop(j)
                    changed = True
                    break
            if changed:
                break
    return segs


# ============ 🧩 预处理区（自动执行，勿改动，顺序固定） ============
# 1-2. 最长边水平兜底 + 方向归一化（坐标系题跳过：x/y 轴即水平基准，旋转/翻转会破坏坐标值意义）
if not axes:
    # 0. 跨度大方向水平（2026-08，配合画布高宽比约束[1,1.5]）：若 y 跨度显著 > x 跨度（图形高瘦），
    #    旋转 90° 使跨度大方向变水平——避免高瘦图形在宽画布中只占中间竖条、两侧大量空白。
    #    坐标系跳过（x 轴水平规则优先）；动点模式跳过（构造时自行摆水平）
    _xs_all = [p[0] for p in points.values()]
    _ys_all = [p[1] for p in points.values()]
    _xsp, _ysp = max(_xs_all) - min(_xs_all), max(_ys_all) - min(_ys_all)
    if _ysp > _xsp * 1.2:
        # 绕图形中心旋转（防远离原点时位移；等距变换角度/长度不变）
        _center = np.array([(min(_xs_all) + max(_xs_all)) / 2, (min(_ys_all) + max(_ys_all)) / 2])
        for k in points:
            points[k] = rotate_point(points[k], _center, 90)
        # ⚠ curves（函数曲线点集）同步旋转（2026-08 review 修复：否则点与曲线错位）
        for _ci, _cv in enumerate(curves):
            curves[_ci] = np.array([rotate_point(np.array([x, y]), _center, 90) for x, y in _cv])
        print(f"旋转 90° 使跨度大方向水平（原 y 跨度 {_ysp:.1f} > x 跨度 {_xsp:.1f}）")
    # 1. 最长边水平兜底（硬规则 #5：整图最长线段水平。⚠ 虚线拆线/落点拆线把完整边拆成多段
    #    （如 AB→(A,D)+(D,B)），直接在 segments 上检测会退化为"拆分段里最长"、水平基准漂移
    #    （如 AB 被拆后 AC 当选）——先 _restore_full_edges 合并恢复完整边再检测；合并仅用于检测，
    #    不改 segments。仅当主图形长底边已水平（水平且 ≈ 最长线段）才跳过旋转，保护
    #    正方形/矩形/平行四边形朝向；任意短水平线段（拆线/辅助线/恰好水平的边）不构成跳过理由）
    _full = _restore_full_edges(points, segments)
    longest_len = max(dist(points[a], points[b]) for (a, b) in _full) if _full else 0.0
    has_horizontal_base = False
    for (a, b) in _full:
        if abs(points[a][1] - points[b][1]) < 1e-9 \
           and dist(points[a], points[b]) >= 0.8 * longest_len:
            has_horizontal_base = True
            break
    if not has_horizontal_base and _full:
        longest = max(_full, key=lambda p: dist(points[p[0]], points[p[1]]))
        v = vec(points[longest[0]], points[longest[1]])
        ang = math.degrees(math.atan2(v[1], v[0]))
        if abs(ang) > 1:
            for k in points:
                points[k] = rotate_point(points[k], np.array([0.,0.]), -ang)
            print(f"旋转 {-ang:.1f} 度使 {longest[0]}{longest[1]} 水平")
        else:
            print(f"最长边 {longest[0]}{longest[1]} 已水平，无需旋转")
    elif _full:
        print("已有水平底边，跳过旋转兜底")

    # 2. 方向归一化：确保图形主体在水平线上方（y>0），避免倒置
    avg_y = sum(p[1] for p in points.values()) / len(points)
    if avg_y < 0:
        for k in points:
            points[k][1] = -points[k][1]
        print("垂直翻转使图形主体朝上")

# 3. 题面条目线段完整性检测（2026-08，先于孤点补连）：required_segments 列出题面所有要求出现的线段
#（图形边/连接线/目标线段/距离约束线段），缺失自动补入并报 [FAIL]——先抓"图形边不完整/连接线漏画"，
# 避免正方形缺边这类情况走到孤点补连（最近点可能连错）
if required_segments:
    _missing = []
    for (_a, _b) in required_segments:
        if (_a, _b) not in segments and (_b, _a) not in segments:
            _missing.append((_a, _b))
    if _missing:
        for (_a, _b) in _missing:
            segments.append((_a, _b))
            print(f"[FAIL] 题面条目线段缺失，已自动补入: {_a}-{_b}")
        print(f"[FAIL] required_segments 有 {len(_missing)} 条缺失（模型请自查为何漏画）")
    else:
        print("[OK] required_segments 全部在 segments 中")

# 3b. label_exempt × 题面结构点交叉检查（2026-08，交付检查）：label_exempt 双端（PNG auto_label + HTML
# generate_html）豁免标签——若含 required_segments 中的题面结构点（图形边/连接线/目标线段端点），双端缺标签。
# [WARN] 提示而非 [FAIL]：模板无法自动判定核心点，垂足等辅助点也可能出现在 required 线段，模型自查确认。
if label_exempt:
    _req_pts = set()
    for (_a, _b) in required_segments:
        _req_pts.add(_a); _req_pts.add(_b)
    _core_exempt = [n for n in label_exempt if n in _req_pts]
    if _core_exempt:
        print(f"[WARN] label_exempt 含题面结构点 {_core_exempt}（出现在 required_segments）——PNG/HTML 双端缺标签；"
              f"仅辅助点可豁免，核心点请移出（PNG 标注位置问题另想办法：接受自动标注或微调坐标）")
    else:
        print("[OK] label_exempt 均为纯辅助点（不与题面条目线段端点重叠）")

# 3c. 拆段顺序检查（2026-08 交付检查，补 4.2「检测盲区」）：**首尾相接**（s1[1]==s2[0] 或 s1[0]==s2[1]）
# 且三点共线的段对，中间点必须严格在两端点之间（|a-x|+|x-b|≈|a-b|）——否则拆段顺序写错（跨点/重叠）会静默视觉错乱。
# 同起点/同终点（如数轴 O-A、O-B）不是拆线连续，不查（防误报）
for _i in range(len(segments)):
    for _j in range(_i + 1, len(segments)):
        _s1, _s2 = segments[_i], segments[_j]
        _x = None
        if _s1[1] == _s2[0]:
            _x, _a, _b = _s1[1], _s1[0], _s2[1]
        elif _s1[0] == _s2[1]:
            _x, _a, _b = _s1[0], _s1[1], _s2[0]
        if _x is not None:
            _va = points[_a] - points[_x]; _vb = points[_b] - points[_x]
            if abs(_va[0] * _vb[1] - _va[1] * _vb[0]) < 1e-9 * max(1.0, np.linalg.norm(_va) * np.linalg.norm(_vb)):
                _d1 = dist(points[_a], points[_x]); _d2 = dist(points[_x], points[_b])
                _d = dist(points[_a], points[_b])
                if abs(_d1 + _d2 - _d) > 1e-6 * max(1.0, _d):
                    print(f"[WARN] 拆段顺序疑错: 段 {tuple(_s1)} 与 {tuple(_s2)} 首尾相接共线但 {_x} 不在 {_a}-{_b} 之间"
                          f"（|{_a}{_x}|+|{_x}{_b}|={_d1 + _d2:.3f} ≠ |{_a}{_b}|={_d:.3f}）——拆线模式请按沿线顺序写（勿跨点/重叠）；"
                          f"若为合法共线端点（如垂足落在延长线上）可忽略本 WARN")

# 4. 孤点检测：每个点至少出现在 segments 的 2 条线段中，不足自动补连最近点（在完整性检测之后执行，
#    required_segments 已补入缺边，此处补连的是真正的悬空端点）
from collections import Counter
deg = Counter()
for (a, b) in segments:
    deg[a] += 1; deg[b] += 1
for name in points:
    if name in isolated_exempt:
        continue  # 用户主动豁免，跳过警告和补连
    if deg[name] < 2:
        print(f"[WARN] 点 {name} 仅连 {deg[name]} 条线段（孤点），自动补连到最近已有点")
        best, best_d = None, 1e9
        for other in points:
            if other != name and (name,other) not in segments and (other,name) not in segments:
                d = dist(points[name], points[other])
                if d < best_d:
                    best, best_d = other, d
        if best and best_d < 10:
            segments.append((name, best))
            print(f"  已补连 {name}-{best} (距离 {best_d:.2f})")
            deg[name] += 1; deg[best] += 1
# =================================================================

# ============ 创建画布 ============
# 根据坐标范围和圆/曲线的范围确定 figure size
x_coords = [p[0] for p in points.values()]
y_coords = [p[1] for p in points.values()]
# 如果有圆，圆心±半径也要纳入范围，防止圆被裁切
for name, info in circles.items():   # circles = {'O': 5, ...}  圆心名→半径
    cx, cy = points[name]
    x_coords.extend([cx - info, cx + info])
    y_coords.extend([cy - info, cy + info])
# 函数曲线点集纳入范围（防裁切）：先按非曲线基准范围（点+圆）外扩 ±10% 裁剪，防极端点撑大画布
if curves:
    if points or circles:
        _bx_lo, _bx_hi = min(x_coords), max(x_coords)
        _by_lo, _by_hi = min(y_coords), max(y_coords)
        _sx = 0.1 * (_bx_hi - _bx_lo) if _bx_hi > _bx_lo else 1.0
        _sy = 0.1 * (_by_hi - _by_lo) if _by_hi > _by_lo else 1.0
        _cx_lo, _cx_hi = _bx_lo - _sx, _bx_hi + _sx
        _cy_lo, _cy_hi = _by_lo - _sy, _by_hi + _sy
        for _cv in curves:
            _m = ((_cv[:, 0] >= _cx_lo) & (_cv[:, 0] <= _cx_hi) &
                  (_cv[:, 1] >= _cy_lo) & (_cv[:, 1] <= _cy_hi))
            x_coords.extend(_cv[_m, 0])
            y_coords.extend(_cv[_m, 1])
    else:
        for _cv in curves:
            x_coords.extend(_cv[:, 0])
            y_coords.extend(_cv[:, 1])
# 坐标系：先算轴范围（内容驱动：点+圆+曲线 → 对称 → 空半轴缩减 → 智能 margin），再纳入画布防裁切
if axes:
    _axis_xmin_c, _axis_xmax_c = min(x_coords), max(x_coords)
    _axis_ymin_c, _axis_ymax_c = min(y_coords), max(y_coords)
    _margin = max(1.0, 0.15 * max(_axis_xmax_c - _axis_xmin_c, _axis_ymax_c - _axis_ymin_c))
    _xp, _xn = max(_axis_xmax_c, 0.0), max(-_axis_xmin_c, 0.0)
    _yp, _yn = max(_axis_ymax_c, 0.0), max(-_axis_ymin_c, 0.0)
    _xlen = max(_xp, _xn) + _margin
    _ylen = max(_yp, _yn) + _margin
    if _xlen < 0.8 * _ylen: _xlen = 0.8 * _ylen
    if _ylen < 0.8 * _xlen: _ylen = 0.8 * _xlen
    _xhi = _xlen if _xp > 0 else _margin
    _xlo = -_xlen if _xn > 0 else -_margin
    _yhi = _ylen if _yp > 0 else _margin
    _ylo = -_ylen if _yn > 0 else -_margin
    x_coords.extend([_xlo, _xhi])   # 轴端点纳入画布，防 PNG 缺轴
    y_coords.extend([_ylo, _yhi])
    # 轴矩形检查：曲线点超出轴范围时警告（绘图时会裁剪，见绘图执行区 0c）
    if curves:
        for _cv in curves:
            _ox = (_cv[:, 0] < _xlo) | (_cv[:, 0] > _xhi)
            _oy = (_cv[:, 1] < _ylo) | (_cv[:, 1] > _yhi)
            if _ox.any() or _oy.any():
                print(f"[WARN] 曲线有 {int(_ox.sum() + _oy.sum())} 个点超出坐标轴范围，绘图时将裁剪")
x_min, x_max = min(x_coords), max(x_coords)
y_min, y_max = min(y_coords), max(y_coords)
pad_x = max(1.0, (x_max - x_min) * 0.25)
pad_y = max(1.0, (y_max - y_min) * 0.25)
width = x_max - x_min + 2 * pad_x
height = y_max - y_min + 2 * pad_y

# 画布高宽比约束（2026-08，适配宽屏）：目标 aspect = width/height ∈ [1, 1.5]（宽 ≥ 高）——
# 防高瘦画布（高>宽）在宽屏上需大幅上下滚动；数据不变形，扩展 padding（图形水平居中，两侧留白）
aspect = width / height
if aspect < 1.0:
    _extra = (height * 1.0 - width) / 2
    pad_x += _extra
    width += 2 * _extra
elif aspect > 1.5:
    _extra = (width / 1.5 - height) / 2
    pad_y += _extra
    height += 2 * _extra

# 保持等比例
aspect = width / height
fig_width = max(5, min(10, 6 * aspect))
fig_height = fig_width / aspect
# 标注字号随画布宽度缩放（2026-08，与 HTML 端 vw 缩放同思路）：fig_width=6 基准 13，clamp [9,18]
_fs_png = max(9, min(18, int(round(13 * fig_width / 6.0))))

fig, ax = plt.subplots(figsize=(fig_width, fig_height))  # 勿加 frameon=False（与 axis('off') 组合会渲染全白）
fig.set_facecolor('white')
ax.set_facecolor('white')
ax.set_aspect('equal')
ax.axis('off')
ax.set_xlim(x_min - pad_x, x_max + pad_x)
ax.set_ylim(y_min - pad_y, y_max + pad_y)

# 边界检查：确保所有元素在画布内（含圆的完整范围）
for name, info in circles.items():
    cx, cy = points[name]
    assert cx - info >= x_min - pad_x and cx + info <= x_max + pad_x, f"圆 {name} 超出水平边界"
    assert cy - info >= y_min - pad_y and cy + info <= y_max + pad_y, f"圆 {name} 超出垂直边界"

# ============ 绘图函数 ============

def draw_segment(ax, a, b, ls='-', zorder=1):
    """画线段（黑色，等宽）"""
    ax.plot([a[0], b[0]], [a[1], b[1]], color=COLOR_LINE, lw=LW, ls=ls, zorder=zorder, solid_capstyle='butt')

def draw_ray(ax, start, direction, length, ls='-', zorder=0):
    """画射线（辅助线）"""
    d = direction / np.linalg.norm(direction) * length
    end = start + d
    ax.plot([start[0], end[0]], [start[1], end[1]], color=COLOR_LINE, lw=LW, ls=ls, zorder=zorder)

def draw_circle(ax, center, radius, zorder=0):
    """画圆（黑色，等宽）"""
    c = mpatches.Circle(center, radius, fill=False, ec=COLOR_LINE, lw=LW, zorder=zorder)
    ax.add_patch(c)

def draw_point(ax, p, size=6, zorder=5):
    """画点（黑色实心，与线宽一致）"""
    ax.scatter(p[0], p[1], c=COLOR_POINT, s=size, zorder=zorder)

def draw_label(ax, text, pos, offset=(0.15, 0.15), fontsize=None):
    """在点旁边标注字母（Times New Roman 斜体大写）；fontsize 缺省用画布宽度缩放字号（2026-08）"""
    if fontsize is None:
        fontsize = _fs_png
    ax.text(pos[0] + offset[0], pos[1] + offset[1], text,
            fontsize=fontsize, color=COLOR_LABEL, fontweight='normal',
            fontname='Times New Roman', style='italic',
            ha='center', va='center')

# 参数速查（默认全实线，用户要求虚线时参考）：
#   draw_segment(ax, a, b, ls='--')   → 虚线线段
#   draw_ray(ax, start, dir, len, ls='--') → 虚线射线
#   只标字母不画点：调用 draw_label 但不调 draw_point 即可
#   虚线被实线遮盖 → 见 4.2「虚线拆线」规则：拆实线、删原段、加虚线

# ============ 标注重叠检测辅助 ============
def _point_to_segment_dist(pt, a, b):
    """点 pt 到线段 ab 的最短距离"""
    ab = b - a
    t = np.dot(pt - a, ab) / np.dot(ab, ab)
    t = max(0, min(1, t))
    proj = a + t * ab
    return np.linalg.norm(pt - proj)

# ============ 自动标注点 ============
def auto_label(ax, points, segments, existing_labels=None, axes=False):
    """自动标注所有点。
    points: {name: coord} 字典
    自动为每个点选择不重叠的标注偏移方向。
    axes=True（坐标系题）：点在坐标轴上时，标签偏移强制向轴外，避免与轴重合。
    """
    if existing_labels is None:
        existing_labels = set()
    names = sorted(points.keys())
    # 简单策略：以图形中心为参考，标签朝外偏移
    center = np.mean([p for p in points.values()], axis=0)
    # A1：标签两两碰撞检测——8 方位候选（与 HTML OFFSETS 一致）+ 已放置标签记录（PNG 端）
    _CAND = [np.array([1,1]), np.array([-1,1]), np.array([-1,-1]), np.array([1,-1]),
             np.array([0,1]), np.array([0,-1]), np.array([-1,0]), np.array([1,0])]
    _placed = {}
    _collide = 0.8   # 碰撞阈值：两标签中心距 < 0.8 视为重叠（偏移 0.35 量级）
    for name in names:
        if name in label_exempt:
            continue  # label_exempt 辅助点不标标签（2026-08 语义分离：isolated_exempt 仅控不补连，标签保留）
        if name in existing_labels:
            continue
        # ④ axes 下跳过原点 O 标签（坐标轴代码已在原点标 O；仅当 O 恰在原点时跳过，不误伤非原点的 O）
        if axes and name == 'O' and np.allclose(points[name], [0.0, 0.0]):
            continue
        p = points[name]
        d = normalize(vec(center, p)) if dist(center, p) > 0.01 else np.array([0, 1])
        offset = d * 0.35
        # 坐标系题避轴：点在 x 轴上(y≈0)时 y 偏移向外；点在 y 轴上(x≈0)时 x 偏移向外
        if axes:
            if abs(p[1]) < 0.5 and abs(p[0]) > 0.5:
                offset = np.array([offset[0], 0.35 if p[1] >= 0 else -0.35])
            elif abs(p[0]) < 0.5 and abs(p[1]) > 0.5:
                offset = np.array([0.35 if p[0] >= 0 else -0.35, offset[1]])
        # 检查标注是否与线段重叠，重叠则尝试替代偏移
        final_offset = tuple(offset)
        for seg in segments:
            if name in seg:
                continue  # 不检查标注点自身所在的线段
            a_pt, b_pt = points[seg[0]], points[seg[1]]
            d_seg = _point_to_segment_dist(p + offset, a_pt, b_pt)
            if d_seg < 0.3:
                alt_offsets = [(-offset[0], offset[1]), (offset[0], -offset[1]),
                              (-offset[0], -offset[1]), (offset[0]*1.5, offset[1]*1.5)]
                for alt in alt_offsets:
                    if _point_to_segment_dist(p + np.array(alt), a_pt, b_pt) >= 0.3:
                        final_offset = tuple(alt)
                        break
        # A1：标签 vs 标签碰撞——与已放置标签重叠则换 8 方位（选第一个不冲突且不碰线段的）
        for _t in range(4):
            _hit = False
            for _p2, _off2 in _placed.values():
                if np.linalg.norm((p + np.array(final_offset)) - (_p2 + np.array(_off2))) < _collide:
                    _hit = True
                    break
            if not _hit:
                break
            _chosen = None
            for _c in _CAND:
                _alt = tuple(_c * 0.35)
                _ok = True
                for _p2, _off2 in _placed.values():
                    if np.linalg.norm((p + np.array(_alt)) - (_p2 + np.array(_off2))) < _collide:
                        _ok = False
                        break
                if _ok:
                    for seg in segments:
                        if name in seg:
                            continue
                        if _point_to_segment_dist(p + np.array(_alt), points[seg[0]], points[seg[1]]) < 0.3:
                            _ok = False
                            break
                if _ok:
                    _chosen = _alt
                    break
            if _chosen is not None:
                final_offset = _chosen
            else:
                break
        draw_label(ax, name, p, offset=final_offset)
        _placed[name] = (np.array(p, dtype=float), np.array(final_offset, dtype=float))

# ============ 🧩 绘图执行区（固定顺序，勿改动） ============
# 0a. 坐标系：若有，画带箭头 x/y 轴（范围已在创建画布区算好：_xlo/_xhi/_ylo/_yhi，zorder=0 最底层），轴不进 segments
if axes:
    ax.annotate('', xy=(_xhi, 0), xytext=(_xlo, 0),
                arrowprops=dict(arrowstyle='->', color='black', lw=LW), zorder=0)
    ax.annotate('', xy=(0, _yhi), xytext=(0, _ylo),
                arrowprops=dict(arrowstyle='->', color='black', lw=LW), zorder=0)
    # 轴端标注：x/y 斜体小写（x 在箭头下方，y 在箭头偏左）；原点 O 斜体大写，标准左下方
    ax.text(_xhi + 0.3, -0.3, 'x', fontsize=_fs_png, style='italic',
            fontname='Times New Roman', ha='left', va='top')
    ax.text(-0.3, _yhi + 0.3, 'y', fontsize=_fs_png, style='italic',
            fontname='Times New Roman', ha='right', va='bottom')
    ax.text(-0.25, -0.25, 'O', fontsize=_fs_png, style='italic',
            fontname='Times New Roman', ha='right', va='top')
# 0b. 互斥：虚线段若也在 segments，先从 segments 移除（防叠画；无虚线时此循环空转）
for (a, b) in list(dashed_segments):
    if (a, b) in segments:
        segments.remove((a, b))
    elif (b, a) in segments:
        segments.remove((b, a))
# 0c. 函数曲线（若有）：zorder 0.5，介于轴(0)与线段(1)之间，防止盖住线段
for _cv in curves:
    if axes:
        # 坐标系：曲线裁剪到轴矩形内，确保内容不超出坐标轴
        _m = ((_cv[:, 0] >= _xlo) & (_cv[:, 0] <= _xhi) &
              (_cv[:, 1] >= _ylo) & (_cv[:, 1] <= _yhi))
        _cv = _cv[_m]
    ax.plot(_cv[:, 0], _cv[:, 1], color='black', lw=LW, zorder=0.5)
# 1. 画实线
for (a, b) in segments:
    draw_segment(ax, points[a], points[b])
# 2. 画虚线（用户要求时才非空；虚线必须在实线之后画，见 4.2 拆线规则）
for (a, b) in dashed_segments:
    draw_segment(ax, points[a], points[b], ls='--')
# 3. 画圆
for name, r in circles.items():
    draw_circle(ax, points[name], r)
# 4. 画点
for name in points:
    draw_point(ax, points[name])
# 5. 标注字母
auto_label(ax, points, segments, axes=axes)
# 6. 直角标记（可选项，硬规则 3）：right_angle_marks 数据驱动（PNG/HTML 双端口径一致，2026-08）——
#    仅用户明确要求"标直角/标垂直"时非空；尺寸与动点模板 JS 同公式（0.1×min 短边，clamp 0.8%~1.7% 跨度）
if right_angle_marks:
    _ramark_span = max(x_max - x_min, y_max - y_min)
    for _m in right_angle_marks:
        _v, _a, _b = points[_m[0]], points[_m[1]], points[_m[2]]
        _n1, _n2 = dist(_v, _a), dist(_v, _b)
        if _n1 < 1e-12 or _n2 < 1e-12:
            continue
        _size = max(0.008 * _ramark_span, min(0.017 * _ramark_span, 0.1 * min(_n1, _n2)))
        draw_right_angle_mark(ax, _v, _a, _b, size=_size)
# 7. 可选扩展区（翻折/对称/坐标系轴等额外绘制放这里）
#    ⚠ 双渲染路径：本区为 PNG 独有（ax.plot 直绘），HTML 的 generate_html 不感知——
#      几何线条（含开放图形覆盖动点范围，如直线 BC 需覆盖关联点 Q 的可达域）必须走
#      segments/curves 数据区（PNG/HTML 共用），禁止在本区手绘承担几何表达；本区仅供装饰
# ============================================================

# ============ 保存 ============
# 输出目录（2026-08 交付规则）：用户提供目标文件夹 → 数据区 output_dir 填该路径（中间+目标文件全放其中）；
# 未提供 → Agent 自行决定（默认 None，兜底当前目录下 geometry_sketch/）；勿写死固定路径
import os
if not output_dir:
    output_dir = os.path.join(os.getcwd(), "geometry_sketch")
os.makedirs(output_dir, exist_ok=True)
output_base = os.path.join(output_dir, "geometry_sketch")

# ============ 🛑 保存前自查（逐条核对，有违例则改） ============
# [ ] 双渲染路径一致：几何线条全在 segments/circles/curves 数据区（PNG/HTML 共用）；扩展区无 draw_ray/draw_segment 承担几何表达（仅装饰/直角标记）
# [ ] label_exempt 仅含辅助点——题面核心点（required_segments 端点）误放会导致 PNG/HTML 双端缺标签（保存前自动检查 [WARN]，见 3b）
# [ ] 代码中无 "svg" / "SVG"
# [ ] 无 draw_angle_mark / draw_equal_length_mark；draw_right_angle_mark 仅在用户明确要求时调用
# [ ] 无旧颜色 '#2d3436' / '#636e72' / '#e17055' / '#d63031'
# [ ] 背景必须为白色（fig.set_facecolor + ax.set_facecolor）
# [ ] 无 ls='--'（全部实线）
# [ ] 无 fontweight='bold'
# [ ] 有圆的图形：是否定义了 circles 字典？半径是否纳入了画布范围？
# [ ] 所有元素是否都在画布边界内？（点 + 圆完整范围）
# [ ] print 无 ✓/✗ 等特殊符号（用 [OK]/[FAIL] 替代；中文描述性 print 允许）
# [ ] 最终边界检查：遍历所有点+圆，确认无任何元素超出画布
# ================================================================

# 🛑 最终边界检查：确保整个图形在画布内
for k, p in points.items():
    assert x_min - pad_x <= p[0] <= x_max + pad_x, f"点 {k} 超出水平边界"
    assert y_min - pad_y <= p[1] <= y_max + pad_y, f"点 {k} 超出垂直边界"
for name, info in circles.items():
    cx, cy = points[name]
    assert cx - info >= x_min - pad_x and cx + info <= x_max + pad_x, f"圆 {name} 超出水平边界"
    assert cy - info >= y_min - pad_y and cy + info <= y_max + pad_y, f"圆 {name} 超出垂直边界"
print("边界检查通过")


# ============ HTML 可旋转预览 ============
def generate_html(points, segments, circles, x_min, x_max, y_min, y_max, pad_x, pad_y, output_path, axes=False, xlo=0.0, xhi=0.0, ylo=0.0, yhi=0.0, curves=None, dashed_segments=None, right_angle_marks=None):
    """生成可旋转、可镜像、可缩放的交互式 HTML 文件"""
    svg_w = x_max - x_min + 2 * pad_x
    svg_h = y_max - y_min + 2 * pad_y
    scale = min(800 / svg_w, 600 / svg_h)
    vw = svg_w * scale
    vh = svg_h * scale
    cx, cy = vw / 2, vh / 2
    # 标注字号随画布宽度缩放（2026-08）：vw=500 基准 14，clamp [9,20]——画布大则标注大、小则小（相对画布比例稳定）
    _fs = max(9, min(20, int(round(14 * vw / 500.0))))

    off_x = x_min - pad_x
    off_y = y_max + pad_y
    def svg_point(x, y):
        return ((x - off_x) * scale, (off_y - y) * scale)

    geo_elems = []
    # 坐标轴（若有）：范围用创建画布区算好的 xlo/xhi/ylo/yhi（与 PNG 一致），正方向端带箭头（SVG marker）
    if axes:
        x0, y0 = svg_point(xlo, 0); x1, y1 = svg_point(xhi, 0)
        geo_elems.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="black" stroke-width="1.5" marker-end="url(#arrowh)"/>')
        x2, y2 = svg_point(0, ylo); x3, y3 = svg_point(0, yhi)
        geo_elems.append(f'<line x1="{x2:.1f}" y1="{y2:.1f}" x2="{x3:.1f}" y2="{y3:.1f}" stroke="black" stroke-width="1.5" marker-end="url(#arrowv)"/>')
        # 轴端标注 x/y（斜体小写）与原点 O（斜体大写）：默认偏移 x/y/O = 0.12/0.14/0.1 数据单位（2026-08 由 0.3/0.25 缩减、
        # "adist=0 时仍远"反馈；y 拉远到 0.14 补偿 x 垂直对齐 leading 空隙使视觉距离一致——x 为垂直 top 对齐（字形
        # 上沿与文本框顶有 leading 空隙）、y 为水平 end 对齐（字形右缘直接贴线））；方位修正——x 在箭头正下方
        # （无水平偏移 + text-anchor middle 居中）、y 在箭头正左方（无垂直偏移）、O 在原点左下方（end 对齐）。
        # data-dx/dy 为固定方位向量，JS 按 adist 延长
        _xx, _xy = svg_point(xhi, -0.12)
        geo_elems.append(f'<text class="axislabel" data-k="x" data-bx="{_xx:.1f}" data-by="{_xy:.1f}" data-dx="0" data-dy="1" x="{_xx:.1f}" y="{_xy:.1f}" text-anchor="middle" dominant-baseline="text-before-edge" font-size="{_fs}" font-style="italic" fill="black" font-family="Times New Roman, serif">x</text>')
        _yx, _yy = svg_point(-0.14, yhi)
        geo_elems.append(f'<text class="axislabel" data-k="y" data-bx="{_yx:.1f}" data-by="{_yy:.1f}" data-dx="-1" data-dy="0" x="{_yx:.1f}" y="{_yy:.1f}" text-anchor="end" dominant-baseline="text-before-edge" font-size="{_fs}" font-style="italic" fill="black" font-family="Times New Roman, serif">y</text>')
        ox, oy = svg_point(-0.1, -0.1)
        geo_elems.append(f'<text class="axislabel" data-k="O" data-bx="{ox:.1f}" data-by="{oy:.1f}" data-dx="-1" data-dy="1" x="{ox:.1f}" y="{oy:.1f}" text-anchor="end" dominant-baseline="text-before-edge" font-size="{_fs}" font-style="italic" fill="black" font-family="Times New Roman, serif">O</text>')
    # 函数曲线（若有）：SVG polyline，画在线段之前（zorder 更低，防盖住线段）
    if curves:
        for _cv in curves:
            if axes:
                # 坐标系：曲线裁剪到轴矩形内（与 PNG 一致），确保内容不超出坐标轴
                _m = ((_cv[:, 0] >= xlo) & (_cv[:, 0] <= xhi) &
                      (_cv[:, 1] >= ylo) & (_cv[:, 1] <= yhi))
                _cv = _cv[_m]
            _pts = ' '.join(f"{svg_point(x, y)[0]:.1f},{svg_point(x, y)[1]:.1f}" for x, y in _cv)
            geo_elems.append(f'<polyline points="{_pts}" fill="none" stroke="black" stroke-width="1.5"/>')
    for (a, b) in segments:
        x1, y1 = svg_point(points[a][0], points[a][1])
        x2, y2 = svg_point(points[b][0], points[b][1])
        geo_elems.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.5" stroke-linecap="round"/>')
    # 虚线（若用户要求）：与 PNG 端一致（双渲染路径，2026-08 修复——早期 generate_html 未渲染虚线）
    if dashed_segments:
        for (a, b) in dashed_segments:
            x1, y1 = svg_point(points[a][0], points[a][1])
            x2, y2 = svg_point(points[b][0], points[b][1])
            geo_elems.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="6,4"/>')

    for name, r in circles.items():
        cx_c, cy_c = svg_point(points[name][0], points[name][1])
        geo_elems.append(f'<circle cx="{cx_c:.1f}" cy="{cy_c:.1f}" r="{r * scale:.1f}" fill="none" stroke="black" stroke-width="1.5"/>')

    # 点标记（与 PNG 一致）
    for name, p in points.items():
        px, py = svg_point(p[0], p[1])
        geo_elems.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.5" fill="black" stroke="none"/>')

    # 直角标记（可选项，硬规则 3）：right_angle_marks 数据驱动（PNG/HTML 双端口径一致，2026-08）
    # 尺寸与动点模板 JS 同公式（0.1×min 短边，clamp 0.8%~1.7% 跨度）；静态点不动，生成时一次算好
    if right_angle_marks:
        _ramark_span = max(x_max - x_min, y_max - y_min)
        for _m in right_angle_marks:
            _v = np.asarray(points[_m[0]], dtype=float)
            _a = np.asarray(points[_m[1]], dtype=float)
            _b = np.asarray(points[_m[2]], dtype=float)
            _u1, _u2 = _a - _v, _b - _v
            _n1, _n2 = np.linalg.norm(_u1), np.linalg.norm(_u2)
            if _n1 < 1e-12 or _n2 < 1e-12:
                continue
            _e1, _e2 = _u1 / _n1, _u2 / _n2
            _size = max(0.008 * _ramark_span, min(0.017 * _ramark_span, 0.1 * min(_n1, _n2)))
            _p1 = _v + _e1 * _size
            _p2 = _v + _e2 * _size
            _p3 = _v + (_e1 + _e2) * _size
            _s1, _s2, _s3 = svg_point(_p1[0], _p1[1]), svg_point(_p2[0], _p2[1]), svg_point(_p3[0], _p3[1])
            geo_elems.append(f'<line x1="{_s1[0]:.1f}" y1="{_s1[1]:.1f}" x2="{_s3[0]:.1f}" y2="{_s3[1]:.1f}" stroke="black" stroke-width="1.5"/>')
            geo_elems.append(f'<line x1="{_s2[0]:.1f}" y1="{_s2[1]:.1f}" x2="{_s3[0]:.1f}" y2="{_s3[1]:.1f}" stroke="black" stroke-width="1.5"/>')

    # 标注文字（在旋转组外，JS 计算位置以保持水平）
    # 8 个方位（前 4 对角 + 后 4 上下左右），点击循环切换
    label_elems = []
    for _li, (name, p) in enumerate(points.items()):   # id 用序号（点名含撇号 B' 等不可拼进 id，防 HTML 属性破裂）；点名存 data-name
        if name in label_exempt:
            continue  # label_exempt 辅助点 HTML 标签不生成（2026-08 语义分离；点标记保留）
        px, py = svg_point(p[0], p[1])
        label_elems.append(f'<text class="lab" id="lab_{_li}" data-name="{name}" x="0" y="0" data-lx="{px:.1f}" data-ly="{py:.1f}" data-pos="0" text-anchor="middle" dominant-baseline="central" font-size="{_fs}" fill="black" font-family="Times New Roman, serif" font-style="italic" style="cursor:pointer" onclick="clickLabel(this)">{name}</text>')

    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Geometry Sketch</title>
<style>
  body{{margin:0;display:flex;flex-direction:column;align-items:center;background:#eee;font-family:sans-serif;}}
  #toolbar{{margin:10px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;position:sticky;top:0;z-index:10;background:#eee;padding:8px;border-bottom:1px solid #ccc;}}
  button{{padding:2px 8px;cursor:pointer;}}
  #main_svg{{border:1px solid #ccc;background:#fff;}}
</style></head>
<body onload="update()">
<div id="toolbar">
  <label>旋转: <input id="rot" type="range" min="0" max="360" value="0" oninput="update()" style="width:120px">
  <input id="rot_num" type="number" min="0" max="360" value="0" oninput="setRot(this.value)" style="width:45px">°</label>
  <button onclick="setRot(90)">90°</button><button onclick="setRot(180)">180°</button><button onclick="setRot(270)">270°</button>
  <button onclick="flip('h')">水平镜像</button><button onclick="flip('v')">垂直镜像</button>
  <label>标注距离: <input id="ldist" type="range" min="4" max="30" value="14" oninput="update()" style="width:80px"><span id="ldist_val">14</span></label>
  <label>轴标注距离: <input id="adist" type="range" min="-20" max="40" value="0" oninput="update()" style="width:80px"><span id="adist_val">0</span></label>
  <label>字号: <input id="fs_slider" type="range" min="4" max="24" value="{_fs}" oninput="update()" style="width:80px"><span id="fs_val">{_fs}</span></label>
  <label>缩放: <input id="scale_slider" type="range" min="20" max="200" value="100" oninput="update()" style="width:100px">
  <span id="scale_val">100%</span></label>
  <label>左右: <input id="pan" type="range" min="{-0.3*vw:.0f}" max="{0.3*vw:.0f}" value="0" oninput="update()" style="width:100px">
  <span id="pan_val">0</span></label>
  <button onclick="savePNG()" style="font-weight:bold">保存为 PNG</button>
</div>
<svg id="main_svg" viewBox="0 0 {vw:.0f} {vh:.0f}" xmlns="http://www.w3.org/2000/svg">
  <rect id="capture_box" x="0" y="0" width="{vw:.0f}" height="{vh:.0f}" fill="none" stroke="#999" stroke-dasharray="8,4" stroke-width="1"/>
  <defs>
    <marker id="arrowh" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="black"/></marker>
    <marker id="arrowv" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="black"/></marker>
  </defs>
  <g id="geo_group" transform="translate({cx:.1f},{cy:.1f}) rotate(0) scale(1,1) translate({-cx:.1f},{-cy:.1f})">
    {''.join(geo_elems)}
  </g>
  <g id="label_group">
    {''.join(label_elems)}
  </g>
</svg>
<script>
let h_flip=1, v_flip=1, panX=0;   // 左右平移（最外层，与旋转/镜像正交）
const OFFSETS = [[12,-12],[-12,-12],[-12,12],[12,12],[0,-12],[0,12],[-12,0],[12,0]];  // 8方位：前4对角 + 后4上下左右
const FS = {_fs};   // 标注字号（随画布宽度缩放，2026-08）：偏移因子 = FS/14
function update(){{
  let r=parseFloat(document.getElementById("rot").value);
  document.getElementById("rot_num").value=r;
  let s=parseInt(document.getElementById("scale_slider").value)/100;
  document.getElementById("scale_val").textContent=Math.round(s*100)+"%";
  let d=parseFloat(document.getElementById("ldist").value);
  document.getElementById("ldist_val").textContent=d;
  let fs=parseInt(document.getElementById("fs_slider").value);
  document.getElementById("fs_val").textContent=fs;
  let ad=parseFloat(document.getElementById("adist").value);
  document.getElementById("adist_val").textContent=ad;
  document.querySelectorAll(".lab").forEach(t=>{{t.setAttribute("font-size", fs);}});
  // 轴标注 x/y/O：字号 + 距离可调（方位固定——x 沿箭头下、y 沿箭头左、O 沿原点左下，data-dx/dy 方向向量）
  document.querySelectorAll(".axislabel").forEach(t=>{{
    t.setAttribute("font-size", fs);
    let bx=parseFloat(t.dataset.bx), by=parseFloat(t.dataset.by);
    t.setAttribute("x", (bx + ad*parseFloat(t.dataset.dx)).toFixed(1));
    t.setAttribute("y", (by + ad*parseFloat(t.dataset.dy)).toFixed(1));
  }});
  panX=parseInt(document.getElementById("pan").value);
  document.getElementById("pan_val").textContent=panX;
  let g=document.getElementById("geo_group");
  // 平移在最外层（translate(cx+panX,cy)），与 scale/rotate 正交——旋转中心/镜像轴不变
  g.setAttribute("transform","translate("+({cx:.1f}+panX)+",{cy:.1f}) scale("+(s*h_flip)+","+(s*v_flip)+") rotate("+r+") translate({-cx:.1f},{-cy:.1f})");
  let rad=r*Math.PI/180, cos=Math.cos(rad), sin=Math.sin(rad);
  document.querySelectorAll(".lab").forEach(t=>{{
    let lx=parseFloat(t.dataset.lx), ly=parseFloat(t.dataset.ly);
    let dx=lx-{cx:.1f}, dy=ly-{cy:.1f};
    let rx=dx*cos - dy*sin, ry=dx*sin + dy*cos;
    rx*=s*h_flip; ry*=s*v_flip;
    let off = OFFSETS[parseInt(t.dataset.pos)];
    let k = d * FS / 196;   // 标注距离×字号缩放合并式（避免同行多除号被静态检查正则误判，2026-08）
    t.setAttribute("x",{cx:.1f}+panX+rx+off[0]*k*h_flip); t.setAttribute("y",{cy:.1f}+ry+off[1]*k*v_flip);
    t.removeAttribute("transform");
  }});
}}
function clickLabel(el){{
  el.dataset.pos = (parseInt(el.dataset.pos)+1)%8;
  update();
}}
function setRot(v){{
  document.getElementById("rot").value=v;
  update();
}}
function flip(dir){{
  if(dir=="h") h_flip*=-1; else v_flip*=-1;
  update();
}}
function savePNG(){{
  let svg=document.getElementById("main_svg");
  let vb=svg.viewBox.baseVal;
  // 分辨率用 viewBox 尺寸 ×3（2026-08：×2 时线条边缘仍有锯齿；×3 更细腻）
  let sw=Math.round(vb.width*3);
  let sh=Math.round(vb.height*3);
  let box=document.getElementById("capture_box");
  box.setAttribute("display","none");   // 导出前隐藏虚线框
  // ⚠ 锯齿根因修复（2026-08）：序列化的 SVG 仅 viewBox 无 width/height → 浏览器按默认尺寸
  //   （~300px）栅格化 img，再 drawImage 拉伸到 canvas → 线条拉伸模糊锯齿。导出前显式设置
  //   SVG 尺寸 = canvas 尺寸，img 栅格化 1:1 不拉伸；导出后恢复原属性
  let _ow=svg.getAttribute("width"), _oh=svg.getAttribute("height");
  svg.setAttribute("width", sw);
  svg.setAttribute("height", sh);
  let data=new XMLSerializer().serializeToString(svg);
  if (_ow) svg.setAttribute("width", _ow); else svg.removeAttribute("width");
  if (_oh) svg.setAttribute("height", _oh); else svg.removeAttribute("height");
  box.setAttribute("display","inline");  // 导出后恢复
  let canvas=document.createElement("canvas");
  canvas.width=sw;canvas.height=sh;
  let ctx=canvas.getContext("2d");
  let img=new Image();
  img.onload=function(){{ctx.fillStyle="#fff";ctx.fillRect(0,0,sw,sh);ctx.drawImage(img,0,0,sw,sh);
    // 保存选路径（2026-08）：Chromium 用 showSaveFilePicker 弹"另存为"对话框选路径；
    // 不支持/用户取消/权限拒绝时回退 <a download> 下载到默认目录
    let dl=function(href){{let a=document.createElement("a");a.download="geometry_sketch.png";a.href=href;a.click();}};
    if (window.showSaveFilePicker){{
      canvas.toBlob(function(blob){{
        if(!blob){{dl(canvas.toDataURL("image/png"));return;}}
        let url=URL.createObjectURL(blob);
        let picker = null;
        try {{ picker=window.showSaveFilePicker({{suggestedName:"geometry_sketch.png",types:[{{description:"PNG 图片",accept:{{"image/png":[".png"]}}}}]}}); }}
        catch(e) {{ dl(url); setTimeout(function(){{URL.revokeObjectURL(url);}},2000); return; }}   // 同步抛错（激活过期/权限）→ 回退
        picker
          .then(function(h){{return h.createWritable();}})
          .then(function(w){{return w.write(blob).then(function(){{return w.close();}});}})
          .catch(function(e){{if(e.name!=="AbortError"){{dl(url);setTimeout(function(){{URL.revokeObjectURL(url);}},2000);}}}})
          .then(function(){{setTimeout(function(){{URL.revokeObjectURL(url);}},2000);}});
      }},"image/png");
    }} else {{
      dl(canvas.toDataURL("image/png"));
    }}
  }};
  img.src="data:image/svg+xml;base64,"+btoa(unescape(encodeURIComponent(data)));
}}
</script>
</body></html>'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

# 保存 PNG
png_path = output_base + ".png"
plt.savefig(png_path, dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"PNG 已保存至: {png_path}")

# 生成可旋转 HTML
html_path = output_base + ".html"
if axes:
    generate_html(points, segments, circles, x_min, x_max, y_min, y_max, pad_x, pad_y, html_path, axes, _xlo, _xhi, _ylo, _yhi, curves, dashed_segments, right_angle_marks)
else:
    generate_html(points, segments, circles, x_min, x_max, y_min, y_max, pad_x, pad_y, html_path, axes, curves=curves, dashed_segments=dashed_segments, right_angle_marks=right_angle_marks)
print(f"HTML 已保存至: {html_path}")

plt.close()
print("绘图完成。")

