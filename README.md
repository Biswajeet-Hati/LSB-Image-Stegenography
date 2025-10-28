# LSB Image Steganography (Streamlit)

Simple LSB-based steganography tool with a Streamlit web UI. It lets you:

- Encode a text message into an image (PNG/BMP recommended).
- Decode a text message from an image created by this tool.

## Features

- 32-bit header stores message length.
- Uses RGB LSBs (1 bit per channel) for capacity of `width * height * 3` bits.
- Shows approximate capacity (in bytes) when you select an image.

## Requirements

- Python 3.10+
- Pillow
- Streamlit

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
# Option 1: Run Streamlit directly
python -m streamlit run app.py

# Option 2: Use the launcher
python main.py
```

## Usage Notes

- Prefer lossless formats (PNG/BMP). JPEG is lossy and can destroy embedded data; only use if you do not re-save after encoding.
- Maximum message size is roughly `(width * height * 3 - 32) / 8` bytes for the selected image.
- Decoding expects images encoded by this project (32-bit big-endian length header followed by UTF-8 payload).
