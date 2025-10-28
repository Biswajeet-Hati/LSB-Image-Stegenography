from typing import Tuple
from PIL import Image

HEADER_BITS = 32  # 32-bit unsigned length header (number of payload bytes)


def _ensure_rgb(image: Image.Image) -> Image.Image:
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def _bytes_to_bits(data: bytes) -> list[int]:
    bits: list[int] = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
    if len(bits) % 8 != 0:
        raise ValueError("Bit length must be a multiple of 8")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i:i+8]:
            byte = (byte << 1) | (bit & 1)
        out.append(byte)
    return bytes(out)


def _capacity_bits(image: Image.Image) -> int:
    w, h = image.size
    channels = 3  # R, G, B
    return w * h * channels


def _iter_pixels(image: Image.Image):
    pixels = image.load()
    w, h = image.size
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            yield x, y, r, g, b


def encode_message(input_path: str, output_path: str, message: str) -> Tuple[int, int]:
    """
    Encode a UTF-8 message into a PNG (recommended) using LSB.

    Returns a tuple (used_bits, capacity_bits).
    """
    with Image.open(input_path) as img_open:
        img = _ensure_rgb(img_open)
        cap = _capacity_bits(img)
        payload = message.encode("utf-8")
        length_bytes = len(payload).to_bytes(4, byteorder="big", signed=False)
        data_bits = _bytes_to_bits(length_bytes + payload)
        need = len(data_bits)
        if need > cap:
            raise ValueError(f"Message too large. Need {need} bits but only {cap} bits available.")

        out = img.copy()
        pixels = out.load()

        bit_i = 0
        for x, y, r, g, b in _iter_pixels(img):
            if bit_i >= need:
                break
            # modify R
            if bit_i < need:
                r = (r & 0xFE) | data_bits[bit_i]
                bit_i += 1
            # modify G
            if bit_i < need:
                g = (g & 0xFE) | data_bits[bit_i]
                bit_i += 1
            # modify B
            if bit_i < need:
                b = (b & 0xFE) | data_bits[bit_i]
                bit_i += 1
            pixels[x, y] = (r, g, b)

        out.save(output_path)
        return need, cap


def decode_message(input_path: str) -> str:
    """
    Decode a UTF-8 message from an image previously encoded with this module.
    """
    with Image.open(input_path) as img_open:
        img = _ensure_rgb(img_open)
        cap = _capacity_bits(img)
        if cap < HEADER_BITS:
            raise ValueError("Image too small or invalid for decoding")

        # First read 32 bits for payload length
        header_bits: list[int] = []
        payload_len = None
        pixels = img.load()
        w, h = img.size

        bit_stream = []
        for _, _, r, g, b in _iter_pixels(img):
            bit_stream.append(r & 1)
            bit_stream.append(g & 1)
            bit_stream.append(b & 1)

        header_bits = bit_stream[:HEADER_BITS]
        length_bytes = _bits_to_bytes(header_bits)
        payload_len = int.from_bytes(length_bytes, byteorder="big", signed=False)

        total_needed = HEADER_BITS + payload_len * 8
        if total_needed > len(bit_stream):
            raise ValueError("Encoded payload exceeds image capacity or file is not encoded with this tool")

        payload_bits = bit_stream[HEADER_BITS:total_needed]
        payload = _bits_to_bytes(payload_bits)
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to latin-1 to avoid crash; user can reinterpret
            return payload.decode("latin-1")
