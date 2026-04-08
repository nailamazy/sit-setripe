import re
import random


def parse_card(text: str) -> dict:
    """Parse a single card line into components."""
    text = text.strip()
    parts = re.split(r'[|:/\\\-\s]+', text)
    if len(parts) < 4:
        return None
    cc = re.sub(r'\D', '', parts[0])
    if not (15 <= len(cc) <= 19):
        return None
    month = parts[1].strip()
    if len(month) == 1:
        month = f"0{month}"
    if not (len(month) == 2 and month.isdigit() and 1 <= int(month) <= 12):
        return None
    year = parts[2].strip()
    if len(year) == 4:
        year = year[2:]
    if len(year) != 2:
        return None
    cvv = re.sub(r'\D', '', parts[3])
    if not (3 <= len(cvv) <= 4):
        return None
    return {"cc": cc, "month": month, "year": year, "cvv": cvv}


def parse_cards(text: str) -> list:
    """Parse multiple card lines from text."""
    cards = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line:
            card = parse_card(line)
            if card:
                cards.append(card)
    return cards


def luhn_checksum(card_number: str) -> int:
    """Calculate Luhn checksum digit."""
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10


def generate_luhn_card(prefix: str, length: int = 16) -> str:
    """Generate a card number with valid Luhn checksum."""
    remaining = length - len(prefix) - 1
    if remaining < 0:
        remaining = 0
    body = prefix + ''.join([str(random.randint(0, 9)) for _ in range(remaining)])
    check_sum = luhn_checksum(body + '0')
    check_digit = (10 - check_sum) % 10
    return body + str(check_digit)


def generate_cards_from_bin(bin_str: str, count: int = 10) -> list:
    """Generate random cards from a BIN prefix (6-12 digits). Max 10 cards."""
    bin_str = re.sub(r'\D', '', bin_str)
    if len(bin_str) < 6 or len(bin_str) > 12:
        return []

    count = min(count, 10)
    cards = []
    generated_numbers = set()

    # Determine card length based on BIN
    if bin_str.startswith('3'):
        card_length = 15  # Amex
    else:
        card_length = 16

    # Determine CVV length
    cvv_length = 4 if bin_str.startswith('3') else 3

    attempts = 0
    while len(cards) < count and attempts < 100:
        attempts += 1
        cc = generate_luhn_card(bin_str, card_length)
        if cc in generated_numbers:
            continue
        generated_numbers.add(cc)

        month = f"{random.randint(1, 12):02d}"
        year = f"{random.randint(26, 35)}"
        cvv = ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])

        cards.append({
            "cc": cc,
            "month": month,
            "year": year,
            "cvv": cvv
        })

    return cards


def is_bin_input(text: str) -> bool:
    """Check if text looks like a BIN (6-12 digits only)."""
    cleaned = re.sub(r'\D', '', text.strip())
    return 6 <= len(cleaned) <= 12
