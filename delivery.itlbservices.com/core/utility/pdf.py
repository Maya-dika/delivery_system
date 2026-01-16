from django.template.loader import render_to_string
from django.utils.text import slugify
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
import io, os
from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse

from urllib.parse import urlparse
import re

def _link_callback(uri, rel):
    # Ignore Pisa's synthetic rel like ".../__dummy__"
    # Handle common schemes up-front
    if not uri:
        return None
    if uri.startswith(("data:", "about:")):
        return None  # let it be ignored

    # file://
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return parsed.path

    # Windows absolute path like C:\...
    if re.match(r"^[a-zA-Z]:\\", uri):
        return uri

    # MEDIA
    if settings.MEDIA_URL and uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri[len(settings.MEDIA_URL):])
        return path if os.path.isfile(path) else None

    # STATIC (collected or app-level)
    if settings.STATIC_URL and uri.startswith(settings.STATIC_URL):
        rel_path = uri[len(settings.STATIC_URL):]
        static_path = finders.find(rel_path) or (os.path.join(settings.STATIC_ROOT, rel_path) if settings.STATIC_ROOT else None)
        return static_path if static_path and os.path.isfile(static_path) else None

    # Relative path -> try static finders
    if not os.path.isabs(uri):
        candidate = finders.find(uri)
        if candidate and os.path.isfile(candidate):
            return candidate

    # Last resort: if it's an absolute POSIX path, return it; otherwise ignore
    return uri if os.path.isabs(uri) and os.path.isfile(uri) else None


def render_template_to_pdf(request, template_name: str, context: dict) -> bytes:
    """
    Render a template to PDF bytes using xhtml2pdf (pisa).
    """
    html = render_to_string(template_name, context=context, request=request)
    buff = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buff, link_callback=_link_callback, encoding="utf-8")
    if result.err:
        raise Exception(f"xhtml2pdf failed with code {result.err}")
    return buff.getvalue()


def pdf_download(pdf_bytes: bytes, filename: str) -> HttpResponse:
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return resp
