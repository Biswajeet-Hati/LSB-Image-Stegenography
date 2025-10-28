import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from PIL import Image

from stego import encode_message, decode_message, _capacity_bits, _ensure_rgb


class StegoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSB Image Steganography")
        self.geometry("760x560")
        self.minsize(720, 520)
        self._setup_style()

        self.selected_image_path: str | None = None
        self.mode = tk.StringVar(value="encode")

        self._build_ui()

    def _setup_style(self):
        style = ttk.Style(self)
        # Use a modern-looking theme if available; fallback to 'clam'
        try:
            style.theme_use("vista")
        except tk.TclError:
            try:
                style.theme_use("xpnative")
            except tk.TclError:
                style.theme_use("clam")

        # Base font sizing
        default_font = ("Segoe UI", 10)
        heading_font = ("Segoe UI Semibold", 12)

        style.configure("TLabel", font=default_font)
        style.configure("TButton", font=default_font, padding=(10, 6))
        style.configure("TRadiobutton", font=default_font, padding=4)
        style.configure("TFrame", padding=10)
        style.configure("Card.TFrame", padding=12)
        style.configure("Card.TLabelframe", padding=12)
        style.configure("Card.TLabelframe.Label", font=heading_font)

    def _build_ui(self):
        # Header
        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill=tk.X)

        title = ttk.Label(header, text="LSB Image Steganography", font=("Segoe UI Semibold", 14))
        title.pack(side=tk.LEFT)

        self.lbl_capacity = ttk.Label(header, text="")
        self.lbl_capacity.pack(side=tk.RIGHT)

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X)

        btn_select = ttk.Button(toolbar, text="Select Image...", command=self.on_select_image)
        btn_select.pack(side=tk.LEFT)

        self.lbl_image = ttk.Label(toolbar, text="No image selected", foreground="#666")
        self.lbl_image.pack(side=tk.LEFT, padx=12)

        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill=tk.X, pady=(0, 4))
        ttk.Radiobutton(mode_frame, text="Encode", variable=self.mode, value="encode", command=self.on_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Decode", variable=self.mode, value="decode", command=self.on_mode_change).pack(side=tk.LEFT, padx=(8, 0))

        # Message card
        msg_frame = ttk.Labelframe(self, text="Message", style="Card.TLabelframe")
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.txt_message = ScrolledText(msg_frame, height=16, wrap=tk.WORD, font=("Consolas", 10))
        self.txt_message.pack(fill=tk.BOTH, expand=True)

        # Footer actions
        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X)

        self.btn_action = ttk.Button(bottom, text="Encode and Save...", command=self.on_action)
        self.btn_action.pack(side=tk.LEFT)

        self.btn_clear = ttk.Button(bottom, text="Clear Message", command=self.on_clear)
        self.btn_clear.pack(side=tk.LEFT, padx=8)

    def on_mode_change(self):
        if self.mode.get() == "encode":
            self.btn_action.configure(text="Encode and Save...")
            self.txt_message.configure(state=tk.NORMAL)
        else:
            self.btn_action.configure(text="Decode Message")
            self.txt_message.delete("1.0", tk.END)
            self.txt_message.configure(state=tk.NORMAL)

    def on_select_image(self):
        filetypes = [
            ("Image files", "*.png;*.bmp;*.jpg;*.jpeg"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select image", filetypes=filetypes)
        if not path:
            return
        try:
            with Image.open(path) as img_open:
                img = _ensure_rgb(img_open)
                cap_bits = _capacity_bits(img)
                cap_bytes = (cap_bits - 32) // 8 if cap_bits >= 32 else 0
            self.selected_image_path = path
            self.lbl_image.configure(text=os.path.basename(path))
            self.lbl_capacity.configure(text=f"Capacity: ~{cap_bytes} bytes")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")

    def on_clear(self):
        self.txt_message.delete("1.0", tk.END)

    def on_action(self):
        if not self.selected_image_path:
            messagebox.showwarning("Missing", "Please select an image first.")
            return

        if self.mode.get() == "encode":
            self.encode_flow()
        else:
            self.decode_flow()

    def encode_flow(self):
        msg = self.txt_message.get("1.0", tk.END).rstrip("\n")
        if not msg:
            messagebox.showwarning("Missing", "Enter a message to encode.")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("BMP image", "*.bmp"), ("All files", "*.*")],
            title="Save encoded image as"
        )
        if not save_path:
            return
        try:
            used, cap = encode_message(self.selected_image_path, save_path, msg)
            used_bytes = max(0, used - 32) // 8
            cap_bytes = max(0, cap - 32) // 8
            messagebox.showinfo("Success", f"Message encoded.\nUsed: {used_bytes} / {cap_bytes} bytes")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to encode message:\n{e}")

    def decode_flow(self):
        try:
            text = decode_message(self.selected_image_path)
            self.txt_message.delete("1.0", tk.END)
            self.txt_message.insert(tk.END, text)
            messagebox.showinfo("Decoded", "Message decoded and shown in the text box.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to decode message:\n{e}")


if __name__ == "__main__":
    app = StegoApp()
    app.mainloop()
