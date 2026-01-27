"""
🎨 My Character's Adventures - PDF Utilities
=============================================

Utilities for creating print-ready A4 PDFs with coloring pages and story text.

Add to backend folder: ~/Downloads/kids-colouring-app/backend/adventure_pdf.py
"""

import io
import base64
from typing import Optional

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm

# =============================================================================
# CONFIGURATION
# =============================================================================

# A4 dimensions at 300 DPI for high-quality printing
A4_WIDTH_PX = 2480
A4_HEIGHT_PX = 3508
DPI = 300

# PDF layout settings
MARGIN_MM = 10
TEXT_AREA_HEIGHT_MM = 45  # Space reserved for story text at bottom


# =============================================================================
# PDF CREATION
# =============================================================================

def create_adventure_pdf(
    image_bytes: bytes,
    episode_num: int,
    episode_title: str,
    story_text: str,
    character_name: str,
    age_level: str,
    total_episodes: int = 10,
    choice_info: Optional[str] = None
) -> bytes:
    """
    Create an A4 PDF with coloring page and story text.
    
    Args:
        image_bytes: PNG image bytes of the coloring page
        episode_num: Episode number (1-10)
        episode_title: Title of this episode
        story_text: Story text to display below the image
        character_name: Name of the main character
        age_level: Age level string (e.g., "age_6")
        total_episodes: Total number of episodes in adventure
        choice_info: Optional string describing choice made (for choice episodes)
    
    Returns:
        PDF file as bytes
    """
    # Open and prepare image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if needed (PDF doesn't support RGBA well)
    if image.mode in ('RGBA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Calculate dimensions
    a4_width_pt, a4_height_pt = A4
    margin = MARGIN_MM * mm
    text_area_height = TEXT_AREA_HEIGHT_MM * mm
    
    # Available space for image (above the text area)
    available_width = a4_width_pt - (2 * margin)
    available_height = a4_height_pt - (2 * margin) - text_area_height
    
    # Create PDF buffer
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    
    # Calculate image size maintaining aspect ratio
    img_aspect = image.width / image.height
    area_aspect = available_width / available_height
    
    if img_aspect > area_aspect:
        # Image is wider - fit to width
        img_width = available_width
        img_height = available_width / img_aspect
    else:
        # Image is taller - fit to height
        img_height = available_height
        img_width = available_height * img_aspect
    
    # Center image horizontally, position above text area
    img_x = margin + (available_width - img_width) / 2
    img_y = margin + text_area_height + (available_height - img_height) / 2
    
    # Draw image
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_reader = ImageReader(img_buffer)
    c.drawImage(img_reader, img_x, img_y, width=img_width, height=img_height)
    
    # Draw episode title (bold, centered)
    c.setFont("Helvetica-Bold", 14)
    title_text = f"Episode {episode_num}: {episode_title}"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 14)
    c.drawString(
        (a4_width_pt - title_width) / 2,
        margin + text_area_height - 5,
        title_text
    )
    
    # Draw story text (wrapped)
    c.setFont("Helvetica", 10)
    max_width = available_width - 20
    
    # Simple text wrapping
    words = story_text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if c.stringWidth(test_line, "Helvetica", 10) > max_width:
            current_line.pop()
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw each line of story text
    y_position = margin + text_area_height - 22
    for line in lines:
        c.drawString(margin + 10, y_position, line)
        y_position -= 12
    
    # Draw choice info if present (italics)
    if choice_info:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(margin + 10, y_position - 5, f"Choice made: {choice_info}")
    
    # Draw footer
    c.setFont("Helvetica-Oblique", 8)
    
    # Left side: Character name and branding
    age_display = age_level.replace("_", " ").replace("age ", "Age ").replace("under ", "Under ")
    footer_left = f"{character_name}'s Adventure • Little Lines • {age_display}"
    c.drawString(margin, margin - 5, footer_left)
    
    # Right side: Page number
    footer_right = f"Page {episode_num} of {total_episodes}"
    footer_right_width = c.stringWidth(footer_right, "Helvetica-Oblique", 8)
    c.drawString(a4_width_pt - margin - footer_right_width, margin - 5, footer_right)
    
    # Finish PDF
    c.save()
    
    # Return bytes
    pdf_buffer.seek(0)
    return pdf_buffer.read()


def create_adventure_pdf_base64(
    image_b64: str,
    episode_num: int,
    episode_title: str,
    story_text: str,
    character_name: str,
    age_level: str,
    total_episodes: int = 10,
    choice_info: Optional[str] = None
) -> str:
    """
    Create an A4 PDF and return as base64 string.
    
    Same as create_adventure_pdf but accepts/returns base64.
    """
    image_bytes = base64.b64decode(image_b64)
    pdf_bytes = create_adventure_pdf(
        image_bytes=image_bytes,
        episode_num=episode_num,
        episode_title=episode_title,
        story_text=story_text,
        character_name=character_name,
        age_level=age_level,
        total_episodes=total_episodes,
        choice_info=choice_info
    )
    return base64.b64encode(pdf_bytes).decode('utf-8')


def upscale_image_for_print(image_bytes: bytes) -> Image.Image:
    """
    Upscale an image to 300 DPI A4 size for high-quality printing.
    
    Args:
        image_bytes: Original image bytes
    
    Returns:
        Upscaled PIL Image (2480x3508 pixels)
    """
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary
    if image.mode in ('RGBA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Upscale to 300 DPI A4 size using LANCZOS (best for line art)
    upscaled = image.resize((A4_WIDTH_PX, A4_HEIGHT_PX), Image.LANCZOS)
    
    return upscaled


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "create_adventure_pdf",
    "create_adventure_pdf_base64",
    "upscale_image_for_print",
    "A4_WIDTH_PX",
    "A4_HEIGHT_PX",
    "DPI"
]
