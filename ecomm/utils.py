from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    # Load HTML template
    template = get_template(template_src)
    html = template.render(context_dict)

    # Create a BytesIO buffer for the PDF
    result = BytesIO()

    # Convert HTML to PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type="application/pdf")
    return None
