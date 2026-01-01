#!/usr/bin/env python3
"""
Memory-Efficient JSON -> PDF Generator for Twitter Data

Production-grade batch processing script.
Streams JSON parsing, downloads images one-by-one, and generates PDF
without holding large data in memory.
Supports nested threads and high-quality images.
"""

import os
import sys
import tempfile
import argparse
import json
from typing import Generator, Optional, Any, Callable, List, Tuple

# Try importing ijson for streaming, fallback to standard json if not available
try:
    import ijson
except ImportError:
    ijson = None

import requests
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Image as RLImage,
    Spacer,
    HRFlowable,
    Table,
    TableStyle
)

# =============================================================================
# CONFIGURATION & LOGGING
# =============================================================================

# Global logger function
_logger: Optional[Callable[[str, str], None]] = None

def set_logger(logger_func: Optional[Callable[[str, str], None]]) -> None:
    global _logger
    _logger = logger_func

def _log(message: str, color: str = "#ffffff") -> None:
    if _logger:
        _logger(message, color)
    else:
        print(message, file=sys.stderr)

MAX_IMAGE_WIDTH = 4096
MAX_IMAGE_HEIGHT = 4096
IMAGE_QUALITY = 100
REQUEST_TIMEOUT = 30
PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT = A4
PDF_MARGIN = 0.5 * inch
CONTENT_WIDTH = PDF_PAGE_WIDTH - 2 * PDF_MARGIN
MAX_IMAGE_HEIGHT_POINTS = 400  # Limit height of images in PDF

# =============================================================================
# STREAMING JSON PARSER
# =============================================================================

def stream_tweets(json_filepath: str) -> Generator[dict, None, None]:
    """Stream tweets from a JSON file one at a time."""
    with open(json_filepath, 'rb') as f:
        if ijson:
            for tweet in ijson.items(f, 'item'):
                yield tweet
        else:
            # Fallback for small files if ijson is missing
            data = json.load(f)
            for tweet in data:
                yield tweet

# =============================================================================
# IMAGE HANDLING
# =============================================================================

def download_and_prepare_image(
    image_url: str,
    max_width: int = MAX_IMAGE_WIDTH,
    max_height: int = MAX_IMAGE_HEIGHT,
    quality: int = IMAGE_QUALITY,
    is_avatar: bool = False
) -> Optional[str]:
    """Download, resize, and save image to temp file."""
    if not image_url:
        return None

    # Append ?name=orig for better quality if not present (skip for avatars)
    if '?' not in image_url and not is_avatar:
        image_url += '?name=orig'
        
    temp_path = None
    raw_temp_path = None
    
    try:
        response = requests.get(image_url, timeout=REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        
        raw_fd, raw_temp_path = tempfile.mkstemp(suffix='.raw')
        try:
            with os.fdopen(raw_fd, 'wb') as raw_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        raw_file.write(chunk)
        except Exception:
            os.close(raw_fd)
            raise
        
        with Image.open(raw_temp_path) as img:
            if img.mode in ('RGBA', 'P', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize logic
            target_w, target_h = max_width, max_height
            if is_avatar:
                # Force resize for avatars to save space/processing
                img = img.resize((target_w, target_h), Image.LANCZOS)
            else:
                # Proportional resize for media
                width_ratio = target_w / img.width if img.width > target_w else 1.0
                height_ratio = target_h / img.height if img.height > target_h else 1.0
                ratio = min(width_ratio, height_ratio)
                
                if ratio < 1.0:
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
            
            fd, temp_path = tempfile.mkstemp(suffix='.jpg')
            try:
                with os.fdopen(fd, 'wb') as out_file:
                    img.save(out_file, format='JPEG', quality=quality, optimize=True)
            except Exception:
                os.close(fd)
                raise
        
        return temp_path
        
    except Exception as e:
        # _log(f"[WARN] Image error {image_url}: {e}", "#FFAA00")
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        return None
    finally:
        if raw_temp_path and os.path.exists(raw_temp_path):
            try:
                os.unlink(raw_temp_path)
            except OSError:
                pass

def cleanup_temp_file(filepath: Optional[str]) -> None:
    if filepath and os.path.exists(filepath):
        try:
            os.unlink(filepath)
        except OSError:
            pass

# =============================================================================
# PDF RENDERING
# =============================================================================

def create_styles() -> dict:
    base_styles = getSampleStyleSheet()
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'
    
    styles = {
        'name': ParagraphStyle(
            'TweetName',
            parent=base_styles['Normal'],
            fontName=font_bold,
            fontSize=11,
            textColor=colors.black,
            leading=13,
        ),
        'handle': ParagraphStyle(
            'TweetHandle',
            parent=base_styles['Normal'],
            fontName=font_name,
            fontSize=10,
            textColor=colors.grey,
            leading=12,
        ),
        'text': ParagraphStyle(
            'TweetText',
            parent=base_styles['Normal'],
            fontName=font_name,
            fontSize=12,
            leading=16,
            spaceBefore=6,
            spaceAfter=8,
            textColor=colors.black,
        ),
        'link': ParagraphStyle(
            'TweetLink',
            parent=base_styles['Normal'],
            fontName=font_name,
            fontSize=10,
            textColor=colors.blue,
        ),
    }
    return styles

def escape_xml(text: str) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )

def render_single_tweet(tweet: dict, styles: dict, content_width: float) -> Tuple[List[Any], List[str]]:
    """Render a single tweet (header + body + media)."""
    elements = []
    temp_files = []
    
    # --- Data Extraction ---
    user = tweet.get('user', {}) or {}
    name = user.get('name') or "Unknown"
    screen_name = user.get('screen_name') or "unknown"
    avatar_url = user.get('profile_image_url')
    
    full_text = tweet.get('full_text', '')
    created_at = tweet.get('created_at', '')
    # Clean date: "Thu Jan 01 07:30:49 +0000 2026" -> "Jan 01, 2026 07:30"
    try:
        if created_at:
            parts = created_at.split()
            # Simple reformat: Month Day, Year Time
            if len(parts) >= 6:
                created_at = f"{parts[1]} {parts[2]}, {parts[5]} {parts[3]}"
    except:
        pass

    media_urls = tweet.get('media', [])
    
    # --- Header (Avatar | Name/Handle/Date) ---
    avatar_img = None
    if avatar_url:
        avatar_path = download_and_prepare_image(avatar_url, max_width=40, max_height=40, is_avatar=True)
        if avatar_path:
            temp_files.append(avatar_path)
            avatar_img = RLImage(avatar_path, width=32, height=32)
    
    header_text = [
        Paragraph(escape_xml(name), styles['name']),
        Paragraph(f"@{escape_xml(screen_name)} • {escape_xml(created_at)}", styles['handle'])
    ]
    
    # Table for Header
    # Col 1: Avatar (fixed width), Col 2: Text
    header_data = [[avatar_img if avatar_img else "", header_text]]
    header_table = Table(header_data, colWidths=[40, content_width - 40])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    
    # --- Body Text ---
    if full_text:
        # Split text into multiple paragraphs to allow better page breaking
        # especially when inside a table (replies)
        paragraphs = full_text.split('\n\n')
        for p_text in paragraphs:
            if p_text.strip():
                formatted_text = escape_xml(p_text).replace('\n', '<br/>')
                elements.append(Paragraph(formatted_text, styles['text']))
    
    # --- Media ---
    if media_urls:
        for url in media_urls:
            img_path = download_and_prepare_image(url)
            if img_path:
                temp_files.append(img_path)
                try:
                    with Image.open(img_path) as pil_img:
                        w, h = pil_img.size
                    
                    # Scale to fit
                    max_w = content_width
                    max_h = MAX_IMAGE_HEIGHT_POINTS
                    scale = min(1.0, max_w / w, max_h / h)
                    
                    rl_img = RLImage(img_path, width=w*scale, height=h*scale)
                    elements.append(Spacer(1, 4))
                    elements.append(rl_img)
                    elements.append(Spacer(1, 4))
                except Exception:
                    pass

    return elements, temp_files

def render_tweet_group(tweet_data: dict, styles: dict, content_width: float) -> Tuple[List[Any], List[str]]:
    """Render a root tweet and its thread replies."""
    all_flowables = []
    all_temp_files = []
    
    # 1. Root Tweet
    f, t = render_single_tweet(tweet_data, styles, content_width)
    all_flowables.extend(f)
    all_temp_files.extend(t)
    
    # 2. Thread Replies
    thread = tweet_data.get('thread', [])
    if thread:
        for reply in thread:
            # Render reply
            # We reduce width slightly for visual hierarchy
            reply_width = content_width - 20 # Indent 20pt
            rf, rt = render_single_tweet(reply, styles, reply_width)
            all_temp_files.extend(rt)
            
            # Create a multi-row table to allow page splitting between elements
            # Each element (Header, Text Paragraph, Image) gets its own row
            reply_rows = [[item] for item in rf]
            
            reply_container = Table(reply_rows, colWidths=[content_width])
            reply_container.setStyle(TableStyle([
                ('LEFTPADDING', (0,0), (-1,-1), 20), # Indent content
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('LINEBEFORE', (0,0), (0,-1), 2, colors.lightgrey), # Continuous vertical line
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            all_flowables.append(reply_container)
            
            # Add spacing between replies
            all_flowables.append(Spacer(1, 12))

    # 3. Divider
    all_flowables.append(Spacer(1, 10))
    all_flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    all_flowables.append(Spacer(1, 10))
    
    return all_flowables, all_temp_files

class TweetFlowableGenerator:
    def __init__(self, json_filepath: str, styles: dict, content_width: float):
        self.json_filepath = json_filepath
        self.styles = styles
        self.content_width = content_width
        self.tweet_count = 0
        self.pending_temp_files = []
    
    def generate_flowables(self) -> Generator[Any, None, None]:
        for tweet in stream_tweets(self.json_filepath):
            self.tweet_count += 1
            if self.tweet_count % 5 == 0:
                _log(f"[INFO] Processing tweet {self.tweet_count}...", "#888888")
            
            elements, temp_files = render_tweet_group(tweet, self.styles, self.content_width)
            self.pending_temp_files.extend(temp_files)
            
            for element in elements:
                yield element
    
    def cleanup(self):
        for filepath in self.pending_temp_files:
            cleanup_temp_file(filepath)
        self.pending_temp_files.clear()

def generate_pdf(json_filepath: str, output_dir: str = None) -> str:
    base_name = os.path.splitext(os.path.basename(json_filepath))[0]
    pdf_filename = f"{base_name}.pdf"
    
    if output_dir:
        output_filepath = os.path.join(output_dir, pdf_filename)
    else:
        output_filepath = os.path.join(os.path.dirname(json_filepath), pdf_filename)
    
    _log(f"[INFO] Generating PDF: {output_filepath}", "#00BFFF")
    
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=A4,
        leftMargin=PDF_MARGIN,
        rightMargin=PDF_MARGIN,
        topMargin=PDF_MARGIN,
        bottomMargin=PDF_MARGIN,
    )
    
    styles = create_styles()
    generator = TweetFlowableGenerator(json_filepath, styles, CONTENT_WIDTH)
    
    try:
        all_flowables = list(generator.generate_flowables())
        doc.build(all_flowables)
        _log(f"[SUCCESS] PDF generated with {generator.tweet_count} root tweets.", "#00FF04")
    finally:
        generator.cleanup()
    
    return output_filepath

def main():
    parser = argparse.ArgumentParser(description='JSON to PDF Converter')
    parser.add_argument('input_json', nargs='?', help='Input JSON file')
    parser.add_argument('output_pdf', nargs='?', help='Output PDF file')
    args = parser.parse_args()
    
    if not args.input_json:
        print("Usage: python json_to_pdf.py <input.json> [output.pdf]")
        sys.exit(1)
        
    generate_pdf(args.input_json, args.output_pdf)

if __name__ == '__main__':
    main()
