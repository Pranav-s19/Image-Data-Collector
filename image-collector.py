import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import time
import os

# ---------------- Main Window ----------------
root = tk.Tk()
root.title("Camera Dataset Tool")
root.geometry("1100x750")

# ---------------- Variables ----------------
save_path = tk.StringVar(value=os.getcwd())
img_size = tk.StringVar(value="640x480")
selected_camera = tk.IntVar(value=0)

auto_capture = False
cap = None

crop_enabled = tk.BooleanVar(value=False)
crop_coords = None
start_x = start_y = 0

# ---------------- Image Size Options ----------------
SIZE_MAP = {
    "320x240": (320, 240),
    "640x480": (640, 480),
    "800x600": (800, 600),
    "1280x720": (1280, 720),
}

# ---------------- Detect Cameras ----------------
def get_available_cameras(max_tested=5):
    available = []
    for i in range(max_tested):
        test_cap = cv2.VideoCapture(i)
        if test_cap.read()[0]:
            available.append(i)
        test_cap.release()
    return available

# ---------------- Camera Setup ----------------
def open_camera(index):
    global cap
    if cap:
        cap.release()
    cap = cv2.VideoCapture(index)

# ---------------- Camera Display ----------------
camera_label = tk.Label(root, bg="black")
camera_label.pack(pady=10)

def update_frame():
    global crop_coords

    if cap is None:
        root.after(100, update_frame)
        return

    ret, frame = cap.read()
    if ret:
        w, h = SIZE_MAP[img_size.get()]
        frame = cv2.resize(frame, (w, h))

        display_frame = frame.copy()
        
        # Draw temporary yellow box while dragging
        if crop_enabled.get() and drag_coords:
            x1, y1, x2, y2 = drag_coords
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0,255,255), 2)  # Yellow

        # Draw final green box after selection
        elif crop_enabled.get() and crop_coords:
            x1, y1, x2, y2 = crop_coords
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0,255,0), 2)  # Green


        rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)

    if auto_capture:
        capture_image()

    root.after(500 if auto_capture else 20, update_frame)

# ---------------- Cropping ----------------
crop_coords = None
drag_coords = None
start_x = start_y = 0
is_dragging = False

def start_crop(event):
    global start_x, start_y, is_dragging, drag_coords
    if crop_enabled.get():
        start_x = event.x
        start_y = event.y
        is_dragging = True
        drag_coords = None

def update_crop(event):
    global drag_coords
    if crop_enabled.get() and is_dragging:
        drag_coords = (start_x, start_y, event.x, event.y)

def end_crop(event):
    global crop_coords, is_dragging, drag_coords
    if crop_enabled.get() and is_dragging:
        crop_coords = (start_x, start_y, event.x, event.y)
        drag_coords = None
        is_dragging = False

camera_label.bind("<ButtonPress-1>", start_crop)
camera_label.bind("<B1-Motion>", update_crop)
camera_label.bind("<ButtonRelease-1>", end_crop)

# ---------------- Capture ----------------
def capture_image():
    ret, frame = cap.read()
    if not ret:
        return

    w, h = SIZE_MAP[img_size.get()]
    frame = cv2.resize(frame, (w, h))

    if crop_enabled.get() and crop_coords:
        x1, y1, x2, y2 = crop_coords
        frame = frame[min(y1,y2):max(y1,y2), min(x1,x2):max(x1,x2)]

    filename = f"img_{int(time.time()*1000)}.png"
    filepath = os.path.join(save_path.get(), filename)
    cv2.imwrite(filepath, frame)

# ---------------- Auto Capture ----------------
def start_auto_capture():
    global auto_capture
    auto_capture = True

def stop_auto_capture():
    global auto_capture
    auto_capture = False

# ---------------- Folder Selection ----------------
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        save_path.set(folder)

# ---------------- Controls ----------------
controls = tk.Frame(root)
controls.pack(pady=10)

# Camera dropdown
available_cams = get_available_cameras()
tk.Label(controls, text="Camera:").grid(row=0, column=0, padx=5)
camera_menu = tk.OptionMenu(
    controls,
    selected_camera,
    *available_cams,
    command=lambda x: open_camera(selected_camera.get())
)
camera_menu.grid(row=0, column=1, padx=5)

# Image size menu
tk.Label(controls, text="Image Size:").grid(row=0, column=2, padx=5)
size_menu = tk.OptionMenu(controls, img_size, *SIZE_MAP.keys())
size_menu.grid(row=0, column=3, padx=5)

# Crop checkbox
tk.Checkbutton(controls, text="Enable Crop", variable=crop_enabled).grid(row=0, column=4, padx=10)

# Folder
tk.Button(controls, text="Select Folder", command=select_folder).grid(row=1, column=0, padx=5, pady=5)
tk.Label(controls, textvariable=save_path, width=50, anchor="w").grid(row=1, column=1, columnspan=4)

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Capture Image", width=15, command=capture_image).grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="Start Auto Capture", width=18, command=start_auto_capture).grid(row=0, column=1, padx=10)
tk.Button(btn_frame, text="Stop", width=10, command=stop_auto_capture).grid(row=0, column=2, padx=10)

# ---------------- Start ----------------
if available_cams:
    open_camera(available_cams[0])
else:
    messagebox.showerror("Error", "No camera found!")

def on_close():
    if cap:
        cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
update_frame()
root.mainloop()