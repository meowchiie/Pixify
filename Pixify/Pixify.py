import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, Tk, Button, Label, Frame, Toplevel, StringVar, OptionMenu
from PIL import Image, ImageTk, ImageDraw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

# --- Inisialisasi ---
root = Tk()
root.title("Pixify ✨")
root.geometry("1000x700")

# --- Background gradasi ---
gradient_colors = ["#F593D0", "#DB67F8", "#5F60A5"]
canvas = tk.Canvas(root, width=1000, height=700, highlightthickness=0)
canvas.place(relwidth=1, relheight=1)

def create_gradient_image(width, height, colors):
    image = Image.new("RGB", (width, height), colors[0])
    draw = ImageDraw.Draw(image)
    r1, g1, b1 = Image.new("RGB", (1, 1), colors[0]).getpixel((0, 0))
    r2, g2, b2 = Image.new("RGB", (1, 1), colors[-1]).getpixel((0, 0))
    for i in range(height):
        r = int(r1 + (r2 - r1) * i / height)
        g = int(g1 + (g2 - g1) * i / height)
        b = int(b1 + (b2 - b1) * i / height)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    return image

bg_label = Label(root)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

def update_gradient(event=None):
    width = root.winfo_width()
    height = root.winfo_height()
    gradient_img = create_gradient_image(width, height, gradient_colors)
    photo = ImageTk.PhotoImage(gradient_img)
    bg_label.config(image=photo)
    bg_label.image = photo

root.bind("<Configure>", update_gradient)
update_gradient()

# --- Variabel global ---
original_img = None
processed_img = None
input_label = None
output_label = None
DISPLAY_SIZE = (400, 300)
MAX_IMAGE_SIZE = (800, 800)

# --- Fungsi utilitas ---
def resize_image_for_display(img):
    h, w = img.shape[:2]
    scale = min(DISPLAY_SIZE[0] / w, DISPLAY_SIZE[1] / h, 1.0)
    return cv2.resize(img, (int(w * scale), int(h * scale)))

def resize_for_processing(img):
    h, w = img.shape[:2]
    if h > MAX_IMAGE_SIZE[1] or w > MAX_IMAGE_SIZE[0]:
        scale = min(MAX_IMAGE_SIZE[0] / w, MAX_IMAGE_SIZE[1] / h)
        return cv2.resize(img, (int(w * scale), int(h * scale)))
    return img

def run_in_thread(func):
    def wrapper():
        threading.Thread(target=func).start()
    return wrapper

def show_images():
    global input_label, output_label
    for label in [input_label, output_label]:
        if label:
            label.destroy()

    img_input = resize_image_for_display(original_img)
    img_output = resize_image_for_display(processed_img)

    input_imgtk = ImageTk.PhotoImage(Image.fromarray(img_input))
    output_imgtk = ImageTk.PhotoImage(Image.fromarray(img_output))

    input_label = Label(img_frame, image=input_imgtk, bg="white", relief="solid", bd=1)
    input_label.image = input_imgtk
    input_label.grid(row=1, column=0, padx=10, pady=10)

    output_label = Label(img_frame, image=output_imgtk, bg="white", relief="solid", bd=1)
    output_label.image = output_imgtk
    output_label.grid(row=1, column=1, padx=10, pady=10)

# --- Fungsi Proses ---
def upload_gambar():
    global original_img, processed_img
    filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
    if filepath:
        img_bgr = cv2.imread(filepath)
        if img_bgr is None:
            return
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_rgb = resize_for_processing(img_rgb)
        original_img = img_rgb.copy()
        processed_img = img_rgb.copy()
        show_images()
        # Munculkan elemen-elemen yang disembunyikan
        process_frame.pack(pady=10)
        dropdown.pack(pady=5)
        apply_btn.pack(pady=5)
        action_frame.pack(pady=10)

def apply_process():
    global processed_img
    if original_img is None:
        return
    img = original_img.copy()
    choice = selected_option.get()

    if choice == "Grayscale":
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        processed_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    elif choice == "Binary":
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        processed_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
    elif choice == "+ Brightness":
        processed_img = cv2.convertScaleAbs(img, alpha=1, beta=30)
    elif choice == "Operasi AND":
        dummy = np.ones_like(img) * 127
        processed_img = cv2.bitwise_and(img, dummy.astype(np.uint8))
    elif choice == "Sharpen":
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        processed_img = cv2.filter2D(img, -1, kernel)
    elif choice == "Dilasi":
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(gray, kernel, iterations=1)
        processed_img = cv2.cvtColor(dilated, cv2.COLOR_GRAY2RGB)

    show_images()

def reset():
    global processed_img
    if original_img is not None:
        processed_img = original_img.copy()
        show_images()

def simpan():
    filepath = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
    if filepath:
        cv2.imwrite(filepath, cv2.cvtColor(processed_img, cv2.COLOR_RGB2BGR))

@run_in_thread
def tampilkan_histogram():
    chans = cv2.split(processed_img)
    colors = ("b", "g", "r")
    fig, ax = plt.subplots()
    for chan, color in zip(chans, colors):
        hist = cv2.calcHist([chan], [0], None, [256], [0, 256])
        ax.plot(hist, color=color)
    ax.set_title("Histogram RGB")
    popup = Toplevel(root)
    popup.title("Histogram RGB")
    canvas = FigureCanvasTkAgg(fig, master=popup)
    canvas.draw()
    canvas.get_tk_widget().pack()

# --- UI Awal ---
judul_text = Label(root, text="Pixify ✨", font=("Segoe UI", 24, "bold"), fg="#833FC2", bg="white")
judul_text.pack(pady=(30, 20))

# Tombol awal saja
Button(root, text="Upload Gambar", command=upload_gambar, width=20, bg="#F4B3DB", font=("Segoe UI", 10)).pack(pady=10)

# --- Frame yang disembunyikan dulu ---
process_frame = Frame(root, bg="white")

# Dropdown + opsi proses
selected_option = StringVar(root)
selected_option.set("Pilih")
options = [
    "Grayscale", "Binary", "+ Brightness",
    "Operasi AND", "Sharpen", "Dilasi"
]
dropdown = OptionMenu(process_frame, selected_option, *options)
dropdown.config(width=20, font=("Segoe UI", 10))

apply_btn = Button(process_frame, text="Terapkan Proses", command=apply_process, bg="#F4B3DB", font=("Segoe UI", 10, "bold"))

# Frame gambar
img_frame = Frame(process_frame, bg="white")
img_frame.pack(pady=10)
Label(img_frame, text="Input", font=("Segoe UI", 12, "bold"), bg="white").grid(row=0, column=0)
Label(img_frame, text="Output", font=("Segoe UI", 12, "bold"), bg="white").grid(row=0, column=1)

# Tombol bawah (histogram dll)
action_frame = Frame(process_frame, bg="white")
Button(action_frame, text="Reset", command=reset, width=18, bg="#F4B3DB").grid(row=0, column=2, padx=5, pady=5)
Button(action_frame, text="Simpan", command=simpan, width=18, bg="#F4B3DB").grid(row=0, column=1, padx=5, pady=5)
Button(action_frame, text="Histogram RGB", command=tampilkan_histogram, width=18, bg="#F4B3DB").grid(row=0, column=0, padx=5, pady=5)

# --- Jalankan GUI ---
root.mainloop()
