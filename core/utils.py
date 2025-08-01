import os
import ezdxf
import io
import math
import numpy as np
from decimal import Decimal
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.math import Bezier, BSpline


matplotlib.use("Agg")


@shared_task
def generate_preview_background(drawing_id, drawing_path):
    try:
        if not drawing_path.endswith(".dxf"):
            return

        preview = generate_dxf_preview(drawing_path)
        if preview:
            preview_filename = f"previews/preview_{drawing_id}.png"
            if default_storage.exists(preview_filename):
                default_storage.delete(preview_filename)
            default_storage.save(preview_filename, preview)
    except Exception as e:
        print(f"[ПОМИЛКА] Помилка генерації прев'ю: {e}")


def get_dxf_layers(dxf_path: str) -> list[str]:
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        return sorted({entity.dxf.layer for entity in msp})
    except Exception as e:
        print(f"[ПОМИЛКА] Не вдалося отримати шари: {e}")
        return []


def extract_entities(dxf_path: str, layer_name: str):
    try:
        doc = ezdxf.readfile(dxf_path)
        return [entity for entity in doc.modelspace() if entity.dxf.layer == layer_name]
    except Exception as e:
        print(f"[ПОМИЛКА] Помилка вилучення об'єктів: {e}")
        return []


def spline_to_lines(spline, segments=100):
    try:
        if hasattr(spline, "fit_points") and spline.fit_points:
            points = np.array([(p[0], p[1]) for p in spline.fit_points])
            t = np.linspace(0, 1, segments)
            return [[points[i], points[i + 1]] for i in range(len(points) - 1)]

        elif hasattr(spline, "control_points") and spline.control_points:
            if spline.dxf.degree == 3:
                bezier = Bezier(spline.control_points)
                points = np.array(bezier.points(np.linspace(0, 1, segments)))
                return [[points[i], points[i + 1]] for i in range(len(points) - 1)]
            else:
                bspline = BSpline(
                    control_points=spline.control_points,
                    order=spline.dxf.degree + 1,
                    knots=spline.knots,
                )
                points = np.array(bspline.points(np.linspace(0, 1, segments)))
                return [[points[i], points[i + 1]] for i in range(len(points) - 1)]

        return []
    except Exception as e:
        print(f"[УВАГА] Помилка обробки SPLINE: {e}")
        return []


def entity_to_lines(entity):
    lines = []
    try:
        if entity.dxftype() == "LINE":
            start = (float(entity.dxf.start[0]), float(entity.dxf.start[1]))
            end = (float(entity.dxf.end[0]), float(entity.dxf.end[1]))
            lines.append([start, end])

        elif entity.dxftype() == "LWPOLYLINE":
            points = entity.get_points("xy")
            points = [(float(x), float(y)) for x, y in points]
            if entity.closed:
                points.append(points[0])
            for i in range(len(points) - 1):
                lines.append([points[i], points[i + 1]])

        elif entity.dxftype() == "CIRCLE":
            # 1. Отримуємо OCS об'єкта
            ocs = entity.ocs()
            # 2. Перетворюємо точку центру з OCS в WCS
            wcs_center = ocs.to_wcs(entity.dxf.center)
            
            center = (wcs_center.x, wcs_center.y) # Використовуємо виправлені WCS координати
            radius = float(entity.dxf.radius)
            angles = np.linspace(0, 2 * np.pi, 33)
            points = [
                (center[0] + radius * np.cos(a), center[1] + radius * np.sin(a))
                for a in angles
            ]
            for i in range(32):
                lines.append([points[i], points[i + 1]])

        elif entity.dxftype() == "ARC":
            # 1. Отримуємо OCS об'єкта
            ocs = entity.ocs()
            # 2. Перетворюємо точку центру з OCS в WCS
            wcs_center = ocs.to_wcs(entity.dxf.center)

            center = (wcs_center.x, wcs_center.y) # Використовуємо виправлені WCS координати
            radius = float(entity.dxf.radius)
            start_angle = np.radians(float(entity.dxf.start_angle))
            end_angle = np.radians(float(entity.dxf.end_angle))
            angles = np.linspace(start_angle, end_angle, 32)
            points = [
                (center[0] + radius * np.cos(a), center[1] + radius * np.sin(a))
                for a in angles
            ]
            for i in range(len(points) - 1):
                lines.append([points[i], points[i + 1]])

        elif entity.dxftype() == "SPLINE":
            lines.extend(spline_to_lines(entity))

        elif entity.dxftype() == "ELLIPSE":
            center = np.array(
                [float(entity.dxf.center[0]), float(entity.dxf.center[1])]
            )
            major = np.array(
                [float(entity.dxf.major_axis[0]), float(entity.dxf.major_axis[1])]
            )
            ratio = float(entity.dxf.ratio)
            angles = np.linspace(0, 2 * np.pi, 64)
            points = [
                center
                + major * np.cos(a)
                + ratio * np.array([-major[1], major[0]]) * np.sin(a)
                for a in angles
            ]
            for i in range(len(points) - 1):
                lines.append([tuple(points[i]), tuple(points[i + 1])])

        elif entity.dxftype() == "POINT":
            x, y = float(entity.dxf.location[0]), float(entity.dxf.location[1])
            lines.append([(x - 0.5, y), (x + 0.5, y)])
            lines.append([(x, y - 0.5), (x, y + 0.5)])

        else:
            print(f"[WARN] Неподдерживаемый тип объекта: {entity.dxftype()}")

    except Exception as e:
        print(f"[УВАГА] Помилка обробки {entity.dxftype()}: {e}")

    return lines


def render_layer(dxf_path: str, layer_name: str) -> ContentFile:
    try:
        entities = extract_entities(dxf_path, layer_name)
        if not entities:
            print(f"[WARN] Слой {layer_name} пуст")
            return None

        all_lines = []
        for entity in entities:
            print(entity)
            all_lines.extend(entity_to_lines(entity))

        if not all_lines:
            print(f"[WARN] Нет данных для отображения в слое {layer_name}")
            return None

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_aspect("equal")
        ax.axis("off")

        lc = LineCollection(all_lines, linewidths=0.5, colors="black")
        ax.add_collection(lc)
        ax.autoscale()

        buffer = io.BytesIO()
        plt.savefig(
            buffer,
            format="png",
            bbox_inches="tight",
            pad_inches=0,
            dpi=300,
            facecolor="white",
        )
        plt.close(fig)

        buffer.seek(0)
        return ContentFile(buffer.read(), name=f"layer_{layer_name}.png")

    except Exception as e:
        print(f"[ПОМИЛКА] Помилка рендерингу шару {layer_name}: {e}")
        return None


@shared_task
def generate_layer_previews(dxf_path, drawing_id):
    try:
        dxf_path = dxf_path

        layers = get_dxf_layers(dxf_path)
        preview_folder = "previews/"

        for filename in default_storage.listdir(preview_folder)[1]:
            if filename.startswith(f"layer_{drawing_id}_"):
                default_storage.delete(os.path.join(preview_folder, filename))

        for layer in layers:
            preview = render_layer(dxf_path, layer)
            if preview:
                filename = f"layer_{drawing_id}_{layer}.png"
                default_storage.save(os.path.join(preview_folder, filename), preview)

    except Exception as e:
        print(f"[ПОМИЛКА] Помилка генерації прев'ю шарів: {e}")


def calculate_layer_cut_length(dxf_path: str, layer_name: str) -> float:
    entities = extract_entities(dxf_path, layer_name)
    if not entities:
        print(f"[ІНФО] Шар '{layer_name}' не знайдено або він порожній.")
        return 0.0

    total_length = 0.0

    for entity in entities:
        if entity.dxftype() == "POINT":
            continue

        line_segments = entity_to_lines(entity)

        for segment in line_segments:
            start_point = segment[0]
            end_point = segment[1]
            length = math.dist(start_point, end_point)
            total_length += length

    return total_length


def get_drawing_area_m2(dxf_path: str) -> Decimal:
    try:
        doc = ezdxf.readfile(dxf_path)
        entities = list(doc.modelspace())

        if not entities:
            print("[ІНФО] Креслення порожнє.")
            return Decimal("0.0")

        polygons = []

        for entity in entities:
            try:
                if entity.dxftype() == "LWPOLYLINE" and entity.closed:
                    points = entity.get_points("xy")
                    points = [(float(x), float(y)) for x, y in points]
                    if len(points) >= 3:
                        polygon = Polygon(points)
                        if polygon.is_valid:
                            polygons.append(polygon)

                elif entity.dxftype() == "CIRCLE":
                    center = (float(entity.dxf.center[0]), float(entity.dxf.center[1]))
                    radius = float(entity.dxf.radius)
                    angles = np.linspace(0, 2 * np.pi, 64)
                    points = [
                        (center[0] + radius * np.cos(a), center[1] + radius * np.sin(a))
                        for a in angles
                    ]
                    polygon = Polygon(points)
                    if polygon.is_valid:
                        polygons.append(polygon)

                elif entity.dxftype() == "ELLIPSE":
                    center = np.array(
                        [float(entity.dxf.center[0]), float(entity.dxf.center[1])]
                    )
                    major = np.array(
                        [
                            float(entity.dxf.major_axis[0]),
                            float(entity.dxf.major_axis[1]),
                        ]
                    )
                    ratio = float(entity.dxf.ratio)
                    angles = np.linspace(0, 2 * np.pi, 64)
                    points = [
                        center
                        + major * np.cos(a)
                        + ratio * np.array([-major[1], major[0]]) * np.sin(a)
                        for a in angles
                    ]
                    points = [tuple(p) for p in points]
                    polygon = Polygon(points)
                    if polygon.is_valid:
                        polygons.append(polygon)

                elif entity.dxftype() == "SPLINE":
                    if hasattr(entity, "closed") and entity.closed:
                        line_segments = spline_to_lines(entity, segments=100)
                        if line_segments:
                            points = [line_segments[0][0]]
                            for segment in line_segments:
                                points.append(segment[1])

                            if len(points) >= 3:
                                polygon = Polygon(points)
                                if polygon.is_valid:
                                    polygons.append(polygon)

                elif entity.dxftype() == "HATCH":
                    if hasattr(entity, "paths"):
                        for path in entity.paths:
                            if hasattr(path, "path_vertices"):
                                points = [
                                    (float(v[0]), float(v[1]))
                                    for v in path.path_vertices
                                ]
                                if len(points) >= 3:
                                    polygon = Polygon(points)
                                    if polygon.is_valid:
                                        polygons.append(polygon)

                elif entity.dxftype() == "SOLID" or entity.dxftype() == "3DFACE":
                    if hasattr(entity.dxf, "vtx0"):
                        points = []
                        for i in range(4):
                            vtx_attr = f"vtx{i}"
                            if hasattr(entity.dxf, vtx_attr):
                                vtx = getattr(entity.dxf, vtx_attr)
                                points.append((float(vtx[0]), float(vtx[1])))

                        if len(points) >= 3:
                            polygon = Polygon(points)
                            if polygon.is_valid:
                                polygons.append(polygon)

                elif entity.dxftype() == "POLYLINE":
                    if entity.is_closed:
                        vertices = list(entity.vertices)
                        points = [
                            (float(v.dxf.location[0]), float(v.dxf.location[1]))
                            for v in vertices
                        ]
                        if len(points) >= 3:
                            polygon = Polygon(points)
                            if polygon.is_valid:
                                polygons.append(polygon)

            except Exception as e:
                print(f"[УВАГА] Помилка обробки {entity.dxftype()}: {e}")
                continue

        if not polygons:
            print(f"[ІНФО] Не знайдено замкнутих контурів для обчислення площі")
            return Decimal("0.0")

        try:
            if not polygons:
                return Decimal("0.0")

            max_polygon = max(
                polygons, key=lambda p: p.area if p.is_valid and not p.is_empty else 0
            )

            if not max_polygon.is_valid or max_polygon.is_empty:
                return Decimal("0.0")

            total_area = max_polygon.area

            area_m2 = total_area / 1000000.0  # мм² у м²

            return Decimal(str(round(area_m2, 6)))

        except Exception as e:
            print(f"[ПОМИЛКА] Помилка обчислення площі: {e}")
            return Decimal("0.0")

    except Exception as e:
        print(f"[ПОМИЛКА] Помилка отримання площі креслення: {e}")
        return Decimal("0.0")


def get_bounding_box_area_m2(dxf_path: str) -> Decimal:
    try:
        doc = ezdxf.readfile(dxf_path)
        entities = list(doc.modelspace())
        if not entities:
            return Decimal("0.0")
        all_points = []
        for entity in entities:
            try:
                if entity.dxftype() == "LINE":
                    all_points.append((float(entity.dxf.start[0]), float(entity.dxf.start[1])))
                    all_points.append((float(entity.dxf.end[0]), float(entity.dxf.end[1])))
                elif entity.dxftype() == "LWPOLYLINE":
                    points = entity.get_points("xy")
                    all_points.extend([(float(x), float(y)) for x, y in points])
                elif entity.dxftype() == "CIRCLE":
                    center = (float(entity.dxf.center[0]), float(entity.dxf.center[1]))
                    radius = float(entity.dxf.radius)
                    all_points.extend([
                        (center[0] + radius, center[1]),
                        (center[0] - radius, center[1]),
                        (center[0], center[1] + radius),
                        (center[0], center[1] - radius),
                    ])
                elif entity.dxftype() == "ARC":
                    center = (float(entity.dxf.center[0]), float(entity.dxf.center[1]))
                    radius = float(entity.dxf.radius)
                    start_angle = float(entity.dxf.start_angle)
                    end_angle = float(entity.dxf.end_angle)
                    from math import radians, cos, sin
                    all_points.append((
                        center[0] + radius * cos(radians(start_angle)),
                        center[1] + radius * sin(radians(start_angle)),
                    ))
                    all_points.append((
                        center[0] + radius * cos(radians(end_angle)),
                        center[1] + radius * sin(radians(end_angle)),
                    ))
                elif entity.dxftype() == "ELLIPSE":
                    center = entity.dxf.center
                    major = entity.dxf.major_axis
                    ratio = entity.dxf.ratio
                    from math import cos, sin, pi
                    for t in [0, pi/2, pi, 3*pi/2]:
                        x = center[0] + major[0] * cos(t) + ratio * (-major[1]) * sin(t)
                        y = center[1] + major[1] * cos(t) + ratio * (major[0]) * sin(t)
                        all_points.append((x, y))
                elif entity.dxftype() == "SPLINE":
                    if hasattr(entity, "fit_points") and entity.fit_points:
                        all_points.extend([(float(p[0]), float(p[1])) for p in entity.fit_points])
                elif entity.dxftype() == "POLYLINE":
                    for v in entity.vertices:
                        all_points.append((float(v.dxf.location[0]), float(v.dxf.location[1])))
            except Exception as e:
                print(f"[УВАГА] Помилка обробки {entity.dxftype()}: {e}")
                continue
        if not all_points:
            return Decimal("0.0")
        xs, ys = zip(*all_points)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        area_mm2 = (max_x - min_x) * (max_y - min_y)
        area_m2 = area_mm2 / 1_000_000.0
        return Decimal(str(round(area_m2, 6)))
    except Exception as e:
        print(f"[ПОМИЛКА] Помилка обчислення bounding box: {e}")
        return Decimal("0.0")


def get_details_area_m2(dxf_path: str) -> Decimal:
    try:
        doc = ezdxf.readfile(dxf_path)
        entities = list(doc.modelspace())
        polygons = []
        for entity in entities:
            try:
                if entity.dxftype() == "LWPOLYLINE" and entity.closed:
                    points = entity.get_points("xy")
                    points = [(float(x), float(y)) for x, y in points]
                    if len(points) >= 3:
                        polygon = Polygon(points)
                        if polygon.is_valid:
                            polygons.append(polygon)
                elif entity.dxftype() == "CIRCLE":
                    center = (float(entity.dxf.center[0]), float(entity.dxf.center[1]))
                    radius = float(entity.dxf.radius)
                    import numpy as np
                    angles = np.linspace(0, 2 * np.pi, 64)
                    points = [
                        (center[0] + radius * np.cos(a), center[1] + radius * np.sin(a))
                        for a in angles
                    ]
                    polygon = Polygon(points)
                    if polygon.is_valid:
                        polygons.append(polygon)
                elif entity.dxftype() == "ELLIPSE":
                    center = entity.dxf.center
                    major = entity.dxf.major_axis
                    ratio = entity.dxf.ratio
                    import numpy as np
                    angles = np.linspace(0, 2 * np.pi, 64)
                    points = [
                        (
                            center[0] + major[0] * np.cos(a) + ratio * (-major[1]) * np.sin(a),
                            center[1] + major[1] * np.cos(a) + ratio * (major[0]) * np.sin(a),
                        )
                        for a in angles
                    ]
                    polygon = Polygon(points)
                    if polygon.is_valid:
                        polygons.append(polygon)
                elif entity.dxftype() == "SPLINE":
                    if hasattr(entity, "closed") and entity.closed:
                        from .utils import spline_to_lines
                        line_segments = spline_to_lines(entity, segments=100)
                        if line_segments:
                            points = [line_segments[0][0]]
                            for segment in line_segments:
                                points.append(segment[1])
                            if len(points) >= 3:
                                polygon = Polygon(points)
                                if polygon.is_valid:
                                    polygons.append(polygon)
                elif entity.dxftype() == "HATCH":
                    if hasattr(entity, "paths"):
                        for path in entity.paths:
                            if hasattr(path, "path_vertices"):
                                points = [
                                    (float(v[0]), float(v[1]))
                                    for v in path.path_vertices
                                ]
                                if len(points) >= 3:
                                    polygon = Polygon(points)
                                    if polygon.is_valid:
                                        polygons.append(polygon)
                elif entity.dxftype() == "SOLID" or entity.dxftype() == "3DFACE":
                    if hasattr(entity.dxf, "vtx0"):
                        points = []
                        for i in range(4):
                            vtx_attr = f"vtx{i}"
                            if hasattr(entity.dxf, vtx_attr):
                                vtx = getattr(entity.dxf, vtx_attr)
                                points.append((float(vtx[0]), float(vtx[1])))
                        if len(points) >= 3:
                            polygon = Polygon(points)
                            if polygon.is_valid:
                                polygons.append(polygon)
                elif entity.dxftype() == "POLYLINE":
                    if entity.is_closed:
                        vertices = list(entity.vertices)
                        points = [
                            (float(v.dxf.location[0]), float(v.dxf.location[1]))
                            for v in vertices
                        ]
                        if len(points) >= 3:
                            polygon = Polygon(points)
                            if polygon.is_valid:
                                polygons.append(polygon)
            except Exception as e:
                print(f"[УВАГА] Помилка обробки {entity.dxftype()}: {e}")
                continue
        if not polygons:
            print(f"[ІНФО] Не знайдено замкнутих контурів для обчислення площі")
            return Decimal("0.0")
        max_polygon = max(polygons, key=lambda p: p.area if p.is_valid and not p.is_empty else 0)
        detail_area = sum(p.area for p in polygons if p != max_polygon)
        if detail_area == 0:
            detail_area = max_polygon.area
        area_m2 = detail_area / 1_000_000.0  # мм² у м²
        return Decimal(str(round(area_m2, 6)))
    except Exception as e:
        print(f"[ПОМИЛКА] Помилка отримання площі деталей: {e}")
        return Decimal("0.0")


def generate_dxf_preview(
    dxf_path: str, output_filename="preview.png"
) -> ContentFile | None:
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_axes([0, 0, 1, 1])

        ctx = RenderContext(doc)
        backend = MatplotlibBackend(ax)
        frontend = Frontend(ctx, backend)
        frontend.draw_layout(msp)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=200)
        buf.seek(0)
        content = ContentFile(buf.read(), name=output_filename)

        buf.close()
        plt.close(fig)
        return content

    except Exception as e:
        print(f"[DXF ПОМИЛКА] Неможливо створити прев'ю: {e}")
        return None
