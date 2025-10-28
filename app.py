import io
import os
import tempfile
from typing import Optional

import streamlit as st
from PIL import Image

from stego import encode_message, decode_message, _capacity_bits, _ensure_rgb


st.set_page_config(page_title="LSB Image Steganography", page_icon="🖼️", layout="centered")
st.title("LSB Image Steganography")
st.caption("Hide and reveal messages in images using least significant bit (LSB) technique.")

mode = st.radio("Mode", options=["Encode", "Decode"], horizontal=True)
uploaded_file = st.file_uploader("Select an image", type=["png", "bmp", "jpg", "jpeg"]) 

if uploaded_file is not None:
    try:
        img_open = Image.open(uploaded_file)
        img = _ensure_rgb(img_open)
        cap_bits = _capacity_bits(img)
        cap_bytes = (cap_bits - 32) // 8 if cap_bits >= 32 else 0
        st.info(f"Approx. capacity: {cap_bytes} bytes")
        st.image(img, caption="Selected Image", use_container_width=True)
    except Exception as e:
        st.error(f"Failed to open image: {e}")
        st.stop()

if mode == "Encode":
    message = st.text_area("Message to encode", height=180, placeholder="Type your secret message here...")
    col1, col2 = st.columns([1, 1])
    out_fmt = col1.selectbox("Output format", options=["png", "bmp"], index=0)
    out_name: str = col2.text_input("Output filename (without extension)", value="encoded")

    if st.button("Encode and Download", type="primary", disabled=(uploaded_file is None)):
        if uploaded_file is None:
            st.warning("Please select an image first.")
            st.stop()
        if not message:
            st.warning("Please enter a message to encode.")
            st.stop()
        try:
            with tempfile.TemporaryDirectory() as td:
                # Persist input to disk for the existing API
                in_suffix = os.path.splitext(uploaded_file.name or "input.png")[1] or ".png"
                in_path = os.path.join(td, f"input{in_suffix}")
                with open(in_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                out_path = os.path.join(td, f"output.{out_fmt}")
                used_bits, capacity_bits = encode_message(in_path, out_path, message)

                with open(out_path, "rb") as f:
                    out_bytes = f.read()

            used_bytes = max(0, used_bits - 32) // 8
            cap_bytes = max(0, capacity_bits - 32) // 8
            st.success(f"Message encoded. Used {used_bytes} / {cap_bytes} bytes")
            st.download_button(
                "Download encoded image",
                data=out_bytes,
                file_name=f"{(out_name or 'encoded').strip()}.{out_fmt}",
                mime=f"image/{'png' if out_fmt == 'png' else 'bmp'}",
            )
        except Exception as e:
            st.error(f"Failed to encode message: {e}")

else:  # Decode
    if st.button("Decode Message", disabled=(uploaded_file is None)):
        if uploaded_file is None:
            st.warning("Please select an image first.")
            st.stop()
        try:
            with tempfile.TemporaryDirectory() as td:
                in_suffix = os.path.splitext(uploaded_file.name or "input.png")[1] or ".png"
                in_path = os.path.join(td, f"input{in_suffix}")
                with open(in_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                text = decode_message(in_path)
            st.success("Message decoded below:")
            st.text_area("Decoded Message", value=text, height=180)
        except Exception as e:
            st.error(f"Failed to decode message: {e}")
