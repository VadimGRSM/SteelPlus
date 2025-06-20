import io
import math
import matplotlib
import matplotlib.pyplot as plt
import ezdxf
from django.core.files.base import ContentFile
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.math import Vec2, Vec3

matplotlib.use("Agg")


def generate_dxf_preview(
    dxf_path: str, output_filename="preview.png"
) -> ContentFile | None:
    try:
        # Чтение DXF
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Создание фигуры matplotlib и оси
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_axes([0, 0, 1, 1])

        # Создание контекста рендеринга и бэкенда
        ctx = RenderContext(doc)
        backend = MatplotlibBackend(ax)  # <-- передаём ax сюда
        frontend = Frontend(ctx, backend)
        frontend.draw_layout(msp)

        # Сохраняем как PNG в память
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=200)
        buf.seek(0)
        content = ContentFile(buf.read(), name=output_filename)

        # Очистка
        buf.close()
        plt.close(fig)
        return content

    except Exception as e:
        print(f"[DXF ERROR] Невозможно создать превью: {e}")
        return None


def get_drawing_sizes(file_path):
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for entity in msp:
            if entity.dxftype() == "LINE":
                for point in [entity.dxf.start, entity.dxf.end]:
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)

            elif entity.dxftype() == "CIRCLE":
                center = entity.dxf.center
                r = entity.dxf.radius
                min_x = min(min_x, center.x - r)
                max_x = max(max_x, center.x + r)
                min_y = min(min_y, center.y - r)
                max_y = max(max_y, center.y + r)

            # Добавь поддержку других типов (ARC, LWPOLYLINE и т.д.) при необходимости

        if min_x == float("inf"):
            return None

        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
        }

    except Exception as e:
        print("[DXF SIZE ERROR]", str(e))
        return None
