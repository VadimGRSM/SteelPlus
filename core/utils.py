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
