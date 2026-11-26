# -*- coding: utf-8 -*-
r"""
Windows 작업 창 / 듀얼모니터 마우스 이동 잠금 유틸리티 (SH Productivity Tool)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
기능:
  - 현재 작업 중인 창(예: Antigravity, AutoCAD 2023 등) 밖으로 마우스가
    다른 창이나 보조 모니터로 넘어가지 못하도록 Win32 ClipCursor로 안전하게 제한합니다.
  - 전역 단축키 (어떤 프로그램에서나 즉시 동작):
      • Ctrl + Alt + L : 현재 활성 창에 마우스 잠금 ON / OFF 토글
      • Ctrl + Alt + M : 현재 모니터(화면)에만 마우스 잠금 ON / OFF 토글
      • Ctrl + Alt + U : 즉시 마우스 잠금 해제
  - 안전장치:
      • Alt+Tab 등으로 다른 창으로 의도적 전환 시 잠금 일시 정지 (갇힘 방지)
      • 프로그램 종료 / 예외 발생 시 atexit로 ClipCursor(None) 100% 자동 해제
      • 작은 상단 플로팅 바를 잠긴 창 안쪽 우상단에 배치해 마우스로도 즉시 해제 가능
"""

from __future__ import annotations

import atexit
import ctypes
from ctypes import wintypes
import sys
import tkinter as tk

# Win32 API 상수 및 함수 바인딩
user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
kernel32 = ctypes.windll.kernel32

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
MONITOR_DEFAULTTONEAREST = 0x00000002
DWMWA_EXTENDED_FRAME_BOUNDS = 9

HK_LOCK_WINDOW = 101   # Ctrl + Alt + L
HK_LOCK_MONITOR = 102  # Ctrl + Alt + M
HK_UNLOCK = 103        # Ctrl + Alt + U


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def enable_dpi_awareness() -> None:
    try:
        # Per-Monitor V2 DPI Awareness (멀티모니터 배율 오차 0px)
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def unlock_cursor() -> None:
    try:
        user32.ClipCursor(None)
    except Exception:
        pass


def clip_cursor_rect(left: int, top: int, right: int, bottom: int) -> bool:
    if right - left < 60 or bottom - top < 60:
        return False
    r = RECT(int(left), int(top), int(right), int(bottom))
    return bool(user32.ClipCursor(ctypes.byref(r)))


def get_window_title(hwnd: int) -> str:
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value.strip()


def get_window_rect_exact(hwnd: int) -> tuple[int, int, int, int] | None:
    if not hwnd or not user32.IsWindow(hwnd) or user32.IsIconic(hwnd):
        return None
    r = RECT()
    hr = dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd),
        wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(r),
        ctypes.sizeof(r),
    )
    if hr != 0:
        if not user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(r)):
            return None
    if r.right - r.left < 80 or r.bottom - r.top < 80:
        return None
    return (r.left, r.top, r.right, r.bottom)


def get_monitor_rect_for_window(hwnd: int) -> tuple[int, int, int, int] | None:
    if not hwnd:
        return None
    hmon = user32.MonitorFromWindow(wintypes.HWND(hwnd), MONITOR_DEFAULTTONEAREST)
    if not hmon:
        return None
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(wintypes.HANDLE(hmon), ctypes.byref(mi)):
        return None
    r = mi.rcMonitor
    return (r.left, r.top, r.right, r.bottom)


class MouseLockOverlayApp:
    def __init__(self, auto_lock_initial: bool = False) -> None:
        enable_dpi_awareness()
        atexit.register(unlock_cursor)

        # 앱 창을 띄우기 직전의 실제 작업 창 핸들을 먼저 확보!
        self.initial_fg_hwnd = int(user32.GetForegroundWindow() or 0)

        self.root = tk.Tk()
        self.root.title("마우스 창 잠금")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.94)
        self.root.configure(bg="#111827")

        self.mode = "off"          # "off" | "window" | "monitor"
        self.locked_hwnd = 0
        self.locked_title = ""
        self.locked_mon_rect: tuple[int, int, int, int] | None = None
        self.self_hwnd = 0

        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self.root.update_idletasks()
        self.self_hwnd = int(user32.GetParent(self.root.winfo_id()) or self.root.winfo_id())
        self._position_near_window(self.initial_fg_hwnd)
        self._register_hotkeys()

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        if auto_lock_initial and self.initial_fg_hwnd and self.initial_fg_hwnd != self.self_hwnd:
            self.lock_window_hwnd(self.initial_fg_hwnd)

        self._poll_hotkeys()
        self._enforce_clip_loop()

    def _build_ui(self) -> None:
        bar = tk.Frame(self.root, bg="#111827", highlightbackground="#38bdf8", highlightthickness=1, padx=8, pady=5)
        bar.pack(fill="both", expand=True)

        # 드래그 핸들 + 상태 라벨
        top = tk.Frame(bar, bg="#111827")
        top.pack(fill="x")

        self.status_var = tk.StringVar(value="🔓 마우스 자유 이동 (Ctrl+Alt+L: 현재 창 잠금)")
        self.status_lbl = tk.Label(
            top, textvariable=self.status_var,
            font=("맑은 고딕", 8, "bold"), fg="#94a3b8", bg="#111827", anchor="w", cursor="fleur",
        )
        self.status_lbl.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.status_lbl.bind("<Button-1>", self._start_drag)
        self.status_lbl.bind("<B1-Motion>", self._do_drag)

        tk.Button(
            top, text="✕", font=("맑은 고딕", 8, "bold"),
            bg="#374151", fg="#f87171", relief="flat", padx=5, pady=0,
            cursor="hand2", command=self.quit_app,
        ).pack(side="right")

        btn_row = tk.Frame(bar, bg="#111827", pady=4)
        btn_row.pack(fill="x")

        self.btn_win = tk.Button(
            btn_row, text="🔒 현재창 잠금 (Ctrl+Alt+L)", font=("맑은 고딕", 8, "bold"),
            bg="#0284c7", fg="#ffffff", relief="flat", padx=7, pady=3,
            cursor="hand2", command=self.toggle_window_lock_delayed,
        )
        self.btn_win.pack(side="left", padx=(0, 4))

        self.btn_mon = tk.Button(
            btn_row, text="🖥️ 화면만 잠금 (Ctrl+Alt+M)", font=("맑은 고딕", 8, "bold"),
            bg="#475569", fg="#e2e8f0", relief="flat", padx=7, pady=3,
            cursor="hand2", command=self.toggle_monitor_lock,
        )
        self.btn_mon.pack(side="left", padx=(0, 4))

        self.btn_unlock = tk.Button(
            btn_row, text="🔓 해제 (Ctrl+Alt+U)", font=("맑은 고딕", 8, "bold"),
            bg="#22c55e", fg="#052e16", relief="flat", padx=7, pady=3,
            cursor="hand2", command=self.release_lock,
        )
        self.btn_unlock.pack(side="left")

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def _position_near_window(self, hwnd: int) -> None:
        rect = get_window_rect_exact(hwnd)
        w = self.root.winfo_reqwidth() or 380
        if rect:
            left, top, right, _bottom = rect
            px = max(left + 12, right - w - 24)
            py = top + 46
        else:
            px, py = 40, 40
        self.root.geometry(f"+{px}+{py}")

    def _register_hotkeys(self) -> None:
        # 전역 단축키 등록 (thread-level HWND=None → PeekMessage로 안전 폴링)
        user32.RegisterHotKey(None, HK_LOCK_WINDOW, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("L"))
        user32.RegisterHotKey(None, HK_LOCK_MONITOR, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("M"))
        user32.RegisterHotKey(None, HK_UNLOCK, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("U"))

    def _unregister_hotkeys(self) -> None:
        for hk in (HK_LOCK_WINDOW, HK_LOCK_MONITOR, HK_UNLOCK):
            try:
                user32.UnregisterHotKey(None, hk)
            except Exception:
                pass

    def _poll_hotkeys(self) -> None:
        msg = wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, 1):
            hk_id = int(msg.wParam)
            if hk_id == HK_LOCK_WINDOW:
                if self.mode == "window":
                    self.release_lock()
                else:
                    fg = int(user32.GetForegroundWindow() or 0)
                    if fg and fg != self.self_hwnd:
                        self.lock_window_hwnd(fg)
                    elif self.initial_fg_hwnd:
                        self.lock_window_hwnd(self.initial_fg_hwnd)
            elif hk_id == HK_LOCK_MONITOR:
                self.toggle_monitor_lock()
            elif hk_id == HK_UNLOCK:
                self.release_lock()
        self.root.after(60, self._poll_hotkeys)

    def toggle_window_lock_delayed(self) -> None:
        if self.mode == "window":
            self.release_lock()
            return
        # 버튼 클릭 시 2초 뒤 사용자가 클릭한 작업 창을 자동 잠금 (또는 직전 창 즉시 잠금)
        target = self.initial_fg_hwnd
        if target and user32.IsWindow(target) and target != self.self_hwnd:
            self.lock_window_hwnd(target)
        else:
            self.status_var.set("⏳ 2초 안에 잠글 작업 창을 클릭하세요...")
            self.root.after(2000, self._lock_current_fg_after_delay)

    def _lock_current_fg_after_delay(self) -> None:
        fg = int(user32.GetForegroundWindow() or 0)
        if fg and fg != self.self_hwnd:
            self.lock_window_hwnd(fg)
        else:
            self.status_var.set("⚠️ 작업 창을 클릭한 뒤 Ctrl+Alt+L을 눌러주세요")

    def lock_window_hwnd(self, hwnd: int) -> None:
        rect = get_window_rect_exact(hwnd)
        if not rect:
            self.status_var.set("⚠️ 잠글 창 영역을 찾지 못했습니다")
            return
        self.locked_hwnd = hwnd
        self.locked_title = get_window_title(hwnd) or f"Window #{hwnd}"
        self.mode = "window"
        self._position_near_window(hwnd)
        clip_cursor_rect(rect[0] + 2, rect[1] + 2, rect[2] - 2, rect[3] - 2)
        short = self.locked_title[:24] + ("…" if len(self.locked_title) > 24 else "")
        self.status_var.set(f"🔒 창 잠금 중: {short}")
        self.status_lbl.configure(fg="#38bdf8")
        self.btn_win.configure(bg="#ef4444", text="🔓 창 잠금 해제 (Ctrl+Alt+L)")
        self.btn_mon.configure(bg="#475569")

    def toggle_monitor_lock(self) -> None:
        if self.mode == "monitor":
            self.release_lock()
            return
        fg = int(user32.GetForegroundWindow() or 0)
        ref = fg if (fg and fg != self.self_hwnd) else self.initial_fg_hwnd
        mrect = get_monitor_rect_for_window(ref or self.self_hwnd)
        if not mrect:
            return
        self.locked_mon_rect = mrect
        self.mode = "monitor"
        clip_cursor_rect(mrect[0] + 1, mrect[1] + 1, mrect[2] - 1, mrect[3] - 1)
        self.status_var.set(f"🖥️ 현재 화면 잠금 ({mrect[2]-mrect[0]}×{mrect[3]-mrect[1]})")
        self.status_lbl.configure(fg="#facc15")
        self.btn_mon.configure(bg="#eab308", fg="#1c1917")
        self.btn_win.configure(bg="#0284c7", text="🔒 현재창 잠금 (Ctrl+Alt+L)")

    def release_lock(self) -> None:
        self.mode = "off"
        self.locked_hwnd = 0
        self.locked_mon_rect = None
        unlock_cursor()
        self.status_var.set("🔓 잠금 해제됨 (Ctrl+Alt+L: 현재 창 잠금)")
        self.status_lbl.configure(fg="#86efac")
        self.btn_win.configure(bg="#0284c7", text="🔒 현재창 잠금 (Ctrl+Alt+L)")
        self.btn_mon.configure(bg="#475569", fg="#e2e8f0")

    def _enforce_clip_loop(self) -> None:
        try:
            fg = int(user32.GetForegroundWindow() or 0)
            if fg and fg != self.self_hwnd:
                self.initial_fg_hwnd = fg

            if self.mode == "window":
                if not user32.IsWindow(self.locked_hwnd):
                    self.release_lock()
                elif fg in (self.locked_hwnd, self.self_hwnd):
                    rect = get_window_rect_exact(self.locked_hwnd)
                    if rect:
                        clip_cursor_rect(rect[0] + 2, rect[1] + 2, rect[2] - 2, rect[3] - 2)
                else:
                    # 사용자가 Alt+Tab 등으로 다른 창으로 의도적 전환 시 일시 해제 (갇힘 방지)
                    unlock_cursor()
            elif self.mode == "monitor" and self.locked_mon_rect:
                r = self.locked_mon_rect
                clip_cursor_rect(r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1)
        except Exception:
            pass
        self.root.after(80, self._enforce_clip_loop)

    def quit_app(self) -> None:
        unlock_cursor()
        self._unregister_hotkeys()
        self.root.destroy()

    def run(self) -> None:
        try:
            self.root.mainloop()
        finally:
            unlock_cursor()
            self._unregister_hotkeys()


if __name__ == "__main__":
    auto_lock = "--lock" in sys.argv
    app = MouseLockOverlayApp(auto_lock_initial=auto_lock)
    app.run()
