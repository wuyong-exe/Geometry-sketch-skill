# 权威源：本文件是 4.1b 动点模板（含 JS 交互内核）的唯一代码权威（薄壳化后 SKILL.md 不再含代码）。
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
    # 填空: '静态点甲': np.array([0.0, 0.0]), '静态点乙': np.array([6.0, 0.0]), ...
}
circles = {
    # 可选: '圆心': 5.0,  圆心点名 -> 半径
    # ⚠ 仅题面明说"在…圆上/以…为直径"时定义可见圆；
    #   旋转类动点（"旋转一周/绕点转动"）的圆是隐含轨迹，不定义在这里（见 luts 隐藏轨迹）
}
segments = [
    # 填空: ('静态点甲','静态点乙'), ('静态点乙','静态点丙'), ('静态点丙','静态点甲'), ...  每条要画的线段
    # ⚠ 目标线段必画：题目所求值表达式中的"两点距离"对应连线（如"求某点甲到某点乙距离的最小值"
    #    → 连接 点甲-点乙），即使题干没说"连接"也要加入 segments（看题人需要看到目标线段的几何意义）
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
    # 可选: ('静态点甲','辅助点'), ...  用户要求虚线的线段（默认空）
    # ⚠ 虚线段必须**同时进 segments + dashed_segments**（2026-08）：segments 供孤点检测计数
    #   （只连虚线的端点否则被判孤点自动补连多余实线），dashed_segments 供虚线渲染；
    #   绘图执行区 0b 互斥自动把 segments 中的虚线段移除（防叠画），两处同放安全
]
isolated_exempt = [
    # 可选: '孤立端点', ...  用户明确要求不连接的端点/合法链端（如翻折像点只连一条线）——**孤点检测跳过不补连，
    #   标签保留**（2026-08 语义分离：独立于 label_exempt；核心点如所求值载体可安全使用，不丢标签）
]
label_exempt = [
    # 可选: '孤立端点', ...  辅助点/**不标标签**的点（2026-08 新增，语义与 isolated_exempt 分离）——
    #   PNG auto_label 与 HTML label 生成均跳过；需同时不补连的辅助点：isolated_exempt + label_exempt 都填。
    #   ⚠ 仅辅助点可放：题面核心点（图形边/连接线/目标线段端点，即出现在 required_segments 的点）勿放——
    #   双端（PNG+HTML）缺标签，保存前检查会 [WARN]
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
dynamics = None  # 动点模式（可选，默认 None 关闭）：
#   题目含"动点/一动点/在...上运动/滑动/绕点转动"等关键词时启用。
#   多动点版：active=一级动点列表（多个独立自由动点）+ params 逐点参数化 + deps 关联点（非独立点）。
#   结构示例（键名为角色占位，实际填题目点名；文档一律用角色名，不出现具体字母示例）：
#   {
#     "active": ["一级动点甲", "一级动点乙"],   # 独立自由动点，每个必须存在于 points
#     "params": {
#       "一级动点甲": {"type": "circle", "center": "圆心", "radius": 1.0, "theta": 1.2, "theta_min": 0.0, "theta_max": 6.283},
#         #   circle:  圆上动点，theta 弧度（从 x 轴正方向逆时针）
#         #   theta_min/theta_max 限定弧段（题面如"劣弧/上半圆"时填；不填 = 全圆，滑块 0~360°）
#       "一级动点乙": {"type": "segment", "a": "线段端点甲", "b": "线段端点乙", "t": 0.5},  # t∈[0,1]
#       "一级动点丙": {"type": "line", "point": "基准点", "dir": [1.0, 0.0], "t": 1.0, "t_min": -3.0, "t_max": 3.0},
#         #   line: 直线上动点（含坐标轴/函数直线），位置 = 基准点 + t×方向向量
#         #   t_min/t_max 限定直线上段（题面如"BC 上方直线段"时填；不填 = 默认 ±3，滑块 -300~300，拖拽同界）
#       "一级动点丁": {"type": "curve", "curve_index": 0, "x": 0.5, "x_min": -1.0, "x_max": 2.0},
#         #   curve: 曲线/函数图像上动点（抛物线、反比例等），位置 = curves[curve_index] 上 x 处点
#         #   x 为参数（题面区间由 x_min/x_max 限定，如"线段 BC 上方"段）；⚠ 必须生成 LUT（见 luts 200 点约定），
#         #   JS 无法解析任意函数，曲线动点一律查表；拖拽 = 鼠标位置到 LUT 最近邻吸附，点始终在曲线上
#     },
#     "deps": {   # 关联点（非独立点）：位置不由自身参数决定、由一级动点派生。按题面关系识别并推导：
#       #   对称点→symmetry、中点→midpoint、定比分点→ratio_point、平移（如"随动点右移"）→translate、
#       #   正方形顶点→square_vertex、圆/线段上的从属点→point_on_*；op 表没有的关系（位似/任意旋转等）
#       #   → Python 直接推导坐标公式（阶段 3 算 LUT 或扩展 op），JS 端无感知
#       #   ⚠ args 支持嵌套 op 表达式（2026-08 JS 对齐 Python）：数组 ["op名",[子args]] 递归求值，
#       #     如 "F": {"op":"translate","args":[["rotate_cw90",["E","A"]],[0.0,4.0]]}（绕 A 顺时针 90° 再平移）；
#       #     也可拆中间构造点（G=rotate_cw90(E,A) → F=translate(G,[0,4])），两种写法等价
#       "关联点甲": {"op": "translate", "args": ["一级动点乙", [3.0, 0.0]]},   # 关联点 = 一级动点乙 + 平移向量
#     },
#     "luts": {   # 预计算位置表（Python 阶段 3 生成，JS 查表 O(1)）。⚠ 可空：
#       #   关联点直接引用一级动点（无二级链）时留空 {}，走 op 公式实时求值（evalPoint 对 deps 永远重算）
#       #   ⚠ 兼作隐藏轨迹：旋转类动点的圆轨迹写在这里（不画可见圆，HTML 默认呈现轨迹虚线，可取消勾选——2026-08）
#       #   圆上动点：θ 按 0.5° 步长采样 720 点，下标 i = round(θ*360/π) mod 720（θ 弧度）
#       #   线段动点：t 按 0.01 步长采样 101 点，下标 i = round(t*100)
#       #   曲线动点：x 在 [x_min,x_max] 均匀采样 200 点，下标 i = round((x-x_min)/(x_max-x_min)*199)；⚠ 曲线动点强制 LUT
#       "关联点甲": [[x0, y0], [x1, y1], ...],   # 有二级链的关联点各一张表
#     },
#     "readouts": [           # 实时读数（可选，留空列表则不显示读数区）
#       {"label": "关联点坐标", "expr": "p", "fmt": "(%.2f, %.2f)"},   # p = 第一个关联点
#       {"label": "目标式", "expr": "3*p[0]+4*p[1]", "fmt": "%.2f"},   # expr 需带乘号，形如 a*p[0]+b*p[1]+c
#     ],
#     "trajectory": ["一级动点甲", "关联点甲"],   # 显示轨迹点名列表（可选）：
#       # 组成规则：全部一级动点 + **涉及题目所求值的关联点**（所求值对象；不含中间构造点）
#       # 纯图形题（无所求值）→ 只列一级动点；不填默认 = 只一级动点。HTML 默认呈现（勾选框默认勾选，可取消——2026-08）
#     "right_angle_marks": [["顶点", "另一点甲", "另一点乙"], ...],   # 直角标记（可选，**仅用户明确要求"标直角/标垂直"时填**）：
#       # 每项 = [顶点, 边上一点甲, 边上一点乙]，在顶点处画直角小方块（HTML 端随动点实时跟随，硬规则 3）
#   }
#   op 集合：symmetry(center,point) / midpoint(a,b) / ratio_point(a,b,ratio)
#     / point_on_circle(center,radius,theta) / point_on_segment(a,b,t) / reflect(point,a,b)
#     / square_vertex(a,b,dir) / translate(point,向量) / line_through_intersect(p,dir,a,b)
#     / seg_intersect(a,b,c,d)（直线 ab 与直线 cd 的交点，如"连接 DE、CF 交于点 P"）
#     / circle_line_x(center,other,y,sd)（圆 (center, 过 other) 与水平线 y 的交点，sd=+1 右 / −1 左，翻折落点/圆弧类题通用）
#     / curve_at(curve_index,x源)（曲线采样上 x 处点，线性插值；x源=数值 或 点名取其 x 分量——轴上动点→曲线上关联点派生）
#   ⚠ 层级：active=一级动点（独立自由动点，可多个）；deps=关联点（非独立点，引用一级动点或二级链，禁环）
#   ⚠ 动点模式下 points 提供默认位置（用于 PNG 与 HTML 初始渲染），
#     dynamics 提供参数化关系（用于 HTML 交互实时重算），两者必须一致。
#   ⚠ 动点模式跳过预处理区旋转/翻转兜底（同 axes 豁免）：模型构造时自行摆水平。
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
# 1-2. 最长边水平兜底 + 方向归一化（坐标系题/动点模式跳过：旋转/翻转会破坏坐标值或参数化关系）
if not axes and dynamics is None:
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
        # ⚠ curves（函数曲线点集）同步旋转（2026-08 review 修复：否则点与曲线错位；曲线可承运动点影响更大）
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

# 3c. 动点 op/type 合法性（2026-08 交付检查）：deps 关联点的 op 必须在 4.1b JS OP 集合、
# params 的 type 必须 ∈ 四类型——否则 HTML 端 evalPoint/paramPoint 会 TypeError（如漏扩 seg_intersect 的教训）
if dynamics:
    _OPS = {'symmetry', 'reflect', 'midpoint', 'ratio_point', 'point_on_circle', 'point_on_segment',
            'square_vertex', 'translate', 'line_through_intersect', 'seg_intersect', 'circle_line_x',
            'rotate', 'rotate_cw90', 'rotate_ccw90', 'curve_at'}
    _TYPES = {'circle', 'segment', 'line', 'curve'}
    for _n, _d in dynamics.get('deps', {}).items():
        if _d.get('op') not in _OPS:
            print(f"[FAIL] deps 关联点 {_n} 使用未知 op: {_d.get('op')}（不在 4.1b JS OP 集合——HTML 端交互会 TypeError，请检查或扩展模板）")
    for _n, _p in dynamics.get('params', {}).items():
        if _p.get('type') not in _TYPES:
            print(f"[FAIL] 动点 {_n} 的 type 未知: {_p.get('type')}（应为 circle/segment/line/curve 之一）")

# 3d. 拆段顺序检查（2026-08 交付检查，补 4.2「检测盲区」）：**首尾相接**（s1[1]==s2[0] 或 s1[0]==s2[1]）
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

def compute_dynamic_extent(dynamics, points, curves):
    """动点可达范围（画布输入，2026-08 ④修复）：返回 (x_list, y_list) 供画布范围扩展。
    一级动点按类型取可达边界：segment 端点已在 points（静态点，跳过）；circle 圆心±半径；
    line 基准点±dir·t 两端；curve 曲线采样 x∈[x_min,x_max] 段的 x/y 极值。
    二级及以上动点（deps）：仅对 **points 中的可见关联点**（中间构造点不在 points、
    不显示 → 豁免画布采样，否则会凭空拉大画布）沿依赖链找被引用的一级动点（可多个）→
    参数网格组合采样 → eval_op 映射本点位置（pts 保留全部 deps 表达式供 eval_arg 递归求值）。
    params 的 center/point/a/b 应为 points 内静态点名（勿引用 deps 点，动态圆心属边缘场景）。"""
    if not dynamics:
        return [], []
    xs, ys = [], []
    for n in dynamics['active']:
        p = dynamics['params'][n]
        if p['type'] == 'segment':
            continue
        if p['type'] == 'circle':
            try:
                c = points[p['center']]
            except KeyError:
                continue  # center 引用 deps 点（边缘场景）：跳过画布扩展防崩（与二级分支防护一致，2026-08）
            xs += [c[0] - p['radius'], c[0] + p['radius']]
            ys += [c[1] - p['radius'], c[1] + p['radius']]
        elif p['type'] == 'line':
            try:
                b = np.asarray(points[p['point']], dtype=float)
            except KeyError:
                continue  # point 引用 deps 点（边缘场景）：跳过画布扩展防崩（2026-08）
            d = np.asarray(p['dir'], dtype=float)
            for tt in (p.get('t_min', -3), p.get('t_max', 3)):
                q = b + d * tt
                xs.append(q[0]); ys.append(q[1])
        elif p['type'] == 'curve':
            ci = p.get('curve_index', 0)
            if 0 <= ci < len(curves):
                cv = np.asarray(curves[ci], dtype=float)
                m = (cv[:, 0] >= p['x_min']) & (cv[:, 0] <= p['x_max'])
                seg = cv[m]
                if len(seg):
                    xs += [seg[:, 0].min(), seg[:, 0].max()]
                    ys += [seg[:, 1].min(), seg[:, 1].max()]
    for dn, dep in dynamics.get('deps', {}).items():
        if dn not in points:
            continue  # 中间构造点不显示：豁免画布采样（pts2 仍保留其 op 表达式供 eval_op 递归求值）
        # 沿 deps 链找被引用的一级动点（同 check_open_coverage._find 语义；可多个）
        def _find(exp, seen):
            if isinstance(exp, str):
                if exp in dynamics['active']:
                    return exp
                if exp in dynamics.get('deps', {}):
                    for a in dynamics['deps'][exp]['args']:
                        if isinstance(a, str):
                            if a in seen:
                                continue
                            seen.add(a)
                            r = _find(a, seen)
                            if r:
                                return r
                        elif isinstance(a, (list, tuple)) and len(a) == 2 and isinstance(a[0], str) and isinstance(a[1], list):
                            # 嵌套 op 表达式（2026-08，与 eval_arg 同语义）：穿透子 args 找一级动点
                            # （否则嵌套写法的 deps 点可达范围漏进画布，拆链写法能找到）
                            for sa in a[1]:
                                if isinstance(sa, str):
                                    if sa in seen:
                                        continue
                                    seen.add(sa)
                                r = _find(sa, seen)
                                if r:
                                    return r
            return None
        acts = []
        for a in dep['args']:
            if not isinstance(a, str):
                continue
            r = _find(a, {a})
            if r and r not in acts:
                acts.append(r)
        if not acts:
            continue
        # 参数网格：circle 41 点 / 其余 21 点；多一级动点时每维压到 ≤11 点防组合爆炸
        grids = []
        for act in acts:
            pp = dynamics['params'][act]
            if pp['type'] == 'circle':
                g = np.linspace(pp.get('theta_min', 0.0), pp.get('theta_max', 2 * math.pi), 41)
            elif pp['type'] == 'line':
                g = np.linspace(pp.get('t_min', -3), pp.get('t_max', 3), 21)
            elif pp['type'] == 'curve':
                g = np.linspace(pp['x_min'], pp['x_max'], 21)
            else:  # segment
                g = np.linspace(0, 1, 21)
            if len(acts) > 1:
                g = g[::max(1, int(np.ceil(len(g) / 11)))]
            grids.append(g)
        import itertools
        combos = list(itertools.product(*grids))
        if len(combos) > 200:  # 组合过多时降采样（最多 200 组合）
            combos = combos[::int(np.ceil(len(combos) / 200))]
        for combo in combos:
            pts2 = {k: np.asarray(v, dtype=float) for k, v in points.items()}
            for dn, ddep in dynamics.get('deps', {}).items():  # deps 链表达式供 eval_arg 递归求值
                pts2[dn] = (ddep['op'], list(ddep['args']))
            for act, val in zip(acts, combo):
                pp = dynamics['params'][act]
                if pp['type'] == 'circle':
                    c = np.asarray(points[pp['center']], dtype=float)
                    pts2[act] = np.array([c[0] + pp['radius'] * math.cos(val), c[1] + pp['radius'] * math.sin(val)])
                elif pp['type'] == 'curve':
                    ci = pp.get('curve_index', 0)
                    cv = np.asarray(curves[ci], dtype=float)
                    pts2[act] = cv[int(np.argmin(np.abs(cv[:, 0] - val)))]
                elif pp['type'] == 'segment':
                    a = np.asarray(points[pp['a']], dtype=float)
                    b = np.asarray(points[pp['b']], dtype=float)
                    pts2[act] = a + val * (b - a)
                else:  # line
                    pts2[act] = np.asarray(points[pp['point']], dtype=float) + np.asarray(pp['dir'], dtype=float) * val
            try:
                pos = np.asarray(eval_op(dep['op'], dep['args'], pts2, curves), dtype=float)
            except Exception:
                continue
            if not np.isnan(pos).any():
                xs.append(pos[0]); ys.append(pos[1])
    return xs, ys


# ============ 创建画布 ============
# 根据坐标范围和圆/曲线的范围确定 figure size
x_coords = [p[0] for p in points.values()]
y_coords = [p[1] for p in points.values()]
# 如果有圆，圆心±半径也要纳入范围，防止圆被裁切
for name, info in circles.items():   # circles = {'圆心': 5, ...}  圆心名→半径
    cx, cy = points[name]
    x_coords.extend([cx - info, cx + info])
    y_coords.extend([cy - info, cy + info])
# 函数曲线点集纳入范围（防裁切）：先按非曲线基准范围（点+圆）外扩 ±10% 裁剪，防极端点撑大画布
if curves:
    # ① 直线型检测：点集拟合 y=kx+b，残差 < 相对阈值 → 无渐近线/爆炸点 → 跳过预裁剪、全量纳入范围；
    #    非直线型（反比例/抛物线）仍走 ±10% 矩形预裁剪，防渐近线爆炸点撑大画布
    for _cv in curves:
        if len(_cv) >= 3:
            _xs, _ys = _cv[:, 0], _cv[:, 1]
            _A = np.vstack([_xs, np.ones_like(_xs)]).T
            _k, _b = np.linalg.lstsq(_A, _ys, rcond=None)[0]
            _resid = np.max(np.abs((_k * _xs + _b) - _ys))
            if _resid < 1e-6 * max(1.0, float(np.max(np.abs(_ys)))):
                x_coords.extend(_xs)   # 直线型：全量纳入
                y_coords.extend(_ys)
                continue
        if points or circles:
            _bx_lo, _bx_hi = min(x_coords), max(x_coords)
            _by_lo, _by_hi = min(y_coords), max(y_coords)
            _sx = 0.1 * (_bx_hi - _bx_lo) if _bx_hi > _bx_lo else 1.0
            _sy = 0.1 * (_by_hi - _by_lo) if _by_hi > _by_lo else 1.0
            _cx_lo, _cx_hi = _bx_lo - _sx, _bx_hi + _sx
            _cy_lo, _cy_hi = _by_lo - _sy, _by_hi + _sy
            _m = ((_cv[:, 0] >= _cx_lo) & (_cv[:, 0] <= _cx_hi) &
                  (_cv[:, 1] >= _cy_lo) & (_cv[:, 1] <= _cy_hi))
            x_coords.extend(_cv[_m, 0])
            y_coords.extend(_cv[_m, 1])
        else:
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
# 动点覆盖（2026-08 ④修复）：动点可达范围纳入画布——一级按类型边界、二级及以上沿 deps 链
# 参数网格采样映射（compute_dynamic_extent）。PNG 与 HTML 共用 x_min/y_min 等，同源解决：
# 拖动点到极端位置时图形/标注不超出画布与 SVG viewBox（替代早期手工 max(y_max, 6.0) 硬编码）
if dynamics:
    _dyn_x, _dyn_y = compute_dynamic_extent(dynamics, points, curves)
    x_coords.extend(_dyn_x)
    y_coords.extend(_dyn_y)
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
def auto_label(ax, points, segments, existing_labels=None, axes=False, curves=None):
    # ② 曲线上点偏移优先取曲线法线（唯一不与曲线相交的方向）；偏移/冲突阈值随图形尺度缩放（防小图过严/大图过松）
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
    # 图形尺度：points 范围中位非零跨度 → 偏移/阈值随尺度缩放（防小图过严/大图过松）
    _arr0 = np.array([p0 for p0 in points.values()])
    _spans = np.ptp(_arr0, axis=0)
    _nz = _spans[_spans > 0]
    _scale = float(np.median(_nz)) if _nz.size else 1.0
    _scale = max(_scale, 1e-3)
    _off_unit = 0.35 * _scale
    _tol = 0.3 * _scale
    # A1：标签两两碰撞检测——8 方位候选（对角 + 上下左右，与 HTML OFFSETS 一致）+ 已放置标签记录
    _CAND = [np.array([1,1]), np.array([-1,1]), np.array([-1,-1]), np.array([1,-1]),
             np.array([0,1]), np.array([0,-1]), np.array([-1,0]), np.array([1,0])]
    _placed = {}   # name -> (p, offset)；碰撞阈值 = 2×偏移量（两标签中心距 < 2×off 视为重叠）
    _collide = 2.2 * _off_unit
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
        offset = d * _off_unit
        # ②(b) 曲线上点：偏移优先取曲线在该点处的法线——取**最近曲线**（所有曲线中距 p 最近者），
        #    而非第一条满足阈值的曲线（多曲线时顺序一变标签方向就不确定，A2 修复）
        if curves:
            _best_d = _tol * 0.4
            _best_n = None
            for _cv in curves:
                _d = np.linalg.norm(_cv - p, axis=1)
                _k = int(np.argmin(_d))
                if _d[_k] < _best_d:
                    _i0 = max(0, _k - 1); _i1 = min(len(_cv) - 1, _k + 1)
                    _t = _cv[_i1] - _cv[_i0]
                    _n = np.array([-_t[1], _t[0]])
                    _nn = np.linalg.norm(_n)
                    if _nn > 1e-12:
                        _best_n = _n / _nn
                        _best_d = _d[_k]
            if _best_n is not None:
                offset = _best_n * _off_unit
        # 坐标系题避轴：点在 x 轴上(y≈0)时 y 偏移向外；点在 y 轴上(x≈0)时 x 偏移向外
        if axes:
            if abs(p[1]) < 0.5 and abs(p[0]) > 0.5:
                offset = np.array([offset[0], _off_unit if p[1] >= 0 else -_off_unit])
            elif abs(p[0]) < 0.5 and abs(p[1]) > 0.5:
                offset = np.array([_off_unit if p[0] >= 0 else -_off_unit, offset[1]])
        # 检查标注是否与线段重叠，重叠则尝试替代偏移
        final_offset = tuple(offset)
        for seg in segments:
            if name in seg:
                continue  # 不检查标注点自身所在的线段
            a_pt, b_pt = points[seg[0]], points[seg[1]]
            d_seg = _point_to_segment_dist(p + offset, a_pt, b_pt)
            if d_seg < _tol:
                alt_offsets = [(-offset[0], offset[1]), (offset[0], -offset[1]),
                              (-offset[0], -offset[1]), (offset[0]*1.5, offset[1]*1.5)]
                for alt in alt_offsets:
                    if _point_to_segment_dist(p + np.array(alt), a_pt, b_pt) >= _tol:
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
            # 换位：8 方位候选 × _off_unit，跳过与主方向完全相反的，取第一个不冲突且线段避让通过的
            _chosen = None
            for _c in _CAND:
                _alt = tuple(_c * _off_unit)
                _ok = True
                for _p2, _off2 in _placed.values():
                    if np.linalg.norm((p + np.array(_alt)) - (_p2 + np.array(_off2))) < _collide:
                        _ok = False
                        break
                if _ok:
                    for seg in segments:
                        if name in seg:
                            continue
                        if _point_to_segment_dist(p + np.array(_alt), points[seg[0]], points[seg[1]]) < _tol:
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


def check_open_coverage(dynamics, curves, segments, points):
    """开放图形覆盖动点范围自动校验（B2）——保存前自查区调用。
    全部动点（一级 line/curve + 二级及以上经 eval_op 沿依赖链映射）采样可达位置，
    用距离法判断是否被开放图形集（curves 全部 + segments 全部）覆盖。
    统一处理直线型与非直线型（抛物线/反比例等 polyline 不做 x 单调假设）。
    闭合图形动点（segment/circle 类型）不参与（动点不会拖出）。"""
    if not dynamics:
        return True
    pts = dict(points)
    # 全部开放图形点集：curves（polyline）+ segments 端点线（采样）
    open_pts = []
    for _cv in curves:
        open_pts.append(np.asarray(_cv, dtype=float))
    for (a, b) in segments:
        _pa, _pb = np.asarray(points[a], dtype=float), np.asarray(points[b], dtype=float)
        _ts = np.linspace(0, 1, 25)
        open_pts.append((_pa[None, :] * (1 - _ts[:, None]) + _pb[None, :] * _ts[:, None]))
    # axes 模式：坐标轴纳入开放图形集（轴上 line 动点如 E(m,0) 的可达范围由轴覆盖，
    # 否则依赖"恰好有轴上线段"的侥幸——x 轴无其他线段时会误判 FAIL 拦出图）。
    # ⚠ 轴点单独存、不入 _scale 计算（轴跨度会撑大 _eps 使覆盖校验变宽松漏检）；轴点仍参与距离判定
    _axis_pts = []
    if axes:
        _axis_pts = [np.column_stack([np.linspace(x_min, x_max, 41), np.zeros(41)]),   # x 轴
                     np.column_stack([np.zeros(41), np.linspace(y_min, y_max, 41)])]   # y 轴
    if not open_pts and not _axis_pts:
        return True
    _base = np.vstack(open_pts) if open_pts else np.array([[0.0, 0.0]])
    open_pts = np.vstack(open_pts + _axis_pts)
    _scale = max(np.ptp(_base, axis=0).max(), 1e-3)   # 阈值基于非轴图形范围
    _eps = 0.1 * _scale

    def _nearest(pp):
        return float(np.min(np.linalg.norm(open_pts - pp, axis=1)))

    def _sample_point(name, t):
        # 采样 name 在参数 t（0-1 归一化到该动点范围）下的位置；二级及以上沿 deps 链 eval_op 映射
        p = dynamics['params'].get(name)
        if p:
            if p['type'] == 'line':
                tmin = p.get('t_min', -3); tmax = p.get('t_max', 3)
                tt = tmin + (tmax - tmin) * t
                try:
                    base = np.asarray(points[p['point']], dtype=float)
                except KeyError:
                    return None  # point 引用 deps 点（边缘场景）：跳过采样（与 compute_dynamic_extent 防护一致，2026-08）
                d = np.asarray(p['dir'], dtype=float)
                return base + d * tt
            if p['type'] == 'curve':
                ci = p.get('curve_index', 0)
                cv = np.asarray(curves[ci], dtype=float)
                x = p['x_min'] + (p['x_max'] - p['x_min']) * t
                idx = int(np.argmin(np.abs(cv[:, 0] - x)))
                return cv[idx]
        # 二级及以上：找依赖链上一级动点，采样它并 eval_op 映射出本点
        dep = dynamics['deps'].get(name)
        if dep:
            # 找被引用的一级动点（沿 args 递归；seen 防环，与 compute_dynamic_extent._find 一致，2026-08）
            # ⚠ 单参数采样设计（与 compute_dynamic_extent 求极值的差异）：B2 沿**第一个**一级动点采样（t 归一化），
            #   其余一级动点用其默认位置——完备的多维参数空间覆盖由 compute_dynamic_extent 画布扩展与轨迹显示承担，
            #   此处仅做可达范围抽检（避免为边缘的多一级动点场景重构采样架构引入回归）
            def _find(exp, seen):
                if isinstance(exp, str):
                    if exp in dynamics.get('active', []):
                        return exp
                    if exp in dynamics.get('deps', {}):
                        for a in dynamics['deps'][exp]['args']:
                            if isinstance(a, str):
                                if a in seen:
                                    continue
                                seen.add(a)
                                r = _find(a, seen)
                                if r:
                                    return r
                            elif isinstance(a, (list, tuple)) and len(a) == 2 and isinstance(a[0], str) and isinstance(a[1], list):
                                # 嵌套 op 表达式（2026-08，与 eval_arg 同语义）：穿透子 args 找一级动点
                                for sa in a[1]:
                                    if isinstance(sa, str):
                                        if sa in seen:
                                            continue
                                        seen.add(sa)
                                    r = _find(sa, seen)
                                    if r:
                                        return r
                return None
            act = None
            for a in dep['args']:
                if isinstance(a, str):
                    act = _find(a, {a})
                    if act:
                        break
                elif isinstance(a, (list, tuple)) and len(a) == 2 and isinstance(a[0], str) and isinstance(a[1], list):
                    # 嵌套 op 表达式：穿透子 args 找一级动点
                    for sa in a[1]:
                        if isinstance(sa, str):
                            act = _find(sa, {sa})
                            if act:
                                break
                    if act:
                        break
            if act:
                p_act = dynamics['params'][act]
                if p_act['type'] == 'line':
                    tmin = p_act.get('t_min', -3); tmax = p_act.get('t_max', 3)
                    tt = tmin + (tmax - tmin) * t
                    base = np.asarray(points[p_act['point']], dtype=float)
                    d = np.asarray(p_act['dir'], dtype=float)
                    act_pos = base + d * tt
                elif p_act['type'] == 'curve':
                    ci = p_act.get('curve_index', 0)
                    cv = np.asarray(curves[ci], dtype=float)
                    x = p_act['x_min'] + (p_act['x_max'] - p_act['x_min']) * t
                    act_pos = cv[int(np.argmin(np.abs(cv[:, 0] - x)))]
                else:
                    return None
                # 用 eval_op 映射：全量注入 deps 链表达式（与 compute_dynamic_extent 一致，2026-08）——
                # 否则 dep['args'] 引用的其他 deps 点（如 seg_intersect(D,E,C,F) 引用 F）会落到静态默认值上求值，采样位置错误
                pts2 = {k: np.asarray(v, dtype=float) for k, v in pts.items()}
                for dn, ddep in dynamics.get('deps', {}).items():
                    pts2[dn] = (ddep['op'], list(ddep['args']))
                pts2[act] = act_pos
                try:
                    return np.asarray(eval_op(dep['op'], dep['args'], pts2, curves), dtype=float)
                except Exception:
                    return None
        return None

    ok_all = True
    # deps 只取 points 中可见关联点（中间构造点不显示、无需覆盖校验——否则 line/curve 一级动点时
    # 中间点被距离法检查且不在任何开放图形上，误报 [FAIL]；2026-08 与 compute_dynamic_extent 同源修复）
    all_names = list(dynamics.get('active', [])) + [n for n in dynamics.get('deps', {}) if n in points]
    for name in all_names:
        p = dynamics['params'].get(name)
        if p and p['type'] in ('segment', 'circle'):
            continue  # 闭合图形
        # 动态线段端点豁免（2026-08，修复翻折点误报）：deps 点若所有连线都含动态端点
        #（另一端点 ∈ active∪deps），该点只被动态线段覆盖（线段随动点移动，静态 open_pts 采样无法验证）——豁免距离法
        if name in dynamics.get('deps', {}):
            _dyn_pts = set(dynamics.get('active', [])) | set(dynamics.get('deps', {}))
            _name_segs = [(a, b) for (a, b) in segments if name in (a, b)]
            if _name_segs and all(((a in _dyn_pts) or (b in _dyn_pts)) for (a, b) in _name_segs):
                print(f"[OK] 动态线段端点 {name}: 所有连线均含动态端点（仅由动态线段覆盖，豁免距离法）")
                continue
        # 一级 curve 动点：距离法机制失效（动点从曲线采样取位置，恒在曲线上距离=0）——
        # 改检查曲线采样 x 范围 ⊇ 动点 [x_min,x_max] + 余量（参数本质判断）
        if p and p['type'] == 'curve':
            _ci = p.get('curve_index', 0)
            if 0 <= _ci < len(curves):
                _cv = np.asarray(curves[_ci], dtype=float)
                _cx_lo, _cx_hi = float(_cv[:, 0].min()), float(_cv[:, 0].max())
                _need_lo, _need_hi = float(p['x_min']), float(p['x_max'])
                # 覆盖 = 曲线 x 范围包含动点可达范围（相等算覆盖）；浮点容差 1e-6
                if _cx_lo > _need_lo + 1e-6 or _cx_hi < _need_hi - 1e-6:
                    ok_all = False
                    print(f"[FAIL] 开放图形覆盖: 曲线动点 {name} 曲线 x 范围 [{_cx_lo:.2f},{_cx_hi:.2f}] 未包含可达范围 [{_need_lo:.2f},{_need_hi:.2f}]——请延伸曲线采样")
                else:
                    _pad = 0.1 * max(_need_hi - _need_lo, 1e-3)
                    _hint = f"（建议两端外扩约 {_pad:.2f} 便于拖拽观察）" if (_cx_lo > _need_lo - _pad or _cx_hi < _need_hi + _pad) else ""
                    print(f"[OK] 曲线动点 {name}: 曲线 x 范围 [{_cx_lo:.2f},{_cx_hi:.2f}] ⊇ 可达 [{_need_lo:.2f},{_need_hi:.2f}]{_hint}")
            else:
                ok_all = False
                print(f"[FAIL] 开放图形覆盖: 曲线动点 {name} 的 curve_index={_ci} 超出 curves 长度 {len(curves)}")
            continue
        for _k in range(6):   # 采样 6 点（含两端）覆盖可达范围
            pos = _sample_point(name, _k / 5.0)
            if pos is None:
                continue
            dmin = _nearest(pos)
            if dmin > _eps:
                ok_all = False
                print(f"[FAIL] 开放图形覆盖: 动点 {name} 采样点 ({pos[0]:.2f},{pos[1]:.2f}) 距开放图形 {dmin:.2f} > 阈值 {_eps:.2f}——开放图形（curves/segments）未覆盖其可达范围，请延伸曲线/线段")
    if ok_all:
        print("[OK] 开放图形覆盖: 全部动点（一级/二级及以上）可达范围被开放图形集覆盖")
    else:
        print("[FAIL] 开放图形覆盖: 有动点可达范围未被覆盖（见上），请修正后重跑")
    return ok_all


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
auto_label(ax, points, segments, axes=axes, curves=curves)
# 6. 可选扩展区（翻折/对称/坐标系轴等额外绘制放这里）
#    ⚠ 双渲染路径：本区为 PNG 独有（ax.plot 直绘），HTML 的 generate_html 不感知——
#      几何线条（含开放图形覆盖动点范围，如直线 BC 需覆盖关联点 Q 的可达域）必须走
#      segments/curves 数据区（PNG/HTML 共用），禁止在本区手绘承担几何表达；本区仅供装饰（直角标记等）
#    ⚠ 直角标记（可选项，硬规则 3）：用户明确要求"标直角/标垂直"时，对指定顶点调用
#      draw_right_angle_mark(ax, points['顶点'], points['顶点端另一点'], points['顶点端第三点'])
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
# [ ] 动点模式（dynamics 非空时）：HTML 含 DYNAMICS JSON（generate_html 自动嵌入，勿手写）
# [ ] 动点模式：每个一级动点（active 数组）都有对应滑块（dyn_slider_点名）与手柄（class dynpt）
# [ ] 动点模式：曲线/函数图像上的动点用 curve 类型（强制 LUT + 最近邻吸附），未映射成坐标轴辅助参数点
# [ ] 动点模式：关联点（deps）随其引用的一级动点联动（evalPoint 对 deps 永远重算，不命中缓存）
# [ ] 动点模式：直线型动点（line）拖拽沿方向向量滑动且不截断；线段型（segment）拖拽截断在 [0,1]
# [ ] 动点模式：开放图形覆盖任意层级动点可达范围——已由下方 check_open_coverage 自动校验（[OK]/[FAIL] 输出）
if dynamics:
    assert check_open_coverage(dynamics, curves, segments, points), "开放图形覆盖校验失败（见上方 [FAIL]）——延伸曲线/线段后重跑"
# [ ] 动点模式：旋转类动点（题面仅说"旋转/绕"）未画可见圆（circles 应为空，轨迹走 luts）
# [ ] 动点模式：距离约束动点（如 EF=2）未画可见圆（轨迹走 luts），且约束线段（EF）已画进 segments
# [ ] 目标线段已画：所求值表达式中的两点距离对应连线已加入 segments（即使题干没说"连接"）
# [ ] 方向已按惯例默认（四边形逆时针；右侧=dir−1、左侧=dir+1），用户可用 HTML 镜像/旋转自行调整（无需询问）
# [ ] 动点模式：points 默认位置与 Python 等价求值器一致（<1%，已打印 [OK]）
# [ ] 动点模式：关联点/动点在 segments 中合理连接，或已加入 isolated_exempt（不补连，标签保留）豁免
# [ ] 动点模式：PNG 输出默认位置静态图（可先用浏览器 HTML 验证默认态一致）
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
def generate_html(points, segments, circles, x_min, x_max, y_min, y_max, pad_x, pad_y, output_path, axes=False, xlo=0.0, xhi=0.0, ylo=0.0, yhi=0.0, curves=None, dynamics=None, dashed_segments=None):
    """生成可旋转、可镜像、可缩放的交互式 HTML 文件（多动点版）"""
    # ⚠ HTML 模板一律用 f-string 拼装：JS/CSS 中的字面 %（如 % 720 取模、+ "%"、%8）在 f-string 里是普通字符，
    #   无需转义；切勿改用 Python % 格式化（js 内嵌 % 会触发 ValueError: unsupported format character 崩溃）。
    import json
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

    pts_json = json.dumps({n: list(svg_point(p[0], p[1])) for n, p in points.items()}, ensure_ascii=False)
    # 曲线点集注入 JS（2026-08：curve 动点 LUT 缺失时的兜底数据源——JS 无法解析任意函数/访问 Python 曲线）
    curves_json = json.dumps([cv.tolist() for cv in curves] if curves else [], ensure_ascii=False)
    dynamics_json = 'null'
    if dynamics is not None:
        dynamics_json = json.dumps(dynamics, ensure_ascii=False)

    geo_elems = []
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
    if curves:
        for _cv in curves:
            if axes:
                _m = ((_cv[:, 0] >= xlo) & (_cv[:, 0] <= xhi) &
                      (_cv[:, 1] >= ylo) & (_cv[:, 1] <= yhi))
                _cv = _cv[_m]
            _pts = ' '.join(f"{svg_point(x, y)[0]:.1f},{svg_point(x, y)[1]:.1f}" for x, y in _cv)
            geo_elems.append(f'<polyline points="{_pts}" fill="none" stroke="black" stroke-width="1.5"/>')
    for (a, b) in segments:
        x1, y1 = svg_point(points[a][0], points[a][1])
        x2, y2 = svg_point(points[b][0], points[b][1])
        geo_elems.append(f'<line id="seg_{a}{b}" data-p1="{a}" data-p2="{b}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.5" stroke-linecap="round"/>')
    # 虚线（若用户要求）：与 PNG 端一致（双渲染路径，2026-08 修复——早期 generate_html 未渲染虚线）
    if dashed_segments:
        for (a, b) in dashed_segments:
            x1, y1 = svg_point(points[a][0], points[a][1])
            x2, y2 = svg_point(points[b][0], points[b][1])
            geo_elems.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="6,4"/>')

    for name, r in circles.items():
        cx_c, cy_c = svg_point(points[name][0], points[name][1])
        geo_elems.append(f'<circle id="cir_{name}" data-center="{name}" cx="{cx_c:.1f}" cy="{cy_c:.1f}" r="{r * scale:.1f}" fill="none" stroke="black" stroke-width="1.5"/>')

    for name, p in points.items():
        px, py = svg_point(p[0], p[1])
        cls = 'pt'
        if dynamics is not None and name in dynamics['active']:
            cls += ' dynpt'
        geo_elems.append(f'<circle class="{cls}" id="pt_{name}" data-name="{name}" cx="{px:.1f}" cy="{py:.1f}" r="2.2" fill="black" stroke="none"/>')

    label_elems = []
    for _li, (name, p) in enumerate(points.items()):   # id 用序号（点名含撇号 B' 等不可拼进 id，防 HTML 属性破裂）；点名存 data-name
        if name in label_exempt:
            continue  # label_exempt 辅助点 HTML 标签不生成（2026-08 语义分离；点标记保留）
        # 仅跳过恰在原点的 O（坐标轴代码已在原点标 O）；非原点的 O 点仍标注（与 PNG auto_label 一致）
        if axes and name == 'O' and np.allclose(p, [0.0, 0.0]):
            continue
        px, py = svg_point(p[0], p[1])
        label_elems.append(f'<text class="lab" id="lab_{_li}" data-name="{name}" x="0" y="0" data-lx="{px:.1f}" data-ly="{py:.1f}" data-pos="0" text-anchor="middle" dominant-baseline="central" font-size="{_fs}" fill="black" font-family="Times New Roman, serif" font-style="italic" style="cursor:pointer" onclick="clickLabel(this)">{name}</text>')

    # 直角标记（可选）：dynamics.right_angle_marks，仅用户明确要求标直角时非空；坐标由 JS init 填充
    ramark_elems = ''
    if dynamics is not None and dynamics.get('right_angle_marks'):
        parts = []
        for _m in dynamics['right_angle_marks']:
            parts.append(f'<g class="ramark" data-v="{_m[0]}" data-a="{_m[1]}" data-b="{_m[2]}">'
                         f'<line class="rm1" stroke="black" stroke-width="1.5"/>'
                         f'<line class="rm2" stroke="black" stroke-width="1.5"/></g>')
        ramark_elems = ''.join(parts)

    # 多动点 UI：每个动点一个滑块
    dyn_ui = ''
    if dynamics is not None:
        dyn_ui = '<button id="adj_btn" onclick="toggleAdjust()">进入调整模式</button>'
        for _n in dynamics['active']:
            _p = dynamics['params'][_n]
            if _p['type'] == 'segment':
                dyn_ui += (f'<label>{_n}: <input id="dyn_slider_{_n}" type="range" min="0" max="100" value="{_p["t"]*100:.0f}" oninput="setDynParam(\'{_n}\',this.value)" style="width:90px"> '
                           f'<span id="dyn_slider_val_{_n}">{_p["t"]:.2f}</span></label>')
            elif _p['type'] == 'line':
                dyn_ui += (f'<label>{_n}: <input id="dyn_slider_{_n}" type="range" min="{(_p.get("t_min", -3))*100:.0f}" max="{(_p.get("t_max", 3))*100:.0f}" value="{_p["t"]*100:.0f}" oninput="setDynParam(\'{_n}\',this.value)" style="width:90px"> '
                           f'<span id="dyn_slider_val_{_n}">{_p["t"]:.2f}</span></label>')
            elif _p['type'] == 'curve':
                dyn_ui += (f'<label>{_n}: <input id="dyn_slider_{_n}" type="range" min="0" max="100" value="{(_p["x"]-_p["x_min"])/(_p["x_max"]-_p["x_min"])*100:.0f}" oninput="setDynParam(\'{_n}\',this.value)" style="width:90px"> '
                           f'<span id="dyn_slider_val_{_n}">{_p["x"]:.2f}</span></label>')
            else:
                dyn_ui += (f'<label>{_n}: <input id="dyn_slider_{_n}" type="range" min="{(_p.get("theta_min", 0))*180/math.pi:.0f}" max="{(_p.get("theta_max", 2*math.pi))*180/math.pi:.0f}" value="{_p["theta"]*180/math.pi:.0f}" oninput="setDynParam(\'{_n}\',this.value)" style="width:90px"> '
                           f'<span id="dyn_slider_val_{_n}">{_p["theta"]*180/math.pi:.0f}°</span></label>')

    dyn_ui += '<label><input type="checkbox" id="traj_cb" checked onchange="toggleTrajectory()"> 显示轨迹</label>   <!-- 默认勾选：HTML 打开即呈现隐藏轨迹（2026-08，防 agent 未勾选/未生成时轨迹不可见） -->'

    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Geometry Sketch</title>
<style>
  body{{margin:0;display:flex;flex-direction:column;align-items:center;background:#eee;font-family:sans-serif;}}
  #toolbar{{margin:10px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;position:sticky;top:0;z-index:10;background:#eee;padding:8px;border-bottom:1px solid #ccc;}}
  button{{padding:2px 8px;cursor:pointer;}}
  #main_svg{{border:1px solid #ccc;background:#fff;}}
  #dyn_readouts{{margin:6px;font:13px Consolas,monospace;color:#333;display:none;}}
  .dynpt{{cursor:grab;}}
  .dynpt.active{{fill:#fff;stroke:#000;stroke-width:1.5;cursor:grabbing;}}
  .locked #view_controls{{opacity:.45;pointer-events:none;}}
</style></head>
<body onload="init()">
<div id="toolbar">
  {dyn_ui}
  <span id="view_controls">
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
  </span>
  <button onclick="savePNG()" style="font-weight:bold">保存为 PNG</button>
</div>
<div id="dyn_readouts"></div>
<svg id="main_svg" viewBox="0 0 {vw:.0f} {vh:.0f}" xmlns="http://www.w3.org/2000/svg">
  <rect id="capture_box" x="0" y="0" width="{vw:.0f}" height="{vh:.0f}" fill="none" stroke="#999" stroke-dasharray="8,4" stroke-width="1"/>
  <defs>
    <marker id="arrowh" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="black"/></marker>
    <marker id="arrowv" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="black"/></marker>
  </defs>
  <g id="geo_group" transform="translate({cx:.1f},{cy:.1f}) rotate(0) scale(1,1) translate({-cx:.1f},{-cy:.1f})">
    <g id="traj_group" style="display:none"></g>
    {ramark_elems}
    {''.join(geo_elems)}
  </g>
  <g id="label_group">
    {''.join(label_elems)}
  </g>
</svg>
<script>
let h_flip=1, v_flip=1, panX=0;   // 左右平移（最外层，与旋转/镜像正交）
const OFFSETS = [[12,-12],[-12,-12],[-12,12],[12,12],[0,-12],[0,12],[-12,0],[12,0]];  // 前4对角 + 后4上下左右（8方位）
const FS = {_fs};   // 标注字号（随画布宽度缩放，2026-08）：偏移因子 = FS/14
const DYNAMICS = {dynamics_json};
const PTS0 = {pts_json};
const CURVES = {curves_json};   // 曲线点集（Python 采样注入，curve 动点 LUT 缺失时的兜底数据源）
const GEO = {{
  cx: {cx:.1f}, cy: {cy:.1f},
  scale: {scale:.6f}, off_x: {off_x:.6f}, off_y: {off_y:.6f},
  x_min: {x_min:.6f}, x_max: {x_max:.6f}, y_min: {y_min:.6f}, y_max: {y_max:.6f},
}};
function svgToData(sx, sy) {{
  return [GEO.off_x + sx / GEO.scale, GEO.off_y - sy / GEO.scale];
}}
function dataToSvg(x, y) {{
  return [(x - GEO.off_x) * GEO.scale, (GEO.off_y - y) * GEO.scale];
}}
let currentPos = {{}};
Object.keys(PTS0).forEach(n => {{
  currentPos[n] = svgToData(PTS0[n][0], PTS0[n][1]);
}});
let adjustMode = false;

// ---- 求值器（多动点：params 字典 + line 类型 + translate op） ----
const OP = {{
  symmetry: (c, p) => [2*c[0]-p[0], 2*c[1]-p[1]],
  reflect: (p, a, b) => {{
    const ab = [b[0]-a[0], b[1]-a[1]];
    const t = ((p[0]-a[0])*ab[0] + (p[1]-a[1])*ab[1]) / (ab[0]*ab[0]+ab[1]*ab[1]);
    const h = [a[0]+t*ab[0], a[1]+t*ab[1]];
    return [2*h[0]-p[0], 2*h[1]-p[1]];
  }},
  midpoint: (a, b) => [(a[0]+b[0])/2, (a[1]+b[1])/2],
  ratio_point: (a, b, r) => [(a[0]+r*b[0])/(1+r), (a[1]+r*b[1])/(1+r)],
  point_on_circle: (c, rr, th) => [c[0]+rr*Math.cos(th), c[1]+rr*Math.sin(th)],
  point_on_segment: (a, b, t) => [a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])],
  square_vertex: (a, b, dir) => [b[0]-dir*(b[1]-a[1]), b[1]+dir*(b[0]-a[0])],
  translate: (p, d) => [p[0]+d[0], p[1]+d[1]],
  line_through_intersect: (p, dir, a, b) => {{
    // 过 p 沿 dir 作直线与直线 ab 的交点（叉积；平行 → NaN，与 Python eval_op 同语义）
    const abx = b[0]-a[0], aby = b[1]-a[1];
    const denom = dir[0]*aby - dir[1]*abx;
    if (Math.abs(denom) < 1e-9) return [NaN, NaN];
    const s = ((a[0]-p[0])*aby - (a[1]-p[1])*abx) / denom;
    return [p[0] + s*dir[0], p[1] + s*dir[1]];
  }},
  // seg_intersect: 直线 ab 与直线 cd 的交点（扩展 op 2026-08，与 Python eval_op 同语义；叉积，平行 → NaN）
  seg_intersect: (a,b,c,d) => {{
    const rx = b[0]-a[0], ry = b[1]-a[1];
    const sx = d[0]-c[0], sy = d[1]-c[1];
    const denom = rx*sy - ry*sx;
    if (Math.abs(denom) < 1e-9) return [NaN, NaN];
    const t = ((c[0]-a[0])*sy - (c[1]-a[1])*sx) / denom;
    return [a[0] + t*rx, a[1] + t*ry];
  }},
  // circle_line_x: 圆 (c, r=dist(c,o)) 与水平线 y 的交点（扩展 op 2026-08，与 Python eval_op 同语义；sd=+1 右 / -1 左）
  circle_line_x: (c, o, y, sd) => {{
    const r = Math.hypot(c[0]-o[0], c[1]-o[1]);
    const dy = y - c[1];
    if (Math.abs(dy) > r + 1e-9) return [NaN, NaN];
    const dx = Math.sqrt(Math.max(0, r*r - dy*dy));
    return [c[0] + sd*dx, y];
  }},
  // rotate: 点 p 绕中心 c 逆时针旋转 deg 度（弧度换算统一在内部；cw90/ccw90 复用同一数学防符号偏差）
  rotate: (p, c, deg) => {{
    const rad = deg * Math.PI / 180;
    const cos = Math.cos(rad), sin = Math.sin(rad);
    const dx = p[0]-c[0], dy = p[1]-c[1];
    return [c[0] + dx*cos - dy*sin, c[1] + dx*sin + dy*cos];
  }},
  rotate_cw90: (p, c) => {{
    const dx = p[0]-c[0], dy = p[1]-c[1];
    return [c[0] + dy, c[1] - dx];
  }},
  rotate_ccw90: (p, c) => {{
    const dx = p[0]-c[0], dy = p[1]-c[1];
    return [c[0] - dy, c[1] + dx];
  }},
  curve_at: (ci, xs) => {{
    // 曲线采样上 x 处点（线性插值 2026-08：轴上动点→曲线上关联点派生；CURVES 为 generate_html 注入的曲线点集）
    const cv = (typeof CURVES !== 'undefined' && CURVES[ci]) ? CURVES[ci] : null;
    if (!cv || cv.length < 2) return [NaN, NaN];
    const x = (typeof xs === 'number') ? xs : xs[0];   // 点名求值后是坐标 → 取 x 分量
    if (x <= cv[0][0]) return [cv[0][0], cv[0][1]];
    if (x >= cv[cv.length-1][0]) return [cv[cv.length-1][0], cv[cv.length-1][1]];
    let k = 0;
    while (k < cv.length-2 && cv[k+1][0] < x) k++;
    const x0 = cv[k][0], y0 = cv[k][1], x1 = cv[k+1][0], y1 = cv[k+1][1];
    const t = (x1 > x0) ? (x - x0)/(x1 - x0) : 0;
    return [x, y0 + t*(y1 - y0)];
  }},
}};

function paramPoint(name) {{
  const p = DYNAMICS.params[name];
  if (p.type === 'circle') return OP.point_on_circle(currentPos[p.center], p.radius, p.theta);
  if (p.type === 'segment') return OP.point_on_segment(currentPos[p.a], currentPos[p.b], p.t);
  if (p.type === 'curve') {{
    const lut = DYNAMICS.luts && DYNAMICS.luts[name];
    if (!lut) {{
      // LUT 缺失兜底：查注入的 CURVES 点集（2026-08，曲线点由 Python 采样注入；无 LUT 位置计算也保持可用）
      const cv = (typeof CURVES !== 'undefined' && CURVES[p.curve_index]) ? CURVES[p.curve_index] : null;
      if (!cv || !cv.length) return currentPos[name];
      let bi = 0, bd = Infinity;
      for (let k = 0; k < cv.length; k++) {{
        const dx = p.x - cv[k][0];
        const dd = dx * dx;
        if (dd < bd) {{ bd = dd; bi = k; }}
      }}
      return cv[bi];
    }}
    const n = lut.length - 1;
    const i = Math.max(0, Math.min(n, Math.round((p.x - p.x_min) / (p.x_max - p.x_min) * n)));
    return lut[i];
  }}
  return [currentPos[p.point][0] + p.dir[0]*p.t, currentPos[p.point][1] + p.dir[1]*p.t];  // line
}}

function evalArg(a) {{
  // 嵌套 op 表达式：["op名", [子args...]]（与 Python eval_arg 的 ('op',[args]) 同语义，2026-08 JS 端对齐）
  // 判定用 OP 查表：坐标/向量字面量如 [0,4] 首元素是数字不触发；未知 op 名/子参数非数组显式报错（对齐 Python eval_op 抛错）
  if (Array.isArray(a) && a.length === 2 && typeof a[0] === 'string') {{
    if (!OP[a[0]]) {{
      console.error('evalArg: 未知 op: ' + a[0]);
      return [NaN, NaN];
    }}
    if (!Array.isArray(a[1])) {{
      console.error('evalArg: op 表达式子参数非数组: ' + JSON.stringify(a));
      return [NaN, NaN];
    }}
    return OP[a[0]](...a[1].map(x => evalArg(x)));
  }}
  if (Array.isArray(a)) return a;        // 坐标/向量字面量
  if (typeof a === 'number') return a;   // 数值字面量
  return evalPoint(a);                   // 点名（一级动点/其他 deps/静态点）
}}

function evalPoint(name) {{
  // deps 点永远重算（currentPos 初始化已含全部点，不能命中缓存短路）；静态/动点读 currentPos
  if (DYNAMICS.deps[name]) {{
    const dep = DYNAMICS.deps[name];
    const args = dep.args.map(a => evalArg(a));
    return OP[dep.op](...args);
  }}
  return currentPos[name];
}}

function lookupOrEval(name) {{
  const lut = DYNAMICS.luts && DYNAMICS.luts[name];
  if (lut) {{
    const p = DYNAMICS.params[name];
    if (p) {{
      let i;
      if (p.type === 'circle') {{ i = Math.round(p.theta * 360 / Math.PI) % 720; if (i < 0) i += 720; }}
      else if (p.type === 'segment') {{ i = Math.round(p.t * 100); if (i > 100) i = 100; }}
      else return evalPoint(name);
      const v = lut[i];
      if (v) return v;
    }}
  }}
  return evalPoint(name);
}}

function recomputeAll() {{
  if (!DYNAMICS) return;
  DYNAMICS.active.forEach(name => {{
    currentPos[name] = paramPoint(name);
  }});
  Object.keys(DYNAMICS.deps).forEach(n => {{
    currentPos[n] = lookupOrEval(n);
  }});
  updateReadouts();
  updateGeo();
}}

// ---- 视图更新 ----
function update() {{
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
  placeLabels();
}}

function placeLabels() {{
  let r=parseFloat(document.getElementById("rot").value);
  let s=parseInt(document.getElementById("scale_slider").value)/100;
  let d=parseFloat(document.getElementById("ldist").value);
  let rad=r*Math.PI/180, cos=Math.cos(rad), sin=Math.sin(rad);
  document.querySelectorAll(".lab").forEach(t=>{{
    let name = t.dataset.name;   // 点名存 data-name（id 为序号 lab_序号，含撇号点名 B' 不再经 id 提取，防属性破裂）
    let p = currentPos[name] || [0,0];
    let lx = (p[0]-GEO.off_x)*GEO.scale;
    let ly = (GEO.off_y - p[1])*GEO.scale;
    let dx=lx-GEO.cx, dy=ly-GEO.cy;
    let rx=dx*cos - dy*sin, ry=dx*sin + dy*cos;
    rx*=s*h_flip; ry*=s*v_flip;
    let off = OFFSETS[parseInt(t.dataset.pos)];
    let k = d * FS / 196;   // 标注距离×字号缩放合并式（避免同行多除号被静态检查正则误判，2026-08）
    t.setAttribute("x",GEO.cx+panX+rx+off[0]*k*h_flip); t.setAttribute("y",GEO.cy+ry+off[1]*k*v_flip);
  }});
}}

function updateGeo() {{
  document.querySelectorAll(".pt").forEach(el => {{
    let name = el.dataset.name;
    let p = currentPos[name];
    if (!p) return;
    let s = dataToSvg(p[0], p[1]);
    el.setAttribute("cx", s[0]); el.setAttribute("cy", s[1]);
  }});
  document.querySelectorAll("line[data-p1]").forEach(el => {{
    let a = currentPos[el.dataset.p1], b = currentPos[el.dataset.p2];
    if (!a || !b) return;
    let s1 = dataToSvg(a[0], a[1]), s2 = dataToSvg(b[0], b[1]);
    el.setAttribute("x1", s1[0]); el.setAttribute("y1", s1[1]);
    el.setAttribute("x2", s2[0]); el.setAttribute("y2", s2[1]);
  }});
  document.querySelectorAll("circle[data-center]").forEach(el => {{
    let c = currentPos[el.dataset.center];
    if (!c) return;
    let s = dataToSvg(c[0], c[1]);
    el.setAttribute("cx", s[0]); el.setAttribute("cy", s[1]);
  }});
  // 直角标记（可选）：顶点处小方块，随动点实时跟随（两条边平行于 va/vb）
  document.querySelectorAll(".ramark").forEach(g => {{
    const v = currentPos[g.dataset.v], a = currentPos[g.dataset.a], b = currentPos[g.dataset.b];
    if (!v || !a || !b) return;
    let u1 = [a[0]-v[0], a[1]-v[1]], u2 = [b[0]-v[0], b[1]-v[1]];
    const n1 = Math.hypot(u1[0], u1[1]), n2 = Math.hypot(u2[0], u2[1]);
    if (n1 < 1e-9 || n2 < 1e-9) return;
    u1 = [u1[0]/n1, u1[1]/n1]; u2 = [u2[0]/n2, u2[1]/n2];
    // 大小 clamp：基准 = 图形跨度；0.1×短边 但限制在 [0.8%, 1.7%] 跨度（防动点拖远后标记巨大 / 拖近后消失；上限 2026-08 由 3% 逐次收紧到 1.7%）
    const geoSpan = Math.max(GEO.x_max - GEO.x_min, GEO.y_max - GEO.y_min);
    const size = Math.max(0.008 * geoSpan, Math.min(0.017 * geoSpan, 0.1 * Math.min(n1, n2)));
    const p1 = [v[0]+u1[0]*size, v[1]+u1[1]*size];
    const p2 = [v[0]+u2[0]*size, v[1]+u2[1]*size];
    const p3 = [v[0]+(u1[0]+u2[0])*size, v[1]+(u1[1]+u2[1])*size];
    const s1 = dataToSvg(p1[0], p1[1]), s2 = dataToSvg(p2[0], p2[1]), s3 = dataToSvg(p3[0], p3[1]);
    g.querySelector('.rm1').setAttribute('x1', s1[0]); g.querySelector('.rm1').setAttribute('y1', s1[1]);
    g.querySelector('.rm1').setAttribute('x2', s3[0]); g.querySelector('.rm1').setAttribute('y2', s3[1]);
    g.querySelector('.rm2').setAttribute('x1', s2[0]); g.querySelector('.rm2').setAttribute('y1', s2[1]);
    g.querySelector('.rm2').setAttribute('x2', s3[0]); g.querySelector('.rm2').setAttribute('y2', s3[1]);
  }});
  placeLabels();
}}

function clickLabel(el){{
  el.dataset.pos = (parseInt(el.dataset.pos)+1)%8;
  placeLabels();
}}
function setRot(v){{
  document.getElementById("rot").value=v;
  update();
}}
function flip(dir){{
  if(dir=="h") h_flip*=-1; else v_flip*=-1;
  update();
}}

// ---- 多动点交互 ----
function setDynParam(name, v) {{
  const p = DYNAMICS.params[name];
  const val = parseFloat(v);
  if (p.type === 'circle') p.theta = val * Math.PI / 180;
  else if (p.type === 'curve') p.x = p.x_min + (p.x_max - p.x_min) * val / 100;
  else p.t = val / 100;
  updateSliderVal(name);
  recomputeAll();
}}

function updateSliderVal(name) {{
  const p = DYNAMICS.params[name];
  const el = document.getElementById('dyn_slider_val_' + name);
  if (p.type === 'circle') el.textContent = Math.round(p.theta*180/Math.PI) + '°';
  else if (p.type === 'curve') el.textContent = p.x.toFixed(2);
  else el.textContent = p.t.toFixed(2);
}}

// 沿 deps 引用链找第一个被引用的一级动点（BFS：先直接引用、再递归 deps 链）
function findDepActive(name, seen) {{
  const dep = DYNAMICS.deps[name];
  if (!dep) return null;
  for (const a of dep.args) {{
    if (typeof a === 'string' && DYNAMICS.active.indexOf(a) >= 0) return a;
  }}
  for (const a of dep.args) {{
    if (typeof a !== 'string' || seen[a]) continue;
    seen[a] = true;
    const r = findDepActive(a, seen);
    if (r) return r;
  }}
  return null;
}}
function buildTrajectory() {{
  if (!DYNAMICS) return;
  const g = document.getElementById("traj_group");
  g.innerHTML = '';
  const names = (DYNAMICS.trajectory && DYNAMICS.trajectory.length) ? DYNAMICS.trajectory : DYNAMICS.active.slice();
  const luts = DYNAMICS.luts || {{}};
  names.forEach(name => {{
    let pts = null;
    if (luts[name]) {{
      pts = luts[name];
    }} else if (DYNAMICS.deps[name]) {{
      // 关联点（deps）无 LUT：沿其依赖的一级动点参数采样，用 evalPoint 实时算轨迹
      const depActive = findDepActive(name, {{}});
      if (depActive) {{
        const p = DYNAMICS.params[depActive];
        const arr = [];
        const save = (p.type === 'circle') ? p.theta : ((p.type === 'curve') ? p.x : p.t);  // 采样前保存参数原值，供恢复行使用
        const pushAt = () => {{
          currentPos[depActive] = paramPoint(depActive);
          const v = evalPoint(name);
          arr.push([v[0], v[1]]);
        }};
        if (p.type === 'circle') {{
          const tmin = (p.theta_min !== undefined) ? p.theta_min : 0;
          const tmax = (p.theta_max !== undefined) ? p.theta_max : 2*Math.PI;
          for (let k = 0; k <= 360; k++) {{ p.theta = tmin + (tmax-tmin)*k/360; pushAt(); }}
        }} else if (p.type === 'segment') {{
          for (let k = 0; k <= 100; k++) {{ p.t = k/100; pushAt(); }}
        }} else if (p.type === 'line') {{
          const tmin = (p.t_min !== undefined) ? p.t_min : -3;
          const tmax = (p.t_max !== undefined) ? p.t_max : 3;
          for (let k = 0; k <= 60; k++) {{ p.t = tmin + (tmax-tmin)*k/60; pushAt(); }}
        }} else if (p.type === 'curve') {{
          const n = (DYNAMICS.luts && DYNAMICS.luts[depActive]) ? DYNAMICS.luts[depActive].length - 1 : 200;
          for (let k = 0; k <= n; k++) {{ p.x = p.x_min + (p.x_max - p.x_min)*k/n; pushAt(); }}
        }}
        // 采样后恢复参数与位置，避免污染滑块/画面（2026-08 修复）
        if (p.type === 'circle') p.theta = save; else if (p.type === 'curve') p.x = save; else p.t = save;
        currentPos[depActive] = paramPoint(depActive);
        Object.keys(DYNAMICS.deps).forEach(n2 => {{ currentPos[n2] = lookupOrEval(n2); }});
        pts = arr;
      }}
    }} else if (DYNAMICS.params[name]) {{
      const p = DYNAMICS.params[name];
      const arr = [];
      if (p.type === 'circle') {{
        const tmin = (p.theta_min !== undefined) ? p.theta_min : 0;
        const tmax = (p.theta_max !== undefined) ? p.theta_max : 2*Math.PI;
        for (let k = 0; k <= 360; k++) arr.push(OP.point_on_circle(currentPos[p.center], p.radius, tmin + (tmax-tmin)*k/360));
      }} else if (p.type === 'segment') {{
        for (let k = 0; k <= 100; k++) arr.push(OP.point_on_segment(currentPos[p.a], currentPos[p.b], k/100));
      }} else if (p.type === 'line') {{
        const tmin = (p.t_min !== undefined) ? p.t_min : -3;
        const tmax = (p.t_max !== undefined) ? p.t_max : 3;
        for (let k = 0; k <= 60; k++) arr.push([currentPos[p.point][0] + p.dir[0]*(tmin+(tmax-tmin)*k/60), currentPos[p.point][1] + p.dir[1]*(tmin+(tmax-tmin)*k/60)]);
      }} else if (p.type === 'curve') {{
        // 曲线一级动点：优先 LUT（规范强制）；LUT 缺失时沿 x 采样 paramPoint 兜底（2026-08：缺失即跳过会导致轨迹不画）
        if (luts[name]) {{
          pts = luts[name];
        }} else if (typeof CURVES !== 'undefined' && CURVES[p.curve_index] && CURVES[p.curve_index].length) {{
          const n = 200;
          const saveX = p.x;
          for (let k = 0; k <= n; k++) {{
            p.x = p.x_min + (p.x_max - p.x_min) * k / n;
            arr.push(paramPoint(name));
          }}
          p.x = saveX;
        }}
      }}
      if (!pts) pts = arr;
    }}
    if (!pts || !pts.length) return;
    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    poly.setAttribute('points', pts.map(pt => {{ const sv = dataToSvg(pt[0], pt[1]); return sv[0].toFixed(1)+','+sv[1].toFixed(1); }}).join(' '));
    poly.setAttribute('fill', 'none'); poly.setAttribute('stroke', 'black');
    poly.setAttribute('stroke-width', '1'); poly.setAttribute('stroke-dasharray', '4,3');
    g.appendChild(poly);
  }});
}}
function toggleTrajectory() {{
  const g = document.getElementById("traj_group");
  const on = document.getElementById("traj_cb").checked;
  if (on) buildTrajectory();
  g.style.display = on ? 'inline' : 'none';
}}
function toggleAdjust() {{
  adjustMode = !adjustMode;
  document.getElementById("adj_btn").textContent = adjustMode ? "退出调整模式" : "进入调整模式";
  document.body.classList.toggle("locked", adjustMode);
  document.querySelectorAll(".dynpt").forEach(el => el.classList.toggle("active", adjustMode));
  document.getElementById("dyn_readouts").style.display = adjustMode ? 'block' : 'none';
}}

function evalLinearExpr(expr, p) {{
  const m = expr.match(/^\\s*([+-]?\\d*\\.?\\d*)\\s*\\*\\s*p\\[0\\]\\s*([+-]\\s*\\d*\\.?\\d*)\\s*\\*\\s*p\\[1\\]\\s*([+-]\\s*\\d*\\.?\\d*)?\\s*$/);
  if (!m) return null;
  const a = (m[1] === '' || m[1] === '+') ? 1 : (m[1] === '-' ? -1 : parseFloat(m[1]));
  const b = parseFloat(m[2].replace(/\\s+/g, ''));
  const c = m[3] ? parseFloat(m[3].replace(/\\s+/g, '')) : 0;
  return a*p[0] + b*p[1] + c;
}}
function sprintfFmt(fmt, x, y) {{
  const m = fmt.match(/\\.(\\d+)f/);
  const prec = m ? parseInt(m[1]) : 2;
  const vals = [x, y]; let i = 0;
  return fmt.replace(/%.?\\d*f/g, () => vals[i++].toFixed(prec));
}}
function updateReadouts() {{
  if (!DYNAMICS || !adjustMode) return;
  const parts = [];
  DYNAMICS.active.forEach(name => {{
    const p = DYNAMICS.params[name];
    if (p.type === 'circle') parts.push(name + '=' + (p.theta*180/Math.PI).toFixed(1) + '°');
    else if (p.type === 'curve') parts.push(name + '=x' + p.x.toFixed(2));
    else parts.push(name + '=t' + p.t.toFixed(2));
  }});
  // 自定义 readouts：expr='p' 输出第一个关联点坐标；线性表达式求值（如目标式/距离）
  const depNames = Object.keys(DYNAMICS.deps || {{}});
  if (DYNAMICS.readouts && depNames.length) {{
    const P = currentPos[depNames[0]];
    DYNAMICS.readouts.forEach(ro => {{
      if (ro.expr === 'p') {{
        parts.push(ro.label + '=' + sprintfFmt(ro.fmt || '(%.2f, %.2f)', P[0], P[1]));
      }} else {{
        const v = evalLinearExpr(ro.expr, P);
        if (v !== null) parts.push(ro.label + '=' + sprintfFmt(ro.fmt || '%.2f', v));
      }}
    }});
  }}
  document.getElementById("dyn_readouts").textContent = parts.join('   ');
}}

// ---- 拖拽（多动点：line 投影 clamp 到 [t_min,t_max]，与滑块两端一致） ----
const svgEl = document.getElementById("main_svg");
let dragging = null;

function getScreenPos(ev) {{
  const ctm = svgEl.getScreenCTM();
  const pt = svgEl.createSVGPoint();
  const client = ev.touches ? ev.touches[0] : ev;
  pt.x = client.clientX; pt.y = client.clientY;
  const sp = pt.matrixTransform(ctm.inverse());
  return [sp.x, sp.y];
}}

function screenToData(sx, sy) {{
  const r = parseFloat(document.getElementById("rot").value) * Math.PI / 180;
  const s = parseInt(document.getElementById("scale_slider").value) / 100;
  let x = (sx - (GEO.cx+panX)) / (s*h_flip), y = (sy - GEO.cy) / (s*v_flip);   // 平移补偿：拖拽不随图形平移错位
  let xr = x*Math.cos(-r) - y*Math.sin(-r), yr = x*Math.sin(-r) + y*Math.cos(-r);
  return svgToData(xr + GEO.cx, yr + GEO.cy);
}}

function dragMove(dp, name) {{
  const p = DYNAMICS.params[name];
  if (p.type === 'circle') {{
    const c = currentPos[p.center];
    let th = Math.atan2(dp[1]-c[1], dp[0]-c[0]);
    if (th < 0) th += 2*Math.PI;
    const tmin = (p.theta_min !== undefined) ? p.theta_min : 0;
    const tmax = (p.theta_max !== undefined) ? p.theta_max : 2*Math.PI;
    p.theta = Math.max(tmin, Math.min(tmax, th));
  }} else if (p.type === 'segment') {{
    const a = currentPos[p.a], b = currentPos[p.b];
    const ab = [b[0]-a[0], b[1]-a[1]];
    const t = ((dp[0]-a[0])*ab[0] + (dp[1]-a[1])*ab[1]) / (ab[0]*ab[0]+ab[1]*ab[1]);
    p.t = Math.max(0, Math.min(1, t));
  }} else if (p.type === 'curve') {{
    // 曲线拖拽 = 鼠标位置到 LUT 最近邻吸附，点始终在曲线上（LUT 缺失时查注入 CURVES 兜底，2026-08）
    const lut = DYNAMICS.luts && DYNAMICS.luts[name];
    const snap = (lut && lut.length) ? lut : ((typeof CURVES !== 'undefined' && CURVES[p.curve_index]) ? CURVES[p.curve_index] : null);
    if (snap && snap.length) {{
      let bi = 0, bd = Infinity;
      for (let k = 0; k < snap.length; k++) {{
        const dx = dp[0]-snap[k][0], dy = dp[1]-snap[k][1];
        const dd = dx*dx + dy*dy;
        if (dd < bd) {{ bd = dd; bi = k; }}
      }}
      if (lut && lut.length) {{
        p.x = p.x_min + (p.x_max - p.x_min) * bi / (lut.length - 1);
      }} else {{
        p.x = snap[bi][0];
      }}
    }}
  }} else {{
    const base = currentPos[p.point];
    const d = p.dir;
    const t = ((dp[0]-base[0])*d[0] + (dp[1]-base[1])*d[1]) / (d[0]*d[0]+d[1]*d[1]);
    const tmin = (p.t_min !== undefined) ? p.t_min : -3;
    const tmax = (p.t_max !== undefined) ? p.t_max : 3;
    p.t = Math.max(tmin, Math.min(tmax, t));
  }}
  const el = document.getElementById('dyn_slider_' + name);
  let sv;
  if (p.type === 'circle') sv = p.theta*180/Math.PI;
  else if (p.type === 'curve') sv = (p.x - p.x_min) / (p.x_max - p.x_min) * 100;
  else sv = p.t*100;
  el.value = Math.round(sv);
  updateSliderVal(name);
  recomputeAll();
}}

let rafPending = false;
let pendingData = null;
svgEl.addEventListener('mousedown', e => {{
  if (!adjustMode || !DYNAMICS) return;
  const target = e.target;
  if (!target.classList || !target.classList.contains('dynpt')) return;
  e.preventDefault();
  dragging = target.dataset.name;
  target.classList.add('active');
}});
svgEl.addEventListener('mousemove', e => {{
  if (!dragging) return;
  const sp = getScreenPos(e);
  pendingData = [screenToData(sp[0], sp[1]), dragging];
  if (!rafPending) {{
    rafPending = true;
    requestAnimationFrame(() => {{
      rafPending = false;
      if (pendingData) dragMove(pendingData[0], pendingData[1]);
      pendingData = null;
    }});
  }}
}});
window.addEventListener('mouseup', () => {{
  if (dragging) {{
    document.querySelectorAll('.dynpt').forEach(el => el.classList.remove('active'));
    dragging = null;
  }}
}});
svgEl.addEventListener('touchstart', e => {{
  if (!adjustMode || !DYNAMICS) return;
  const t = e.touches[0];
  const el = document.elementFromPoint(t.clientX, t.clientY);
  if (el && el.classList && el.classList.contains('dynpt')) {{
    e.preventDefault();
    dragging = el.dataset.name;
    el.classList.add('active');
  }}
}}, {{passive:false}});
svgEl.addEventListener('touchmove', e => {{
  if (!dragging) return;
  e.preventDefault();
  const sp = getScreenPos(e);
  pendingData = [screenToData(sp[0], sp[1]), dragging];
  if (!rafPending) {{
    rafPending = true;
    requestAnimationFrame(() => {{
      rafPending = false;
      if (pendingData) dragMove(pendingData[0], pendingData[1]);
      pendingData = null;
    }});
  }}
}}, {{passive:false}});
window.addEventListener('touchend', () => {{
  if (dragging) {{
    document.querySelectorAll('.dynpt').forEach(el => el.classList.remove('active'));
    dragging = null;
  }}
}});

function init() {{
  update();
  recomputeAll();
  // 默认呈现隐藏轨迹（2026-08）：traj_cb 默认勾选，onload 即构建并显示，不依赖用户/agent 操作
  if (document.getElementById("traj_cb").checked) {{
    buildTrajectory();
    document.getElementById("traj_group").style.display = 'inline';
  }}
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
    generate_html(points, segments, circles, x_min, x_max, y_min, y_max, pad_x, pad_y, html_path, axes, _xlo, _xhi, _ylo, _yhi, curves, dynamics, dashed_segments)
else:
    generate_html(points, segments, circles, x_min, x_max, y_min, y_max, pad_x, pad_y, html_path, axes, curves=curves, dynamics=dynamics, dashed_segments=dashed_segments)
print(f"HTML 已保存至: {html_path}")

plt.close()
print("绘图完成。")

