import wcocr
import os
from find_wechat_path import find_wechat_path, find_wechatocr_exe
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, font
from PIL import Image, ImageTk

# Initialize global variables
rects = []
rect_id = None
start_x = start_y = 0

def wechat_ocr(image_path, rects=None):
    wechat_path = find_wechat_path()
    wechatocr_path = find_wechatocr_exe()

    wcocr.init(wechatocr_path, wechat_path)
    result = wcocr.ocr(image_path)

    if rects:
        rect_texts = []
        image = Image.open(image_path)
        image_width, image_height = image.size
        for rect in rects:
            x, y, w, h = rect
            if x < 0 or y < 0 or x + w > image_width or y + h > image_height:
                continue
            roi = image.crop((x, y, x + w, y + h))
            roi_path = "temp_roi.png"
            roi.save(roi_path)
            roi_result = wcocr.ocr(roi_path)
            rect_text = ""
            for temp in roi_result['ocr_response']:
                rect_text += temp['text'] + "\n"
            rect_texts.append(rect_text)

        show_message(rect_texts_only=rect_texts)
    else:
        ocr_text = ""
        for temp in result['ocr_response']:
            ocr_text += temp['text'] + "\n"
        show_message(ocr_text=ocr_text)

def show_message(ocr_text=None, rect_texts_only=None):
    if ocr_text is not None:
        result_window = tk.Toplevel()
        result_window.title("全局识别结果")
        result_window.geometry("600x500")

        frame = tk.Frame(result_window)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        text_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=70, height=20)
        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, ocr_text)
        text_area.config(state=tk.NORMAL)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame, command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area['yscrollcommand'] = scrollbar.set

        create_text_area_with_font_options(result_window, text_area)

    elif rect_texts_only:
        rect_text_window = tk.Toplevel()
        rect_text_window.title("矩形区域识别结果")
        rect_text_window.geometry("600x500")

        frame = tk.Frame(rect_text_window)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        rect_text_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=70, height=20)
        rect_text_area.config(state=tk.NORMAL)
        rect_text_area.delete(1.0, tk.END)
        for rect_text in rect_texts_only:
            rect_text_area.insert(tk.INSERT, rect_text + "\n")
        rect_text_area.config(state=tk.NORMAL)
        rect_text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame, command=rect_text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        rect_text_area['yscrollcommand'] = scrollbar.set

        create_text_area_with_font_options(rect_text_window, rect_text_area)

def create_text_area_with_font_options(parent, text_area):
    font_size = tk.IntVar(value=12)
    font_family = tk.StringVar(value="宋体")

    menu = tk.Menu(parent, tearoff=0)
    menu.add_command(label="复制", command=lambda: text_area.event_generate("<<Copy>>"))
    menu.add_command(label="全选", command=lambda: text_area.event_generate("<<SelectAll>>"))

    prioritized_fonts = ["宋体", "楷体", "微软雅黑", "Times New Roman"]
    font_families = prioritized_fonts + [f for f in font.families() if f not in prioritized_fonts]

    def update_font(widget, family, size):
        current_font = font.Font(family=family.get(), size=size.get())
        widget.config(font=current_font)

    font_menu = tk.OptionMenu(parent, font_family, *prioritized_fonts, command=lambda _: update_font(text_area, font_family, font_size))
    font_menu.pack(side=tk.LEFT, padx=10, pady=10)

    size_spinbox = tk.Spinbox(parent, from_=8, to=72, textvariable=font_size, command=lambda: update_font(text_area, font_family, font_size))
    size_spinbox.pack(side=tk.LEFT, padx=10, pady=10)

    size_spinbox.bind("<Return>", lambda event: update_font(text_area, font_family, font_size))

    def show_all_fonts():
        font_menu['menu'].delete(0, 'end')
        for font_name in font_families:
            font_menu['menu'].add_command(label=font_name, command=tk._setit(font_family, font_name, lambda _: update_font(text_area, font_family, font_size)))

    show_all_fonts_button = tk.Menubutton(parent, text="显示全部字体", relief=tk.RAISED)
    show_all_fonts_button.menu = tk.Menu(show_all_fonts_button, tearoff=0)
    show_all_fonts_button["menu"] = show_all_fonts_button.menu

    for font_name in font_families:
        show_all_fonts_button.menu.add_command(label=font_name, command=tk._setit(font_family, font_name, lambda _: update_font(text_area, font_family, font_size)))

    show_all_fonts_button.pack(side=tk.LEFT, padx=10, pady=10)

    def show_menu(event):
        menu.post(event.x_root, event.y_root)

    text_area.bind("<Button-3>", show_menu)

def load_image():
    file_path = filedialog.askopenfilename(
        title="选择图片文件",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
    )
    if file_path:
        image_path.set(file_path)
        display_image(file_path)

def display_image(file_path):
    image = Image.open(file_path)
    photo = ImageTk.PhotoImage(image)

    canvas.config(width=photo.width(), height=photo.height())
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo

def start_rect_ocr():
    if image_path.get() and rects:
        wechat_ocr(image_path.get(), rects)
    else:
        messagebox.showwarning("警告", "请先选择图片并绘制矩形区域")

def start_global_ocr():
    if image_path.get():
        wechat_ocr(image_path.get())
    else:
        messagebox.showwarning("警告", "请先选择图片")

def on_canvas_click(event):
    global start_x, start_y
    start_x, start_y = event.x, event.y

def on_canvas_drag(event):
    global rect_id
    if rect_id:
        canvas.delete(rect_id)
    rect_id = canvas.create_rectangle(start_x, start_y, event.x, event.y, outline='green')

def on_canvas_release(event):
    global rects, rect_id
    end_x, end_y = event.x, event.y
    rects.append((start_x, start_y, end_x - start_x, end_y - start_y))
    rect_id = None

# Create main window
root = tk.Tk()
root.title("OCR 图片识别")
root.geometry("600x400")

image_path = tk.StringVar()

# Load Image Button
load_button = tk.Button(root, text="载入图片", command=load_image)
load_button.pack(padx=10, pady=10)

# Start Global OCR Button
global_ocr_button = tk.Button(root, text="全局识别", command=start_global_ocr)
global_ocr_button.pack(padx=10, pady=10)

# Start Rectangular OCR Button
rect_ocr_button = tk.Button(root, text="矩形识别", command=start_rect_ocr)
rect_ocr_button.pack(padx=10, pady=10)

# Create Canvas for Image Display
canvas = tk.Canvas(root, bg="white")
canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
canvas.bind("<Button-1>", on_canvas_click)
canvas.bind("<B1-Motion>", on_canvas_drag)
canvas.bind("<ButtonRelease-1>", on_canvas_release)

# Start the application
root.mainloop()
