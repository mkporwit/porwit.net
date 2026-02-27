"""
PDF generation for single cards - based on challenge.py
"""
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red, black
from models import get_challenge

PAGE_WIDTH, PAGE_HEIGHT = letter
CARD_WIDTH = 180
CARD_HEIGHT = 252
CORNER_RADIUS = 12

SUITS = {
    'Hearts': ('\u2665', red),
    'Diamonds': ('\u2666', red),
    'Clubs': ('\u2663', black),
    'Spades': ('\u2660', black)
}



def draw_joker(c, color, card_x, card_y):
    """Draw a Joker card."""
    if color == 'Red':
        c.setFillColor(red)
    else:
        c.setFillColor(black)

    c.setFont("Helvetica-Bold", 28)
    text_width = c.stringWidth("JOKER", "Helvetica-Bold", 28)
    center_x = card_x + CARD_WIDTH / 2
    center_y = card_y + CARD_HEIGHT / 2
    c.drawString(center_x - text_width / 2, center_y, "JOKER")

    c.setFont("Helvetica-Bold", 40)
    star = "\u2605"
    c.drawString(center_x - 15, center_y + 50, star)
    c.drawString(center_x - 15, center_y - 60, star)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(card_x + 12, card_y + CARD_HEIGHT - 28, "J")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(card_x + 10, card_y + CARD_HEIGHT - 44, "\u2605")

    c.saveState()
    c.translate(card_x + CARD_WIDTH - 12, card_y + 28)
    c.rotate(180)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0, 0, "J")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(-2, -16, "\u2605")
    c.restoreState()


def draw_pips(c, count, symbol, center_x, center_y):
    """Draw pip patterns for number cards."""
    c.setFont("Helvetica", 32)
    symbol_offset = 16

    pip_patterns = {
        2: [(0, 60), (0, -60)],
        3: [(0, 60), (0, 0), (0, -60)],
        4: [(-25, 60), (25, 60), (-25, -60), (25, -60)],
        5: [(-25, 60), (25, 60), (0, 0), (-25, -60), (25, -60)],
        6: [(-25, 60), (25, 60), (-25, 0), (25, 0), (-25, -60), (25, -60)],
        7: [(-25, 60), (25, 60), (0, 30), (-25, 0), (25, 0), (-25, -60), (25, -60)],
        8: [(-25, 60), (25, 60), (0, 30), (-25, 0), (25, 0), (0, -30), (-25, -60), (25, -60)],
        9: [(-25, 65), (25, 65), (-25, 25), (25, 25), (0, 0), (-25, -25), (25, -25), (-25, -65), (25, -65)],
        10: [(-25, 70), (25, 70), (0, 40), (-25, 20), (25, 20), (-25, -20), (25, -20), (0, -40), (-25, -70), (25, -70)]
    }

    positions = pip_patterns.get(count, [])
    for x_off, y_off in positions:
        c.drawString(center_x + x_off - symbol_offset, center_y + y_off - 12, symbol)


def draw_standard_card(c, rank, suit, card_x, card_y):
    """Draw a standard playing card."""
    symbol, color = SUITS[suit]
    c.setFillColor(color)

    c.setFont("Helvetica-Bold", 22)
    c.drawString(card_x + 12, card_y + CARD_HEIGHT - 32, rank)
    c.setFont("Helvetica", 24)
    c.drawString(card_x + 10, card_y + CARD_HEIGHT - 56, symbol)

    c.saveState()
    c.translate(card_x + CARD_WIDTH - 12, card_y + 32)
    c.rotate(180)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(0, 0, rank)
    c.setFont("Helvetica", 24)
    c.drawString(-2, -24, symbol)
    c.restoreState()

    center_x = card_x + CARD_WIDTH / 2
    center_y = card_y + CARD_HEIGHT / 2

    if rank in ['J', 'Q', 'K']:
        c.setFont("Helvetica-Bold", 72)
        text_width = c.stringWidth(rank, "Helvetica-Bold", 72)
        c.drawString(center_x - text_width / 2, center_y - 10, rank)
        c.setFont("Helvetica", 36)
        c.drawString(center_x - 12, center_y - 55, symbol)
    elif rank == 'A':
        c.setFont("Helvetica", 100)
        c.drawString(center_x - 30, center_y - 30, symbol)
    else:
        draw_pips(c, int(rank), symbol, center_x, center_y)


def draw_card(c, rank, suit, page_width, page_height):
    """Draw a single card centered on the page."""
    card_x = (page_width - CARD_WIDTH) / 2
    card_y = (page_height - CARD_HEIGHT) / 2

    c.setStrokeColor(black)
    c.setLineWidth(2)
    c.setFillColor('white')
    c.roundRect(card_x, card_y, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, stroke=1, fill=1)

    if rank == 'JOKER':
        draw_joker(c, suit, card_x, card_y)
    else:
        draw_standard_card(c, rank, suit, card_x, card_y)


def generate_card_pdf(rank: str, suit: str, week_info: str = None) -> bytes:
    """
    Generate a PDF for a single card.
    Returns the PDF as bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    draw_card(c, rank, suit, PAGE_WIDTH, PAGE_HEIGHT)

    # Add challenge description below the card
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 14)
    description = get_challenge(rank)
    desc_width = c.stringWidth(description, "Helvetica-Bold", 14)
    c.drawString(PAGE_WIDTH / 2 - desc_width / 2, 50, description)

    # Add week info if provided
    if week_info:
        c.setFont("Helvetica", 10)
        week_width = c.stringWidth(week_info, "Helvetica", 10)
        c.drawString(PAGE_WIDTH / 2 - week_width / 2, 30, week_info)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
