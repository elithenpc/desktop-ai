import ctypes, re, subprocess, time

class XDevice(ctypes.Structure):
    _fields_ = [("device_id", ctypes.c_ulong), ("num_classes", ctypes.c_int), ("classes", ctypes.c_void_p)]


class DesktopCursor:
    def __init__(self):
        self.x11 = ctypes.CDLL("libX11.so.6")
        self.xi = ctypes.CDLL("libXi.so.6")
        self.xtst = ctypes.CDLL("libXtst.so.6")
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.display = self.x11.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("Cannot open X11 display.")

        self.xi.XOpenDevice.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.xi.XOpenDevice.restype = ctypes.POINTER(XDevice)
        self.xi.XCloseDevice.argtypes = [ctypes.c_void_p, ctypes.POINTER(XDevice)]
        self.xtst.XTestFakeDeviceMotionEvent.argtypes = [ctypes.c_void_p, ctypes.POINTER(XDevice), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_ulong]
        self.xtst.XTestFakeDeviceMotionEvent.restype = ctypes.c_int
        self.xtst.XTestFakeDeviceButtonEvent.argtypes = [ctypes.c_void_p, ctypes.POINTER(XDevice), ctypes.c_uint, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_ulong]
        self.xtst.XTestFakeDeviceButtonEvent.restype = ctypes.c_int
        self.xtst.XTestFakeDeviceKeyEvent.argtypes = [ctypes.c_void_p, ctypes.POINTER(XDevice), ctypes.c_uint, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_ulong]
        self.xtst.XTestFakeDeviceKeyEvent.restype = ctypes.c_int
        self.x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.x11.XFlush.argtypes = [ctypes.c_void_p]
        self.x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x11.XStringToKeysym.restype = ctypes.c_ulong
        self.x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x11.XKeysymToKeycode.restype = ctypes.c_uint
        self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]

        self.name = "DesktopAI"
        subprocess.run(["xinput", "create-master", self.name], check=True, capture_output=True, text=True)
        time.sleep(0.3)
        listing = subprocess.run(["xinput", "list", "--short"], check=True, capture_output=True, text=True).stdout

        # XOpenDevice rejects master devices (XI_BadDevice). Open their XTEST
        # slave devices instead; injecting into those slaves drives the paired
        # independent master pointer and keyboard.
        pointer_match = re.search(re.escape(self.name) + r" XTEST pointer\s+id=(\d+)", listing, re.I)
        keyboard_match = re.search(re.escape(self.name) + r" XTEST keyboard\s+id=(\d+)", listing, re.I)
        master_match = re.search(re.escape(self.name) + r" pointer\s+id=(\d+)", listing, re.I)
        if not pointer_match or not keyboard_match or not master_match:
            subprocess.run(["xinput", "remove-master", self.name + " pointer", "Floating"], capture_output=True)
            raise RuntimeError("Created the Desktop AI master devices, but could not find their XTEST slave devices. Run 'xinput list --short' to inspect the device list.")

        self.master_pointer_id = int(master_match.group(1))
        self.pointer_id = int(pointer_match.group(1))
        self.keyboard_id = int(keyboard_match.group(1))
        self.device = self.xi.XOpenDevice(self.display, self.pointer_id)
        self.keyboard = self.xi.XOpenDevice(self.display, self.keyboard_id)
        if not self.device or not self.keyboard:
            if self.device:
                self.xi.XCloseDevice(self.display, self.device)
            if self.keyboard:
                self.xi.XCloseDevice(self.display, self.keyboard)
            subprocess.run(["xinput", "remove-master", str(self.master_pointer_id), "Floating"], capture_output=True)
            raise RuntimeError("Could not open the Desktop AI XTEST slave devices.")
        self.cancel_motion = False
        self.buttons = set()
        self.keys = set()
        self.x11.XSync(self.display, 0)
        self.x11.XDefaultRootWindow.argtypes=[ctypes.c_void_p]
        self.x11.XDefaultRootWindow.restype=ctypes.c_ulong
        self.x11.XQueryPointer.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_ulong),ctypes.POINTER(ctypes.c_ulong),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_uint)]
        self.x11.XQueryPointer.restype=ctypes.c_int
        root=self.x11.XDefaultRootWindow(self.display)
        rr=ctypes.c_ulong(); child=ctypes.c_ulong()
        rx=ctypes.c_int(); ry=ctypes.c_int(); wx=ctypes.c_int(); wy=ctypes.c_int(); mask=ctypes.c_uint()
        if self.x11.XQueryPointer(self.display,root,ctypes.byref(rr),ctypes.byref(child),ctypes.byref(rx),ctypes.byref(ry),ctypes.byref(wx),ctypes.byref(wy),ctypes.byref(mask)):
            self.position=(wx.value,wy.value)
        else:
            self.position=(0,0)
        self.move(*self.position)

    def move(self, x, y):
        self.cancel_motion = False
        axes = (ctypes.c_int * 2)(int(x), int(y))
        if not self.xtst.XTestFakeDeviceMotionEvent(self.display, self.device, 0, 0, axes, 2, 0):
            raise RuntimeError("XTest pointer movement failed.")
        self.position=(int(x),int(y))
        self.x11.XFlush(self.display)

    def move_smooth(self, x, y):
        import math
        x=int(x); y=int(y)
        sx,sy=self.position
        distance=math.hypot(x-sx,y-sy)
        steps=max(3,min(36,int(distance/35)))
        duration=min(0.42,max(0.07,distance/2800.0))
        for i in range(1,steps+1):
            t=i/steps
            eased=1-(1-t)**3
            self.move(round(sx+(x-sx)*eased),round(sy+(y-sy)*eased))
            if i<steps: time.sleep(duration/steps)

    def _button(self, number, down):
        self.xtst.XTestFakeDeviceButtonEvent(self.display, self.device, number, int(down), None, 0, 0)
        (self.buttons.add if down else self.buttons.discard)(number)
        self.x11.XFlush(self.display)

    def click(self, x, y, button="left"):
        self.move(x, y)
        number = {"left": 1, "middle": 2, "right": 3}.get(button, 1)
        self._button(number, True)
        self._button(number, False)

    def type_text(self, text):
        # Clipboard paste supports Unicode. This replaces the current clipboard contents.
        subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
        self.press_key("CTRL+V")

    def press_key(self, key):
        aliases = {"ENTER": "Return", "ESC": "Escape", "TAB": "Tab", "SPACE": "space",
                   "BACKSPACE": "BackSpace", "DELETE": "Delete", "UP": "Up", "DOWN": "Down",
                   "LEFT": "Left", "RIGHT": "Right", "CTRL": "Control_L", "ALT": "Alt_L",
                   "SHIFT": "Shift_L", "SUPER": "Super_L"}
        parts = key.upper().split("+")
        codes = []
        for part in parts:
            symbol = aliases.get(part, part if len(part) == 1 else part.title())
            keysym = self.x11.XStringToKeysym(symbol.encode())
            if not keysym:
                raise ValueError("Unknown key: " + part)
            code = self.x11.XKeysymToKeycode(self.display, keysym)
            if not code:
                raise ValueError("Unavailable key: " + part)
            codes.append(code)
        for code in codes[:-1]:
            self.xtst.XTestFakeDeviceKeyEvent(self.display, self.keyboard, code, 1, None, 0, 0)
            self.keys.add(code)
        self.xtst.XTestFakeDeviceKeyEvent(self.display, self.keyboard, codes[-1], 1, None, 0, 0)
        self.xtst.XTestFakeDeviceKeyEvent(self.display, self.keyboard, codes[-1], 0, None, 0, 0)
        for code in reversed(codes[:-1]):
            self.xtst.XTestFakeDeviceKeyEvent(self.display, self.keyboard, code, 0, None, 0, 0)
            self.keys.discard(code)
        self.x11.XFlush(self.display)

    def scroll(self, x, y, amount):
        self.move(x, y)
        number = 4 if amount < 0 else 5
        for _ in range(min(abs(int(amount)), 12)):
            self._button(number, True)
            self._button(number, False)

    def release_all(self):
        for number in list(self.buttons):
            self._button(number, False)
        for code in list(self.keys):
            self.xtst.XTestFakeDeviceKeyEvent(self.display, self.keyboard, code, 0, None, 0, 0)
            self.keys.discard(code)
        self.x11.XFlush(self.display)

    def close(self):
        if not getattr(self, "display", None):
            return
        self.release_all()
        if getattr(self, "device", None):
            self.xi.XCloseDevice(self.display, self.device)
            self.device = None
        if getattr(self, "keyboard", None):
            self.xi.XCloseDevice(self.display, self.keyboard)
            self.keyboard = None
        subprocess.run(["xinput", "remove-master", str(self.master_pointer_id), "Floating"], capture_output=True)
        self.x11.XCloseDisplay(self.display)
        self.display = None
