import win32gui
res=[]
def cb(h,_):
    if win32gui.IsWindowVisible(h):
        t=win32gui.GetWindowText(h); c=win32gui.GetClassName(h)
        if c=="#32770" or c=="OrCaptureFrame": res.append((h,c,t))
win32gui.EnumWindows(cb,None)
print(res)
