import base64
from io import BytesIO


def barcode_data_uri(tracking_number: str) -> str:
    from barcode import Code128
    from barcode.writer import ImageWriter
    buf = BytesIO()
    Code128(str(tracking_number), writer=ImageWriter()).write(buf, {
        "module_height": 15.0, "module_width": 0.4, "text_distance": 1.0,
        "font_size": 10, "quiet_zone": 1.0,
    })
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"