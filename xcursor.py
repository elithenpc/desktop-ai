import ctypes, re, subprocess, time

class XDevice(ctypes.Structure):
    _fields_=[("device_id",ctypes.c_ulong),("num_classes",ctypes.c_int),("classes",ctypes.c_void_p)]

class DesktopCursor:
    def __init__(self):
        self.x11=ctypes.CDLL("libX11.so.6")
        self.xi=ctypes.CDLL("libXi.so.6")
        self.xtst=ctypes.CDLL("libXtst.so.6")
        self.x11.XOpenDisplay.restype=ctypes.c_void_p
        self.display=self.x11.XOpenDisplay(None)
        if not self.display: raise RuntimeError("Cannot open X11 display.")
        self.x11.XDefaultRootWindow.argtypes=[ctypes.c_void_p]; self.x11.XDefaultRootWindow.restype=ctypes.c_ulong
        self.xi.XOpenDevice.argtypes=[ctypes.c_void_p,ctypes.c_ulong]; self.xi.XOpenDevice.restype=ctypes.POINTER(XDevice)
        self.xi.XCloseDevice.argtypes=[ctypes.c_void_p,ctypes.POINTER(XDevice)]
        self.xtst.XTestFakeDeviceMotionEvent.argtypes=[ctypes.c_void_p,ctypes.POINTER(XDevice),ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_ulong]
        self.xtst.XTestFakeDeviceMotionEvent.restype=ctypes.c_int
        self.xtst.XTestFakeDeviceButtonEvent.argtypes=[ctypes.c_void_p,ctypes.POINTER(XDevice),ctypes.c_uint,ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_ulong]
        self.xtst.XTestFakeDeviceButtonEvent.restype=ctypes.c_int
        self.xtst.XTestFakeDeviceKeyEvent.argtypes=[ctypes.c_void_p,ctypes.POINTER(XDevice),ctypes.c_uint,ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_ulong]
        self.xtst.XTestFakeDeviceKeyEvent.restype=ctypes.c_int
        self.x11.XSync.argtypes=[ctypes.c_void_p,ctypes.c_int]
        self.x11.XFlush.argtypes=[ctypes.c_void_p]
        self.x11.XStringToKeysym.argtypes=[ctypes.c_char_p]; self.x11.XStringToKeysym.restype=ctypes.c_ulong
        self.x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong]; self.x11.XKeysymToKeycode.restype=ctypes.c_uint
        self.x11.XFree.argtypes=[ctypes.c_void_p]
        self.name="DesktopAI"
        subprocess.run(["xinput","create-master",self.name],check=True,capture_output=True,text=True)
        time.sleep(.25)
        listing=subprocess.run(["xinput","list","--short"],check=True,capture_output=True,text=True).stdout
        match=re.search(r"↳\s*"+re.escape(self.name)+r" pointer\s+id=(\d+)",listing)
        if not match:
            match=re.search(re.escape(self.name)+r" pointer\s+id=(\d+)",listing)
        if not match: raise RuntimeError("Created XInput master but could not find its pointer ID.")
        self.pointer_id=int(match.group(1))
        kmatch=re.search(re.escape(self.name)+r" keyboard\s+id=(\d+)",listing)
        if not kmatch: raise RuntimeError("Could not find the independent XInput master keyboard.")
        self.keyboard_id=int(kmatch.group(1))
        self.device=self.xi.XOpenDevice(self.display,self.pointer_id)
        self.keyboard=self.xi.XOpenDevice(self.display,self.keyboard_id)
        if not self.device or not self.keyboard: raise RuntimeError("Could not open the independent XInput master devices.")
        self.keysym_device=self.x11.XDefaultRootWindow(self.display)
        self.buttons=set(); self.keys=set()
        self.x11.XSync(self.display,0)

    def move(self,x,y):
        axes=(ctypes.c_int*2)(int(x),int(y))
        if not self.xtst.XTestFakeDeviceMotionEvent(self.display,self.device,0,0,axes,2,0): raise RuntimeError("XTest pointer movement failed.")
        self.x11.XFlush(self.display)

    def _button(self,n,down):
        self.xtst.XTestFakeDeviceButtonEvent(self.display,self.device,n,int(down),None,0,0)
        (self.buttons.add if down else self.buttons.discard)(n)
        self.x11.XFlush(self.display)

    def click(self,x,y,button="left"):
        self.move(x,y); n={"left":1,"middle":2,"right":3}.get(button,1)
        self._button(n,True); self._button(n,False)

    def type_text(self,text):
        # Use clipboard paste so Unicode works; only paste into the currently focused field.
        subprocess.run(["xclip","-selection","clipboard"],input=text,text=True,check=True)
        self.press_key("CTRL+V")

    def press_key(self,key):
        aliases={"ENTER":"Return","ESC":"Escape","TAB":"Tab","SPACE":"space","BACKSPACE":"BackSpace","DELETE":"Delete","UP":"Up","DOWN":"Down","LEFT":"Left","RIGHT":"Right","CTRL":"Control_L","ALT":"Alt_L","SHIFT":"Shift_L","SUPER":"Super_L"}
        parts=key.upper().split("+")
        codes=[]
        for part in parts:
            sym=aliases.get(part,part if len(part)==1 else part.title())
            ks=self.x11.XStringToKeysym(sym.encode())
            if not ks: raise ValueError("Unknown key: "+part)
            code=self.x11.XKeysymToKeycode(self.display,ks)
            if not code: raise ValueError("Unavailable key: "+part)
            codes.append(code)
        for code in codes[:-1]:
            self.xtst.XTestFakeDeviceKeyEvent(self.display,self.keyboard,code,1,None,0,0); self.keys.add(code)
        self.xtst.XTestFakeDeviceKeyEvent(self.display,self.keyboard,codes[-1],1,None,0,0)
        self.xtst.XTestFakeDeviceKeyEvent(self.display,self.device,codes[-1],0,None,0,0)
        for code in reversed(codes[:-1]):
            self.xtst.XTestFakeDeviceKeyEvent(self.display,self.keyboard,code,0,None,0,0); self.keys.discard(code)
        self.x11.XFlush(self.display)

    def scroll(self,x,y,amount):
        self.move(x,y)
        n=4 if amount<0 else 5
        for _ in range(min(abs(int(amount)),12)):
            self._button(n,True); self._button(n,False)

    def release_all(self):
        for n in list(self.buttons): self._button(n,False)
        for code in list(self.keys):
            self.xtst.XTestFakeDeviceKeyEvent(self.display,self.device,code,0,None,0,0)
            self.keys.discard(code)
        self.x11.XFlush(self.display)

    def close(self):
        self.release_all()
        self.xi.XCloseDevice(self.display,self.device)
        self.xi.XCloseDevice(self.display,self.keyboard)
        subprocess.run(["xinput","remove-master",str(self.pointer_id),"Floating"],capture_output=True)
        self.x11.XCloseDisplay(self.display)
