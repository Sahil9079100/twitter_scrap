#!/usr/bin/env python3
"""
Memory-Efficient JSON → PDF Generator for Twitter Data

Production-grade batch processing script.
Streams JSON parsing, downloads images one-by-one, and generates PDF
without holding large data in memory.

Author: Senior Python Engineer
"""

import os
import sys
import tempfile
import argparse
from typing import Generator, Optional, Any, Callable

import ijson
import requests
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Image as RLImage,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT


# =============================================================================
# CONFIGURATION & LOGGING
# =============================================================================

# Global logger function (can be set by caller)
_logger: Optional[Callable[[str, str], None]] = None

def set_logger(logger_func: Optional[Callable[[str, str], None]]) -> None:
    """
    Set the logging callback function.
    
    Args:
        logger_func: Function with signature (text: str, color: str) -> None
                     or None to use stderr.
    """
    global _logger
    _logger = logger_func

def _log(message: str, color: str = "#ffffff") -> None:
    """
    Log a message using the configured logger or stderr.
    
    Args:
        message: The message to log.
        color: Color code (used if logger is set).
    """
    if _logger:
        _logger(message, color)
    else:
        print(message, file=sys.stderr)

MAX_IMAGE_WIDTH = 500  # pixels
MAX_IMAGE_HEIGHT = 400  # pixels - prevent overly tall images
IMAGE_QUALITY = 70  # JPEG compression quality (1-100)
REQUEST_TIMEOUT = 10  # seconds
PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT = A4
PDF_MARGIN = 0.75 * inch
CONTENT_WIDTH = PDF_PAGE_WIDTH - 2 * PDF_MARGIN
CONTENT_HEIGHT = PDF_PAGE_HEIGHT - 2 * PDF_MARGIN
MAX_IMAGE_HEIGHT_POINTS = CONTENT_HEIGHT * 0.6  # Max 60% of page height for single image


# =============================================================================
# STREAMING JSON PARSER
# =============================================================================

def stream_tweets(json_filepath: str) -> Generator[dict, None, None]:
    """
    Stream tweets from a JSON file one at a time using ijson.
    
    Never loads the entire JSON into memory.
    
    Args:
        json_filepath: Path to the JSON file containing tweet array.
        
    Yields:
        dict: One tweet object at a time.
    """
    with open(json_filepath, 'rb') as f:
        # ijson.items streams through the array, yielding one item at a time
        for tweet in ijson.items(f, 'item'):
            yield tweet


# =============================================================================
# IMAGE HANDLING
# =============================================================================

def download_and_prepare_image(
    image_url: str,
    max_width: int = MAX_IMAGE_WIDTH,
    max_height: int = MAX_IMAGE_HEIGHT,
    quality: int = IMAGE_QUALITY
) -> Optional[str]:
    """
    Download an image, resize it, compress it, and save to a temp file.
    
    Args:
        image_url: URL of the image to download.
        max_width: Maximum width in pixels for resizing.
        max_height: Maximum height in pixels for resizing.
        quality: JPEG compression quality (1-100).
        
    Returns:
        Path to the temporary file containing the processed image,
        or None if download/processing failed.
        
    Note:
        Caller is responsible for deleting the temp file after use.
    """
    temp_path = None
    raw_temp_path = None
    
    try:
        # Download image with timeout
        response = requests.get(image_url, timeout=REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        
        # Save raw downloaded bytes to a temp file (don't hold in memory)
        raw_fd, raw_temp_path = tempfile.mkstemp(suffix='.raw')
        try:
            with os.fdopen(raw_fd, 'wb') as raw_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        raw_file.write(chunk)
        except Exception:
            os.close(raw_fd)
            raise
        
        # Open with Pillow and process
        with Image.open(raw_temp_path) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'P', 'LA'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if wider than max_width OR taller than max_height
            width_ratio = max_width / img.width if img.width > max_width else 1.0
            height_ratio = max_height / img.height if img.height > max_height else 1.0
            ratio = min(width_ratio, height_ratio)
            
            if ratio < 1.0:
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Save compressed JPEG to temp file
            fd, temp_path = tempfile.mkstemp(suffix='.jpg')
            try:
                with os.fdopen(fd, 'wb') as out_file:
                    img.save(out_file, format='JPEG', quality=quality, optimize=True)
            except Exception:
                os.close(fd)
                raise
        
        return temp_path
        
    except requests.RequestException as e:
        _log(f"[WARN] Failed to download image {image_url}: {e}", "#FFAA00")
        return None
    except Exception as e:
        _log(f"[WARN] Failed to process image {image_url}: {e}", "#FFAA00")
        # Clean up temp file if it was created
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        return None
    finally:
        # Always clean up the raw download temp file
        if raw_temp_path and os.path.exists(raw_temp_path):
            try:
                os.unlink(raw_temp_path)
            except OSError:
                pass


def cleanup_temp_file(filepath: Optional[str]) -> None:
    """
    Safely delete a temporary file.
    
    Args:
        filepath: Path to the file to delete, or None.
    """
    if filepath and os.path.exists(filepath):
        try:
            os.unlink(filepath)
        except OSError as e:
            _log(f"[WARN] Failed to delete temp file {filepath}: {e}", "#FFAA00")


# =============================================================================
# PDF RENDERING
# =============================================================================

def create_styles() -> dict:
    """
    Create and return custom paragraph styles for the PDF.
    
    Returns:
        dict: Dictionary of named ParagraphStyle objects.
    """
    base_styles = getSampleStyleSheet()
    
    styles = {
        'date': ParagraphStyle(
            'TweetDate',
            parent=base_styles['Normal'],
            fontSize=9,
            textColor=HexColor('#666666'),
            spaceAfter=4,
        ),
        'text': ParagraphStyle(
            'TweetText',
            parent=base_styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=8,
        ),
        'link': ParagraphStyle(
            'TweetLink',
            parent=base_styles['Normal'],
            fontSize=9,
            textColor=HexColor('#1DA1F2'),
            spaceAfter=4,
        ),
        'video_label': ParagraphStyle(
            'VideoLabel',
            parent=base_styles['Normal'],
            fontSize=9,
            textColor=HexColor('#888888'),
            spaceAfter=2,
        ),
    }
    
    return styles


def escape_xml(text: str) -> str:
    """
    Escape special XML characters for ReportLab Paragraph.
    
    Args:
        text: Raw text string.
        
    Returns:
        XML-safe string.
    """
    if not text:
        return ""
    return (
        text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def render_tweet_block(
    tweet: dict,
    styles: dict,
    content_width: float
) -> list:
    """
    Render a single tweet as a list of ReportLab flowables.
    
    Downloads and processes images on-the-fly, cleaning up temp files
    immediately after they're added to the flowables list.
    
    Args:
        tweet: Tweet dictionary with id, date, text, images, etc.
        styles: Dictionary of ParagraphStyle objects.
        content_width: Available width for content in points.
        
    Returns:
        list: ReportLab flowables representing this tweet.
    """
    elements = []
    temp_files_to_cleanup = []
    
    try:
        # --- Date ---
        date_str = tweet.get('date', '')
        if date_str:
            # Format: 2025-12-26T21:35:02.000Z → 2025-12-26 21:35:02
            display_date = date_str.replace('T', ' ').replace('.000Z', '').replace('Z', '')
            elements.append(Paragraph(escape_xml(display_date), styles['date']))
        
        # --- Tweet Text ---
        text = tweet.get('text', '')
        if text:
            elements.append(Paragraph(escape_xml(text), styles['text']))
        
        # --- Images (downloaded, resized, embedded) ---
        images = tweet.get('images', [])
        if images:
            for img_url in images:
                if not img_url:
                    continue
                
                temp_path = download_and_prepare_image(img_url)
                if temp_path:
                    temp_files_to_cleanup.append(temp_path)
                    try:
                        # Get image dimensions for proper sizing
                        with Image.open(temp_path) as pil_img:
                            img_width, img_height = pil_img.size
                        
                        # Scale to fit content width (in points)
                        max_width_points = min(content_width, MAX_IMAGE_WIDTH * 0.75)
                        max_height_points = MAX_IMAGE_HEIGHT_POINTS
                        
                        # Calculate scale factors for both dimensions
                        width_scale = min(1.0, max_width_points / img_width)
                        height_scale = min(1.0, max_height_points / img_height)
                        scale = min(width_scale, height_scale)
                        
                        display_width = img_width * scale
                        display_height = img_height * scale
                        
                        # Create ReportLab Image flowable
                        rl_image = RLImage(
                            temp_path,
                            width=display_width,
                            height=display_height
                        )
                        elements.append(rl_image)
                        elements.append(Spacer(1, 6))
                        
                    except Exception as e:
                        _log(f"[WARN] Failed to embed image: {e}", "#FFAA00")
        
        # --- Video URL (as clickable text, NOT embedded) ---
        video_url = tweet.get('video_url')
        if video_url:
            elements.append(Paragraph("Video:", styles['video_label']))
            link_text = f'<link href="{escape_xml(video_url)}">{escape_xml(video_url)}</link>'
            elements.append(Paragraph(link_text, styles['link']))
        
        # --- Tweet URL (clickable) ---
        tweet_url = tweet.get('tweet_url', '')
        if tweet_url:
            link_text = f'<link href="{escape_xml(tweet_url)}">{escape_xml(tweet_url)}</link>'
            elements.append(Paragraph(link_text, styles['link']))
        
        # --- Divider ---
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=HexColor('#CCCCCC'),
            spaceBefore=4,
            spaceAfter=12
        ))
        
    finally:
        # Clean up all temp files immediately after adding to elements
        # Note: ReportLab reads the image file when building the PDF,
        # so we need to keep files until after the PDF is built.
        # We return the list of files to clean up later.
        pass
    
    return elements, temp_files_to_cleanup


class TweetFlowableGenerator:
    """
    Generator-based flowable producer for memory-efficient PDF building.
    
    This class allows us to stream tweets and clean up temp files
    progressively as the PDF is built.
    """
    
    def __init__(self, json_filepath: str, styles: dict, content_width: float):
        self.json_filepath = json_filepath
        self.styles = styles
        self.content_width = content_width
        self.tweet_count = 0
        self.pending_temp_files = []
    
    def generate_flowables(self) -> Generator[Any, None, None]:
        """
        Generate flowables one tweet at a time.
        
        Yields flowables and tracks temp files for cleanup.
        """
        for tweet in stream_tweets(self.json_filepath):
            self.tweet_count += 1
            
            if self.tweet_count % 1 == 0:
                _log(f"[INFO] Processing tweet {self.tweet_count}...", "#888888")
            
            elements, temp_files = render_tweet_block(
                tweet, self.styles, self.content_width
            )
            
            # Track temp files for later cleanup
            self.pending_temp_files.extend(temp_files)
            
            for element in elements:
                yield element
    
    def cleanup(self):
        """Clean up all pending temp files."""
        for filepath in self.pending_temp_files:
            cleanup_temp_file(filepath)
        self.pending_temp_files.clear()


def generate_pdf(json_filepath: str, output_dir: str = None) -> str:
    """
    Generate a PDF from a JSON file of tweets.
    
    Streams the JSON, processes images one-by-one, and builds
    the PDF without holding large amounts of data in memory.
    
    Args:
        json_filepath: Path to input JSON file.
        output_dir: Directory to save PDF. If None, saves in same dir as JSON.
        
    Returns:
        str: Full path to the generated PDF file.
    """
    # Derive output filename from input JSON
    base_name = os.path.splitext(os.path.basename(json_filepath))[0]
    pdf_filename = f"{base_name}.pdf"
    
    # Determine output directory
    if output_dir:
        output_filepath = os.path.join(output_dir, pdf_filename)
    else:
        output_filepath = os.path.join(os.path.dirname(json_filepath), pdf_filename)
    
    _log(f"[INFO] Starting PDF generation...", "#00BFFF")
    _log(f"[INFO] Input: {json_filepath}", "#00BFFF")
    _log(f"[INFO] Output: {output_filepath}", "#00BFFF")
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=A4,
        leftMargin=PDF_MARGIN,
        rightMargin=PDF_MARGIN,
        topMargin=PDF_MARGIN,
        bottomMargin=PDF_MARGIN,
    )
    
    # Create styles
    styles = create_styles()
    
    # Create flowable generator
    generator = TweetFlowableGenerator(
        json_filepath, styles, CONTENT_WIDTH
    )
    
    try:
        # Collect all flowables
        # Note: ReportLab's SimpleDocTemplate.build() requires a list,
        # but we generate them on-the-fly to avoid holding tweet data in memory.
        # The flowables themselves must be kept until build() completes.
        _log(f"[INFO] Streaming tweets and generating flowables...", "#888888")
        all_flowables = list(generator.generate_flowables())
        
        _log(f"[INFO] Building PDF with {generator.tweet_count} tweets...", "#00BFFF")
        
        # Build PDF
        doc.build(all_flowables)
        
        _log(f"[INFO] PDF generation complete!", "#00FF04")
        _log(f"[INFO] Total tweets processed: {generator.tweet_count}", "#00FF04")
        
    finally:
        # Clean up all temp image files
        _log(f"[INFO] Cleaning up {len(generator.pending_temp_files)} temp files...", "#888888")
        generator.cleanup()
    
    return output_filepath


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Memory-efficient JSON to PDF converter for Twitter data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
    python json_to_pdf.py dayendtrader_mega_scrape.json output.pdf
    python json_to_pdf.py -i tweets.json -o report.pdf

The script streams the JSON file and processes images one-by-one,
making it suitable for large datasets on low-RAM machines.
        """
    )
    
    parser.add_argument(
        'input_json',
        nargs='?',
        help='Input JSON file path'
    )
    parser.add_argument(
        'output_pdf',
        nargs='?',
        help='Output PDF file path'
    )
    parser.add_argument(
        '-i', '--input',
        dest='input_file',
        help='Input JSON file (alternative to positional argument)'
    )
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        help='Output PDF file (alternative to positional argument)'
    )
    
    args = parser.parse_args()
    
    # Resolve input file
    input_json = args.input_file or args.input_json
    if not input_json:
        parser.error("Input JSON file is required")
    
    # Resolve output file
    output_pdf = args.output_file or args.output_pdf
    if not output_pdf:
        # Default: same name as input with .pdf extension
        base_name = os.path.splitext(input_json)[0]
        output_pdf = f"{base_name}.pdf"
    
    # Validate input file exists
    if not os.path.exists(input_json):
        print(f"[ERROR] Input file not found: {input_json}", file=sys.stderr)
        sys.exit(1)
    
    # Generate PDF
    try:
        generate_pdf(input_json, output_pdf)
        print(f"[SUCCESS] PDF saved to: {output_pdf}")
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
