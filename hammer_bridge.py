import ctypes
from ctypes import wintypes
import time
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def _attach_desktop():
    hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
    if hdesk:
        user32.SetThreadDesktop(hdesk)
    return hdesk

def find_hammer_window():
    _attach_desktop()
    found = []
    
    def cb(h, l):
        if not user32.IsWindowVisible(h):
            return True
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(h, cls, 256)
        c_name = cls.value.lower()
        if "hammmerplusplus" in c_name or "hammer" in c_name:
            len_t = user32.GetWindowTextLengthW(h)
            buf = ctypes.create_unicode_buffer(len_t + 1)
            user32.GetWindowTextW(h, buf, len_t + 1)
            rect = wintypes.RECT()
            user32.GetWindowRect(h, ctypes.byref(rect))
            found.append({
                "hwnd": h,
                "class": cls.value,
                "title": buf.value,
                "rect": (rect.left, rect.top, rect.right, rect.bottom),
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top
            })
        return True

    PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumDesktopWindows(0, PROC(cb), 0)
    
    if not found:
        return None
    found.sort(key=lambda x: x["width"] * x["height"], reverse=True)
    return found[0]

def capture_viewport(view_type="full", max_size=1280):
    win = find_hammer_window()
    if not win:
        raise RuntimeError("Hammer++ window not found. Is Hammer++ running?")
        
    hwnd = win["hwnd"]
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    
    if width <= 0 or height <= 0:
        raise RuntimeError(f"Invalid Hammer++ window dimensions: {width}x{height}")
        
    hdc_w = user32.GetDC(hwnd)
    hdc_m = gdi32.CreateCompatibleDC(hdc_w)
    hbm = gdi32.CreateCompatibleBitmap(hdc_w, width, height)
    gdi32.SelectObject(hdc_m, hbm)
    
    gdi32.BitBlt(hdc_m, 0, 0, width, height, hdc_w, 0, 0, 0x00CC0020)
    
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD)
        ]

    bih = BITMAPINFOHEADER()
    bih.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bih.biWidth = width
    bih.biHeight = -height
    bih.biPlanes = 1
    bih.biBitCount = 32
    bih.biCompression = 0

    buf = (ctypes.c_char * (width * height * 4))()
    gdi32.GetDIBits(hdc_m, hbm, 0, height, ctypes.byref(buf), ctypes.byref(bih), 0)

    im = Image.frombuffer('RGBA', (width, height), buf, 'raw', 'BGRA', 0, 1)

    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_m)
    user32.ReleaseDC(hwnd, hdc_w)

    right_panel_w = int(width * 0.10)
    top_bar_h = 32
    bottom_bar_h = 24
    
    vp_w = width - right_panel_w
    vp_h = height - top_bar_h - bottom_bar_h
    mid_y = top_bar_h + vp_h // 2
    
    if view_type == "3d":
        im = im.crop((0, top_bar_h, vp_w // 2, mid_y))
    elif view_type == "top":
        im = im.crop((vp_w // 2, top_bar_h, vp_w, mid_y))
    elif view_type == "front":
        im = im.crop((0, mid_y, vp_w // 2, top_bar_h + vp_h))
    elif view_type == "side":
        im = im.crop((vp_w // 2, mid_y, vp_w, top_bar_h + vp_h))

    w, h = im.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        
    return im

def focus_hammer():
    win = find_hammer_window()
    if not win:
        return False
    hwnd = win["hwnd"]
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    return True

def send_hotkey(combo):
    win = find_hammer_window()
    if not win:
        return False
    
    VK_CONTROL = 0x11
    VK_S = 0x53
    VK_R = 0x52
    VK_F5 = 0x74
    VK_F9 = 0x78
    
    focus_hammer()
    time.sleep(0.05)
    
    parts = combo.lower().split('+')
    if 'ctrl' in parts:
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        
    if 's' in parts:
        user32.keybd_event(VK_S, 0, 0, 0)
        user32.keybd_event(VK_S, 0, 2, 0)
    elif 'r' in parts:
        user32.keybd_event(VK_R, 0, 0, 0)
        user32.keybd_event(VK_R, 0, 2, 0)
    elif 'f5' in parts:
        user32.keybd_event(VK_F5, 0, 0, 0)
        user32.keybd_event(VK_F5, 0, 2, 0)
    elif 'f9' in parts:
        user32.keybd_event(VK_F9, 0, 0, 0)
        user32.keybd_event(VK_F9, 0, 2, 0)
        
    if 'ctrl' in parts:
        user32.keybd_event(VK_CONTROL, 0, 2, 0)
        
    return True
