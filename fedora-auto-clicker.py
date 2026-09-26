#!/usr/bin/python3
"""
Fedora Auto Clicker – All-in-One Clicker & Macro Automation
Licensed under GPLv3
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
import random
import json
import sys
import os
true_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(true_dir, 'libs'))
import datetime
import re
import subprocess
import libevdev
from libevdev import EV_KEY, EV_SYN
import keyboard  # global hotkeys + key combo simulation
import pyautogui  # for recording mouse/position (bundled alternative)
pyautogui.PAUSE = 0.01
import logging

# ------------------------------------------------------------
# App Configuration
# ------------------------------------------------------------
APP_NAME = "Fedora Auto Clicker"
VERSION = "1.0.0"
LANG_FILE = os.path.join(true_dir, "lang.json")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Simple translation system
STRINGS = {
    "en": {
        "title": "Fedora Auto Clicker",
        "always_on_top": "Always on top",
        "status_ready": "Status: READY",
        "start": "START",
        "stop": "STOP",
        "clicker_tab": "Clicker",
        "keycombo_tab": "Key Combo",
        "macro_tab": "Macro",
        "profiles_tab": "Profiles",
        "settings_tab": "Settings",
        "delay": "Click Interval (sec):",
        "random_interval": "Random interval",
        "min": "Min",
        "max": "Max",
        "mouse_button": "Mouse Button:",
        "repeat": "Repeat (0=∞):",
        "position": "Position:",
        "current_pos": "Current cursor",
        "fixed_pos": "Fixed X,Y",
        "pos_x": "X:",
        "pos_y": "Y:",
        "radius_random": "Randomize radius (px):",
        "key_combo": "Key Combo:",
        "listen": "Listen (F2)",
        "macro_record": "Record",
        "macro_play": "Play",
        "macro_stop": "Stop",
        "macro_clear": "Clear",
        "profile_save": "Save",
        "profile_load": "Load",
        "profile_delete": "Delete",
        "language": "Language",
        "hotkey_start": "Start Hotkey:",
        "hotkey_stop": "Stop Hotkey:",
        "idle_detect": "Idle detection (pause on mouse move)",
        "scheduled_start": "Scheduled start (HH:MM)",
        "stats": "Actions:",
        "error_root": "Please run with sudo for virtual input devices.",
        "status_paused": "Status: PAUSED (idle)",
    },
    "de": {
        "title": "Fedora Auto Clicker",
        "always_on_top": "Immer im Vordergrund",
        "status_ready": "Status: BEREIT",
        "start": "START",
        "stop": "STOPP",
        "clicker_tab": "Klicker",
        "keycombo_tab": "Tastenkombi",
        "macro_tab": "Makro",
        "profiles_tab": "Profile",
        "settings_tab": "Einstellungen",
        "delay": "Intervall (Sek):",
        "random_interval": "Zufallsintervall",
        "min": "Min",
        "max": "Max",
        "mouse_button": "Maustaste:",
        "repeat": "Wiederholungen (0=∞):",
        "position": "Position:",
        "current_pos": "Aktueller Cursor",
        "fixed_pos": "Feste Koordinaten",
        "pos_x": "X:",
        "pos_y": "Y:",
        "radius_random": "Streuradius (px):",
        "key_combo": "Tastenkombi:",
        "listen": "Aufnehmen (F2)",
        "macro_record": "Aufnehmen",
        "macro_play": "Abspielen",
        "macro_stop": "Stopp",
        "macro_clear": "Löschen",
        "profile_save": "Speichern",
        "profile_load": "Laden",
        "profile_delete": "Löschen",
        "language": "Sprache",
        "hotkey_start": "Start Hotkey:",
        "hotkey_stop": "Stopp Hotkey:",
        "idle_detect": "Idle‑Erkennung (Pause bei Mausbewegung)",
        "scheduled_start": "Geplanter Start (HH:MM)",
        "stats": "Aktionen:",
        "error_root": "Bitte mit sudo starten.",
        "status_paused": "Status: PAUSE (Idle)",
    }
}

def load_language():
    if os.path.exists(LANG_FILE):
        with open(LANG_FILE, 'r') as f:
            return json.load(f).get("lang", "en")
    return "en"

def save_language(lang):
    with open(LANG_FILE, 'w') as f:
        json.dump({"lang": lang}, f)

current_lang = load_language()
tr = lambda key: STRINGS[current_lang].get(key, key)

# ------------------------------------------------------------
# Virtual input device
# ------------------------------------------------------------
def init_virtual_mouse():
    dev = libevdev.Device()
    dev.name = "Fedora Auto Clicker Virtual Device"
    dev.enable(EV_KEY.BTN_LEFT)
    dev.enable(EV_KEY.BTN_RIGHT)
    dev.enable(EV_KEY.BTN_MIDDLE)
    # enable common keys for combos
    for code in range(1, 128):
        try:
            dev.enable(code)
        except:
            pass
    return dev.create_uinput_device()

# ------------------------------------------------------------
# Main Application Class
# ------------------------------------------------------------
class FedoraAutoClicker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("680x620")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.is_running = False
        self.paused = False
        self.uinput = None
        self.stats_counter = 0
        self.macro_events = []  # list of (type, data, delay)
        self.record_start_time = None
        self.idle_position = None
        self.idle_timer = None
        self.scheduled_job = None
        self.current_profile = None

        self.start_hotkey = 'f8'
        self.stop_hotkey = 'f9'
        self.listen_hotkey = 'f2'

        self.lang_var = ctk.StringVar(value=current_lang)

        # Language
        self.load_language()

        # Init virtual mouse
        try:
            self.uinput = init_virtual_mouse()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create virtual device: {e}")
            sys.exit(1)

        # Build UI
        self.build_ui()
        self.register_global_hotkeys()

        # Start idle detection thread
        self.idle_thread = threading.Thread(target=self.idle_watcher, daemon=True)
        self.idle_thread.start()

        self.update_status("ready")

    def load_language(self):
        global current_lang
        current_lang = self.lang_var.get()
        # Rebuild UI if needed (simple approach: destroy and rebuild)
        # For simplicity, we will just update all text elements
        if hasattr(self, 'title_label'):
            self.refresh_texts()

    def refresh_texts(self):
        self.title_label.configure(text=tr("title"))
        self.always_on_top_check.configure(text=tr("always_on_top"))
        self.update_status("ready")
        # update tabs titles
        self.tabview.configure(**{f"{tr('clicker_tab')}": ...})  # not possible directly; we'll use tab names
        # Instead, we reconstruct tabs, but to keep it simple, we just set tab names
        self.tabview.rename("Clicker", tr("clicker_tab"))
        self.tabview.rename("KeyCombo", tr("keycombo_tab"))
        self.tabview.rename("Macro", tr("macro_tab"))
        self.tabview.rename("Profiles", tr("profiles_tab"))
        self.tabview.rename("Settings", tr("settings_tab"))

    def build_ui(self):
        # Top bar
        self.title_label = ctk.CTkLabel(self, text=tr("title"), font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=10)

        self.always_on_top_var = ctk.BooleanVar(value=True)
        self.always_on_top_check = ctk.CTkCheckBox(self, text=tr("always_on_top"), variable=self.always_on_top_var, command=self.toggle_always_on_top)
        self.always_on_top_check.pack()

        # Tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.clicker_tab = self.tabview.add(tr("clicker_tab"))
        self.keycombo_tab = self.tabview.add(tr("keycombo_tab"))
        self.macro_tab = self.tabview.add(tr("macro_tab"))
        self.profiles_tab = self.tabview.add(tr("profiles_tab"))
        self.settings_tab = self.tabview.add(tr("settings_tab"))

        self.build_clicker_tab()
        self.build_keycombo_tab()
        self.build_macro_tab()
        self.build_profiles_tab()
        self.build_settings_tab()

        # Status & stats
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=10, pady=(0,5))
        self.status_label = ctk.CTkLabel(status_frame, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(side="left", padx=10)
        self.stats_label = ctk.CTkLabel(status_frame, text="", font=ctk.CTkFont(size=12))
        self.stats_label.pack(side="right", padx=10)
        self.update_status("ready")

        # Start/Stop buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        self.start_btn = ctk.CTkButton(btn_frame, text=tr("start"), fg_color="#2ecc71", hover_color="#27ae60", command=self.start_action)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=5)
        self.stop_btn = ctk.CTkButton(btn_frame, text=tr("stop"), fg_color="#e74c3c", hover_color="#c0392b", command=self.stop_action, state="disabled")
        self.stop_btn.pack(side="right", expand=True, fill="x", padx=5)

    def build_clicker_tab(self):
        tab = self.clicker_tab
        # Interval
        ctk.CTkLabel(tab, text=tr("delay")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.delay_entry = ctk.CTkEntry(tab, width=80)
        self.delay_entry.insert(0, "1.0")
        self.delay_entry.grid(row=0, column=1, padx=5, pady=5)

        self.random_var = ctk.BooleanVar()
        self.random_check = ctk.CTkCheckBox(tab, text=tr("random_interval"), variable=self.random_var, command=self.toggle_random_fields)
        self.random_check.grid(row=1, column=0, columnspan=2, pady=5)

        ctk.CTkLabel(tab, text=tr("min")).grid(row=2, column=0, padx=5, pady=2, sticky="e")
        self.min_entry = ctk.CTkEntry(tab, width=60)
        self.min_entry.insert(0, "1.0")
        self.min_entry.grid(row=2, column=1, padx=5, pady=2)
        ctk.CTkLabel(tab, text=tr("max")).grid(row=3, column=0, padx=5, pady=2, sticky="e")
        self.max_entry = ctk.CTkEntry(tab, width=60)
        self.max_entry.insert(0, "2.0")
        self.max_entry.grid(row=3, column=1, padx=5, pady=2)
        self.toggle_random_fields()

        # Mouse button
        ctk.CTkLabel(tab, text=tr("mouse_button")).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.button_combo = ctk.CTkComboBox(tab, values=["Left", "Right", "Middle"], width=80)
        self.button_combo.set("Left")
        self.button_combo.grid(row=4, column=1, padx=5, pady=5)

        # Repeat
        ctk.CTkLabel(tab, text=tr("repeat")).grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.repeat_entry = ctk.CTkEntry(tab, width=80)
        self.repeat_entry.insert(0, "0")
        self.repeat_entry.grid(row=5, column=1, padx=5, pady=5)

        # Position
        ctk.CTkLabel(tab, text=tr("position")).grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.pos_mode = ctk.CTkComboBox(tab, values=[tr("current_pos"), tr("fixed_pos")], command=self.toggle_pos_fields)
        self.pos_mode.set(tr("current_pos"))
        self.pos_mode.grid(row=6, column=1, padx=5, pady=5)

        ctk.CTkLabel(tab, text=tr("pos_x")).grid(row=7, column=0, padx=5, pady=2, sticky="e")
        self.pos_x = ctk.CTkEntry(tab, width=60)
        self.pos_x.insert(0, "500")
        self.pos_x.grid(row=7, column=1, padx=5, pady=2)
        ctk.CTkLabel(tab, text=tr("pos_y")).grid(row=8, column=0, padx=5, pady=2, sticky="e")
        self.pos_y = ctk.CTkEntry(tab, width=60)
        self.pos_y.insert(0, "300")
        self.pos_y.grid(row=8, column=1, padx=5, pady=2)

        self.radius_var = ctk.BooleanVar()
        self.radius_check = ctk.CTkCheckBox(tab, text=tr("radius_random"), variable=self.radius_var)
        self.radius_check.grid(row=9, column=0, columnspan=2, pady=5)
        self.radius_entry = ctk.CTkEntry(tab, width=60)
        self.radius_entry.insert(0, "5")
        self.radius_entry.grid(row=9, column=1, padx=5, pady=5)

        self.toggle_pos_fields(self.pos_mode.get())

    def toggle_random_fields(self):
        if self.random_var.get():
            self.min_entry.configure(state="normal")
            self.max_entry.configure(state="normal")
        else:
            self.min_entry.configure(state="disabled")
            self.max_entry.configure(state="disabled")

    def toggle_pos_fields(self, choice):
        if choice == tr("fixed_pos"):
            self.pos_x.configure(state="normal")
            self.pos_y.configure(state="normal")
        else:
            self.pos_x.configure(state="disabled")
            self.pos_y.configure(state="disabled")

    def build_keycombo_tab(self):
        tab = self.keycombo_tab
        ctk.CTkLabel(tab, text=tr("key_combo")).pack(pady=10)
        self.combo_entry = ctk.CTkEntry(tab, width=200)
        self.combo_entry.insert(0, "shift+a")
        self.combo_entry.pack(pady=5)
        listen_btn = ctk.CTkButton(tab, text=tr("listen"), command=self.listen_combo)
        listen_btn.pack(pady=5)

        # Repeat
        ctk.CTkLabel(tab, text=tr("repeat")).pack()
        self.combo_repeat = ctk.CTkEntry(tab, width=80)
        self.combo_repeat.insert(0, "0")
        self.combo_repeat.pack(pady=5)

        # Interval with randomness
        self.combo_random_var = ctk.BooleanVar()
        ctk.CTkCheckBox(tab, text=tr("random_interval"), variable=self.combo_random_var).pack()
        frame = ctk.CTkFrame(tab)
        frame.pack()
        ctk.CTkLabel(frame, text=tr("min")).grid(row=0,column=0)
        self.combo_min_entry = ctk.CTkEntry(frame, width=60)
        self.combo_min_entry.insert(0, "1.0")
        self.combo_min_entry.grid(row=0,column=1)
        ctk.CTkLabel(frame, text=tr("max")).grid(row=1,column=0)
        self.combo_max_entry = ctk.CTkEntry(frame, width=60)
        self.combo_max_entry.insert(0, "2.0")
        self.combo_max_entry.grid(row=1,column=1)

    def build_macro_tab(self):
        tab = self.macro_tab
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=10)
        self.record_btn = ctk.CTkButton(btn_frame, text=tr("macro_record"), command=self.start_recording)
        self.record_btn.pack(side="left", padx=5)
        self.stop_rec_btn = ctk.CTkButton(btn_frame, text=tr("macro_stop"), command=self.stop_recording, state="disabled")
        self.stop_rec_btn.pack(side="left", padx=5)
        self.play_macro_btn = ctk.CTkButton(btn_frame, text=tr("macro_play"), command=self.play_macro, state="disabled")
        self.play_macro_btn.pack(side="left", padx=5)
        self.clear_macro_btn = ctk.CTkButton(btn_frame, text=tr("macro_clear"), command=self.clear_macro)
        self.clear_macro_btn.pack(side="left", padx=5)

        self.macro_status = ctk.CTkLabel(tab, text="No events recorded.")
        self.macro_status.pack()

    def build_profiles_tab(self):
        tab = self.profiles_tab
        self.profile_list = ctk.CTkComboBox(tab, values=self.get_profile_list(), width=200)
        self.profile_list.pack(pady=10)
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text=tr("profile_load"), command=self.load_profile).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=tr("profile_save"), command=self.save_profile).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=tr("profile_delete"), command=self.delete_profile).pack(side="left", padx=5)

    def build_settings_tab(self):
        tab = self.settings_tab
        ctk.CTkLabel(tab, text=tr("language")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        lang_combo = ctk.CTkComboBox(tab, values=["en", "de"], variable=self.lang_var, command=self.change_language)
        lang_combo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(tab, text=tr("hotkey_start")).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.hotkey_start_entry = ctk.CTkEntry(tab, width=80)
        self.hotkey_start_entry.insert(0, self.start_hotkey)
        self.hotkey_start_entry.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(tab, text=tr("hotkey_stop")).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.hotkey_stop_entry = ctk.CTkEntry(tab, width=80)
        self.hotkey_stop_entry.insert(0, self.stop_hotkey)
        self.hotkey_stop_entry.grid(row=2, column=1, padx=5, pady=5)

        self.idle_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(tab, text=tr("idle_detect"), variable=self.idle_var).grid(row=3, column=0, columnspan=2, pady=5)

        ctk.CTkLabel(tab, text=tr("scheduled_start")).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.schedule_entry = ctk.CTkEntry(tab, width=80)
        self.schedule_entry.insert(0, "")
        self.schedule_entry.grid(row=4, column=1, padx=5, pady=5)
        ctk.CTkButton(tab, text="Set", command=self.set_schedule).grid(row=4, column=2, padx=5)

    def change_language(self, lang):
        save_language(lang)
        self.lang_var.set(lang)
        self.load_language()
        self.refresh_texts()
        self.rebuild_tabs()  # easier: destroy and rebuild tab contents

    def rebuild_tabs(self):
        for tab in [self.clicker_tab, self.keycombo_tab, self.macro_tab, self.profiles_tab, self.settings_tab]:
            for widget in tab.winfo_children():
                widget.destroy()
        self.build_clicker_tab()
        self.build_keycombo_tab()
        self.build_macro_tab()
        self.build_profiles_tab()
        self.build_settings_tab()

    # ------------------------------------------------------------
    # Global Hotkeys
    # ------------------------------------------------------------
    def register_global_hotkeys(self):
        # clear previous hotkeys
        try:
            keyboard.unhook_all_hotkeys()
        except AttributeError:
            try:
                keyboard.remove_hotkey(self.start_hotkey)
            except:
                pass
            try:
                keyboard.remove_hotkey(self.stop_hotkey)
            except:
                pass
            try:
                keyboard.remove_hotkey(self.listen_hotkey)
            except:
                pass

        keyboard.add_hotkey(self.start_hotkey, self.hotkey_start)
        keyboard.add_hotkey(self.stop_hotkey, self.hotkey_stop)
        keyboard.add_hotkey(self.listen_hotkey, self.hotkey_listen)

    def hotkey_start(self):
        self.after(0, self.start_action)

    def hotkey_stop(self):
        self.after(0, self.stop_action)

    def hotkey_listen(self):
        self.after(0, self.listen_combo)
    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------
    def start_action(self):
        if self.is_running:
            return
        self.is_running = True
        self.paused = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.update_status("running")
        current_tab = self.tabview.get()   # ein String (übersetzt)
        if current_tab == tr("clicker_tab"):
            threading.Thread(target=self.clicker_loop, daemon=True).start()
        elif current_tab == tr("keycombo_tab"):
            threading.Thread(target=self.keycombo_loop, daemon=True).start()
        elif current_tab == tr("macro_tab"):
            # Wenn ein Makro existiert, spiele es ab, sonst Hinweis
            if self.macro_events:
                self.play_macro()   # startet selbst einen Thread
            else:
                self.stop_action()
                messagebox.showinfo("Info", "No macro recorded.")
        else:
            self.stop_action()
            messagebox.showinfo("Info", "Switch to Clicker, Key Combo or Macro tab.")

    def stop_action(self):
        self.is_running = False
        self.paused = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.update_status("ready")
        # Cancel any schedule
        if self.scheduled_job:
            self.after_cancel(self.scheduled_job)
            self.scheduled_job = None

    # ------------------------------------------------------------
    # Clicker Loop
    # ------------------------------------------------------------
    def clicker_loop(self):
        delay = 1.0
        try:
            if self.random_var.get():
                dmin = float(self.min_entry.get())
                dmax = float(self.max_entry.get())
                delay = random.uniform(dmin, dmax)
            else:
                delay = float(self.delay_entry.get())
        except:
            pass

        button = self.button_combo.get().lower()
        repeat = int(self.repeat_entry.get())
        count = 0
        fixed_pos = None
        if self.pos_mode.get() == tr("fixed_pos"):
            try:
                fixed_pos = (int(self.pos_x.get()), int(self.pos_y.get()))
            except:
                fixed_pos = None

        radius = 0
        if self.radius_var.get():
            try:
                radius = int(self.radius_entry.get())
            except:
                radius = 0

        while self.is_running and not self.paused:
            if fixed_pos:
                x, y = fixed_pos
                if radius > 0:
                    x += random.randint(-radius, radius)
                    y += random.randint(-radius, radius)
                # Save original window state to avoid desktop manager interference 
                was_topmost = self.attributes("-topmost")
                # Temporarily disable always-on-top to allow proper mouse positioning
                self.attributes("-topmost", False)
                pyautogui.moveTo(x, y)
                # Restore always-on-top state
                self.attributes("-topmost", was_topmost)
            pyautogui.click(button=button)
            self.stats_counter += 1
            self.after(0, self.update_stats)
            count += 1
            if repeat > 0 and count >= repeat:
                break

            time.sleep(delay)
            if self.random_var.get():
                delay = random.uniform(float(self.min_entry.get()), float(self.max_entry.get()))
            else:
                delay = float(self.delay_entry.get()) if not self.random_var.get() else delay

        self.after(0, self.stop_action)

    # ------------------------------------------------------------
    # Key Combo Loop
    # ------------------------------------------------------------
    def keycombo_loop(self):
        combo_str = self.combo_entry.get().strip()
        repeat = int(self.combo_repeat.get())
        count = 0
        while self.is_running and not self.paused:
            keyboard.press_and_release(combo_str)
            self.stats_counter += 1
            self.after(0, self.update_stats)
            count += 1
            if repeat > 0 and count >= repeat:
                break
            # interval
            if self.combo_random_var.get():
                d = random.uniform(float(self.combo_min_entry.get()), float(self.combo_max_entry.get()))
            else:
                d = float(self.delay_entry.get())
            time.sleep(d)
        self.after(0, self.stop_action)

    # ------------------------------------------------------------
    # Macro Recording
    # ------------------------------------------------------------
    def start_recording(self):
        self.macro_events = []
        self.record_start_time = time.time()
        self.record_btn.configure(state="disabled")
        self.stop_rec_btn.configure(state="normal")
        self.play_macro_btn.configure(state="disabled")
        self.macro_status.configure(text="Recording... (press Stop or F9)")
        # Hook mouse & keyboard events
        keyboard.hook(self._record_keyboard)
        pyautogui.hook(self._record_mouse)

    def _record_keyboard(self, event):
        if event.event_type == 'down':
            self.macro_events.append(('key', event.name, time.time() - self.record_start_time))

    def _record_mouse(self, event):
        # pyautogui mouse hook events: MoveEvent, ButtonEvent, ScrollEvent
        t = time.time() - self.record_start_time
        if isinstance(event, pyautogui.MoveEvent):
            self.macro_events.append(('move', (event.x, event.y), t))
        elif isinstance(event, pyautogui.ButtonEvent) and event.event_type == 'down':
            self.macro_events.append(('click', event.button, t))

    def stop_recording(self):
        keyboard.unhook_all()
        pyautogui.unhook_all()
        self.record_btn.configure(state="normal")
        self.stop_rec_btn.configure(state="disabled")
        if self.macro_events:
            self.play_macro_btn.configure(state="normal")
            self.macro_status.configure(text=f"Recorded {len(self.macro_events)} events.")
        else:
            self.macro_status.configure(text="No events recorded.")

    def play_macro(self):
        if not self.macro_events:
            return
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self._macro_playback, daemon=True).start()

    def _macro_playback(self):
        last_time = 0
        for evt in self.macro_events:
            if not self.is_running:
                break
            delay = evt[2] - last_time
            if delay > 0:
                time.sleep(delay)
            last_time = evt[2]
            if evt[0] == 'move':
                pyautogui.moveTo(*evt[1])
            elif evt[0] == 'click':
                pyautogui.click(button=evt[1])
            elif evt[0] == 'key':
                keyboard.press_and_release(evt[1])
            self.stats_counter += 1
            self.after(0, self.update_stats)
        self.after(0, self.stop_action)

    def clear_macro(self):
        self.macro_events = []
        self.play_macro_btn.configure(state="disabled")
        self.macro_status.configure(text="Cleared.")

    # ------------------------------------------------------------
    # Idle Detection
    # ------------------------------------------------------------
    def idle_watcher(self):
        while True:
            time.sleep(0.5)
            if self.idle_var.get() and self.is_running:
                current_pos = pyautogui.position()
                if self.idle_position is None:
                    self.idle_position = current_pos
                else:
                    if current_pos != self.idle_position:
                        # Mouse moved -> pause
                        if not self.paused:
                            self.paused = True
                            self.after(0, self.update_status, "paused")
                    else:
                        if self.paused:
                            self.paused = False
                            self.after(0, self.update_status, "running")
                self.idle_position = current_pos
            else:
                self.paused = False
                self.idle_position = None

    # ------------------------------------------------------------
    # Scheduled Start
    # ------------------------------------------------------------
    def set_schedule(self):
        time_str = self.schedule_entry.get().strip()
        if not re.match(r'^\d{1,2}:\d{2}$', time_str):
            messagebox.showerror("Error", "Format: HH:MM (e.g. 14:30)")
            return
        now = datetime.datetime.now()
        target = datetime.datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        if target < now:
            target += datetime.timedelta(days=1)
        delay = (target - now).total_seconds()
        self.scheduled_job = self.after(int(delay*1000), self.start_action)
        messagebox.showinfo("Scheduled", f"Start scheduled at {target.strftime('%H:%M')}")

    # ------------------------------------------------------------
    # Profile Management
    # ------------------------------------------------------------
    def get_profile_list(self):
        profile_dir = os.path.join(true_dir, "profiles")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        return [f.replace('.json','') for f in os.listdir(profile_dir) if f.endswith('.json')]

    def save_profile(self):
        name = ctk.CTkInputDialog(text="Profile name:", title="Save Profile").get_input()
        if not name:
            return
        data = {
            "clicker": {
                "delay": self.delay_entry.get(),
                "random": self.random_var.get(),
                "min": self.min_entry.get(),
                "max": self.max_entry.get(),
                "button": self.button_combo.get(),
                "repeat": self.repeat_entry.get(),
                "pos_mode": self.pos_mode.get(),
                "pos_x": self.pos_x.get(),
                "pos_y": self.pos_y.get(),
                "radius": self.radius_entry.get(),
            },
            "keycombo": {
                "combo": self.combo_entry.get(),
                "repeat": self.combo_repeat.get(),
                "random": self.combo_random_var.get(),
                "min": self.combo_min_entry.get(),
                "max": self.combo_max_entry.get(),
            }
        }
        profile_path = os.path.join(os.path.dirname(__file__), "profiles", f"{name}.json")
        with open(profile_path, 'w') as f:
            json.dump(data, f, indent=2)
        self.profile_list.configure(values=self.get_profile_list())
        self.profile_list.set(name)
        self.current_profile = name

    def load_profile(self):
        name = self.profile_list.get()
        if not name:
            return
        profile_path = os.path.join(os.path.dirname(__file__), "profiles", f"{name}.json")
        with open(profile_path, 'r') as f:
            data = json.load(f)
        # Apply clicker settings
        c = data["clicker"]
        self.delay_entry.delete(0,'end'); self.delay_entry.insert(0,c["delay"])
        self.random_var.set(c["random"])
        self.min_entry.delete(0,'end'); self.min_entry.insert(0,c["min"])
        self.max_entry.delete(0,'end'); self.max_entry.insert(0,c["max"])
        self.button_combo.set(c["button"])
        self.repeat_entry.delete(0,'end'); self.repeat_entry.insert(0,c["repeat"])
        self.pos_mode.set(c["pos_mode"])
        self.pos_x.delete(0,'end'); self.pos_x.insert(0,c["pos_x"])
        self.pos_y.delete(0,'end'); self.pos_y.insert(0,c["pos_y"])
        self.radius_entry.delete(0,'end'); self.radius_entry.insert(0,c["radius"])
        self.toggle_random_fields()
        self.toggle_pos_fields(c["pos_mode"])
        # Key combo settings
        k = data["keycombo"]
        self.combo_entry.delete(0,'end'); self.combo_entry.insert(0,k["combo"])
        self.combo_repeat.delete(0,'end'); self.combo_repeat.insert(0,k["repeat"])
        self.combo_random_var.set(k["random"])
        self.combo_min_entry.delete(0,'end'); self.combo_min_entry.insert(0,k["min"])
        self.combo_max_entry.delete(0,'end'); self.combo_max_entry.insert(0,k["max"])
        self.current_profile = name

    def delete_profile(self):
        name = self.profile_list.get()
        if not name:
            return
        os.remove(os.path.join(os.path.dirname(__file__), "profiles", f"{name}.json"))
        self.profile_list.configure(values=self.get_profile_list())
        self.profile_list.set('')

    # ------------------------------------------------------------
    # UI Helpers
    # ------------------------------------------------------------
    def toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top_var.get())

    def listen_combo(self):
        self.combo_entry.delete(0, 'end')
        self.combo_entry.insert(0, "Press keys...")
        self.after(100, self._capture_combo)

    def _capture_combo(self):
        recorded = keyboard.read_hotkey(suppress=False)
        self.combo_entry.delete(0, 'end')
        self.combo_entry.insert(0, recorded)

    def update_status(self, state):
        if state == "ready":
            self.status_label.configure(text=tr("status_ready"), text_color="#2ecc71")
        elif state == "running":
            self.status_label.configure(text="Status: ACTIVE", text_color="#3498db")
        elif state == "paused":
            self.status_label.configure(text=tr("status_paused"), text_color="#f1c40f")
        else:
            self.status_label.configure(text=f"Status: {state}")

    def update_stats(self):
        self.stats_label.configure(text=f"{tr('stats')} {self.stats_counter}")

# ------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    if os.geteuid() != 0:
        # Try to re‑run with pkexec or sudo
        print("Root required. Restarting with pkexec...")
        os.execvp("pkexec", ["pkexec", sys.executable] + sys.argv)
    app = FedoraAutoClicker()
    app.mainloop()
