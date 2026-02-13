"""
PDF conversion utilities for Kids Colouring App
Converts generated PNGs to print-ready A4 PDFs at 300 DPI
"""

import base64
import io
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# A4 at 300 DPI
A4_WIDTH_PX = 2480
A4_HEIGHT_PX = 3508
A4_WIDTH_PT, A4_HEIGHT_PT = A4  # 595.27, 841.89 points

# Margins (0mm for edge-to-edge printing)
MARGIN_MM = 0
MARGIN_PT = MARGIN_MM * mm


def upscale_image_for_print(image_b64: str) -> tuple[Image.Image, bool]:
    """
    Upscale image to 300 DPI for A4 printing.
    Input: base64 PNG (can be portrait or landscape)
    Output: (PIL Image at 300 DPI, is_landscape bool)
    """
    image_bytes = base64.b64decode(image_b64)
    image = Image.open(io.BytesIO(image_bytes))
    
    # Detect orientation
    is_landscape = image.width > image.height
    
    # Convert to RGB if necessary (PDF doesn't support RGBA well)
    if image.mode in ('RGBA', 'P'):
        # Create white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Upscale to 300 DPI A4 size using LANCZOS (best for line art)
    if is_landscape:
        # Landscape: swap dimensions
        upscaled = image.resize((A4_HEIGHT_PX, A4_WIDTH_PX), Image.LANCZOS)
    else:
        # Portrait: normal dimensions
        upscaled = image.resize((A4_WIDTH_PX, A4_HEIGHT_PX), Image.LANCZOS)
    
    return upscaled, is_landscape


def create_a4_pdf(image_b64: str) -> str:
    """
    Convert base64 PNG to print-ready A4 PDF at 300 DPI.
    
    Input: base64 encoded PNG (portrait or landscape)
    Output: base64 encoded PDF (matching orientation)
    """
    from reportlab.lib.pagesizes import landscape
    
    # Upscale image and detect orientation
    upscaled_image, is_landscape = upscale_image_for_print(image_b64)
    
    # Save upscaled image to bytes
    img_buffer = io.BytesIO()
    upscaled_image.save(img_buffer, format='PNG', optimize=True)
    img_buffer.seek(0)
    
    # Create PDF with matching orientation
    pdf_buffer = io.BytesIO()
    if is_landscape:
        page_size = landscape(A4)
    else:
        page_size = A4
    c = canvas.Canvas(pdf_buffer, pagesize=page_size)
    
    # Calculate drawable area (A4 minus margins)
    page_width, page_height = page_size
    drawable_width = page_width - (2 * MARGIN_PT)
    drawable_height = page_height - (2 * MARGIN_PT)
    
    # Calculate scale to fit image in drawable area while maintaining aspect ratio
    img_aspect = upscaled_image.width / upscaled_image.height
    drawable_aspect = drawable_width / drawable_height
    
    print(f"[PDF] Image: {upscaled_image.width}x{upscaled_image.height}, Landscape: {is_landscape}")
    
    if img_aspect > drawable_aspect:
        # Image is wider - fit to width
        final_width = drawable_width
        final_height = drawable_width / img_aspect
    else:
        # Image is taller - fit to height
        final_height = drawable_height
        final_width = drawable_height * img_aspect
    
    # Center image on page
    x = MARGIN_PT + (drawable_width - final_width) / 2
    y = MARGIN_PT + (drawable_height - final_height) / 2
    
    # Draw image
    img_reader = ImageReader(img_buffer)
    c.drawImage(img_reader, x, y, width=final_width, height=final_height)
    
    c.save()
    
    # Return as base64
    pdf_buffer.seek(0)
    pdf_b64 = base64.b64encode(pdf_buffer.read()).decode('utf-8')
    
    return pdf_b64
