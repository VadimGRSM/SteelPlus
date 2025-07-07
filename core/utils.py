import os
import ezdxf
import io
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.math import Bezier, BSpline

from .models import Drawing

matplotlib.use("Agg")


@shared_task
def generate_preview_background(drawing_id):
    try:
        drawing = Drawing.objects.get(pk=drawing_id)
        if not drawing.file_path.name.endswith(".dxf"):
            return

        preview = generate_dxf_preview(drawing.file_path.path)
        if preview:
            preview_filename = f"previews/preview_{drawing.pk}.png"
            if default_storage.exists(preview_filename):
                default_storage.delete(preview_filename)
            default_storage.save(preview_filename, preview)
    except Exception as e:
        print(f"[ERROR] Ошибка генерации превью: {e}")


def get_dxf_layers(dxf_path: str) -> list[str]:
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        return sorted({entity.dxf.layer for entity in msp})
    except Exception as e:
        print(f"[ERROR] Не удалось получить слои: {e}")
        return []


def extract_entities(dxf_path: str, layer_name: str):
    try:
        doc = ezdxf.readfile(dxf_path)
        return [entity for entity in doc.modelspace() if entity.dxf.layer == layer_name]
    except Exception as e:
        print(f"[ERROR] Ошибка извлечения объектов: {e}")
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
        print(f"[WARN] Ошибка обработки SPLINE: {e}")
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
            center = (float(entity.dxf.center[0]), float(entity.dxf.center[1]))
            radius = float(entity.dxf.radius)
            angles = np.linspace(0, 2 * np.pi, 33)
            points = [
                (center[0] + radius * np.cos(a), center[1] + radius * np.sin(a))
                for a in angles
            ]
            for i in range(32):
                lines.append([points[i], points[i + 1]])

        elif entity.dxftype() == "ARC":
            center = (float(entity.dxf.center[0]), float(entity.dxf.center[1]))
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
        print(f"[WARN] Ошибка обработки {entity.dxftype()}: {e}")

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
        print(f"[ERROR] Ошибка рендеринга слоя {layer_name}: {e}")
        return None


@shared_task
def generate_layer_previews(drawing_id, dxf_path=None):
    try:
        drawing = Drawing.objects.get(pk=drawing_id)
        dxf_path = dxf_path or drawing.file_path.path

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
        print(f"[ERROR] Ошибка генерации превью слоев: {e}")


def calculate_layer_cut_length(dxf_path: str, layer_name: str) -> float:
    entities = extract_entities(dxf_path, layer_name)
    if not entities:
        print(f"[INFO] Слой '{layer_name}' не найден или пуст.")
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


def generate_dxf_preview(dxf_path: str, output_filename="preview.png") -> ContentFile | None:
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
        print(f"[DXF ERROR] Невозможно создать превью: {e}")
        return None
