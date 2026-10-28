"""cursor_loop.py — 闭环加光标:点击选中→Display→Max→像素验证(青色十字线)"""
import time, win32gui, win32con
import print_export as pe
from PIL import ImageGrab

H = None

def cyan_count(bbox):
    img = ImageGrab.grab(bbox=bbox).convert("RGB")
    n = 0
    px = img.load()
    for y in range(0, img.size[1], 2):
        for x in range(0, img.size[0], 2):
            r, g, b = px[x, y]
            if g > 180 and b > 180 and r < 140:
                n += 1
    return n

def cursor_max_robust(click_xy, check_bbox, name, tries=3):
    for i in range(tries):
        pe.click(*click_xy)
        time.sleep(0.6)
        win32gui.PostMessage(H, win32con.WM_COMMAND, 0x801c, 0)  # Display
        time.sleep(0.8)
        win32gui.PostMessage(H, win32con.WM_COMMAND, 0x801d, 0)  # Max
        time.sleep(0.9)
        n = cyan_count(check_bbox)
        print(f"  {name} try{i}: cyan={n}")
        if n >= 8:
            return True
    return False

def main():
    global H
    H = pe.probe_frame()
    pe.set_fore(H)
    # Vo: 图例(255,651); 峰值区 (400-620, 140-280)
    ok1 = cursor_max_robust((255, 651), (400, 140, 620, 280), "Vo")
    # Vi: 曲线峰值(319,844); 验证区 (240-420, 780-900)
    ok2 = cursor_max_robust((319, 844), (240, 780, 420, 900), "Vi")
    # Vs: 曲线峰值(305,771); 验证区 (230-420, 700-800)
    ok3 = cursor_max_robust((305, 771), (230, 700, 420, 800), "Vs")
    print("RESULT:", ok1, ok2, ok3)
    img = ImageGrab.grab(bbox=(0, 100, 1500, 980))
    img.save(r"D:\Main_FIles\free-deng\orcad-mcp\cs_final.png")

if __name__ == "__main__":
    main()
