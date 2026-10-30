import customtkinter as ctk
from tkinter import filedialog, messagebox
import minecraft_launcher_lib
import subprocess
import threading
import os
import json
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


def get_launcher_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    path = os.path.join(base, "NexusData")
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "versions"), exist_ok=True)
    os.makedirs(os.path.join(path, "libraries"), exist_ok=True)
    os.makedirs(os.path.join(path, "assets"), exist_ok=True)
    os.makedirs(os.path.join(path, "instances"), exist_ok=True)
    return path


LAUNCHER_DIR = get_launcher_dir()
INSTALLATIONS_FILE = os.path.join(LAUNCHER_DIR, "installations.json")
SETTINGS_FILE = os.path.join(LAUNCHER_DIR, "settings.json")


class NexusLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Nexus Launcher")
        self.geometry("1080x640")
        self.minsize(980, 580)
        self.configure(fg_color="#1b1b1b")

        self.launcher_dir = LAUNCHER_DIR
        self.installations = self.load_json(INSTALLATIONS_FILE, {})
        self.settings = self.load_json(SETTINGS_FILE, {"username": "Player"})

        self.status = None
        self.play_btn = None
        self.play_menu = None
        self.play_var = None
        self.inst_scroll = None
        self.search_entry = None

        self.build_ui()
        self.show_play_page()

    # ================== ДАННЫЕ ==================
    def load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_installed_versions(self):
        try:
            versions = minecraft_launcher_lib.utils.get_installed_versions(self.launcher_dir)
            versions.sort(key=lambda x: x["id"], reverse=True)
            return [v["id"] for v in versions]
        except Exception:
            return []

    def widget_exists(self, widget):
        try:
            return widget is not None and widget.winfo_exists()
        except Exception:
            return False

    # ================== UI ==================
    def build_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="#121212")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        acc = ctk.CTkFrame(self.sidebar, fg_color="#1e1e1e", corner_radius=8)
        acc.pack(fill="x", padx=10, pady=12)

        ctk.CTkLabel(acc, text="👤", font=ctk.CTkFont(size=20)).pack(side="left", padx=10, pady=10)
        info = ctk.CTkFrame(acc, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=8)

        self.username_label = ctk.CTkLabel(
            info,
            text=self.settings.get("username", "Player"),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self.username_label.pack(fill="x")
        ctk.CTkLabel(
            info, text="Оффлайн", font=ctk.CTkFont(size=11),
            text_color="#888", anchor="w"
        ).pack(fill="x")

        ctk.CTkButton(
            acc, text="✎", width=28, height=28,
            fg_color="transparent", hover_color="#333",
            command=self.change_username
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            self.sidebar, text="🟩  JAVA EDITION", anchor="w", height=40,
            fg_color="#1f3d2a", text_color="#4ade80",
            hover_color="#2a2a2a", font=ctk.CTkFont(size=13),
            command=self.show_play_page
        ).pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(
            self.sidebar, text="Nexus v1.0",
            text_color="#555", font=ctk.CTkFont(size=11)
        ).pack(side="bottom", pady=10)

        self.main = ctk.CTkFrame(self, fg_color="#1b1b1b", corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

        self.topbar = ctk.CTkFrame(self.main, height=48, fg_color="#121212", corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        self.tab_play = ctk.CTkButton(
            self.topbar, text="Играть", width=90, height=28,
            fg_color="transparent", hover_color="#2a2a2a",
            command=self.show_play_page
        )
        self.tab_play.pack(side="left", padx=(20, 4), pady=10)

        self.tab_inst = ctk.CTkButton(
            self.topbar, text="Установки", width=100, height=28,
            fg_color="transparent", hover_color="#2a2a2a",
            command=self.show_installations_page
        )
        self.tab_inst.pack(side="left", padx=4, pady=10)

        self.content = ctk.CTkFrame(self.main, fg_color="#1b1b1b")
        self.content.pack(fill="both", expand=True)

    def set_active_tab(self, tab):
        if tab == "play":
            self.tab_play.configure(text_color="#4ade80")
            self.tab_inst.configure(text_color="white")
        else:
            self.tab_play.configure(text_color="white")
            self.tab_inst.configure(text_color="#4ade80")

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()
        self.status = None
        self.play_btn = None
        self.play_menu = None
        self.play_var = None
        self.inst_scroll = None
        self.search_entry = None

    # ================== НИК ==================
    def change_username(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Смена ника")
        dialog.geometry("320x160")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#1b1b1b")

        ctk.CTkLabel(dialog, text="Ник игрока", font=ctk.CTkFont(size=14)).pack(pady=(20, 8))
        entry = ctk.CTkEntry(dialog, width=240)
        entry.insert(0, self.settings.get("username", "Player"))
        entry.pack()
        entry.focus()

        def save():
            name = entry.get().strip() or "Player"
            self.settings["username"] = name
            self.save_json(SETTINGS_FILE, self.settings)
            self.username_label.configure(text=name)
            dialog.destroy()

        ctk.CTkButton(
            dialog, text="Сохранить", width=120,
            fg_color="#3cb371", hover_color="#2e8b57", command=save
        ).pack(pady=20)

    # ================== ИГРАТЬ ==================
    def show_play_page(self):
        self.set_active_tab("play")
        self.clear_content()

        banner = ctk.CTkFrame(self.content, fg_color="#0d0d0d", height=260)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        title_frame = ctk.CTkFrame(banner, fg_color="transparent")
        title_frame.place(relx=0.04, rely=0.28)

        ctk.CTkLabel(title_frame, text="NEXUS", font=ctk.CTkFont(size=34, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="LAUNCHER", font=ctk.CTkFont(size=16), text_color="#4ade80").pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Выбери профиль и нажми Играть",
            font=ctk.CTkFont(size=13), text_color="#aaa"
        ).pack(anchor="w", pady=(12, 0))

        bottom = ctk.CTkFrame(self.content, fg_color="#121212", height=100)
        bottom.pack(side="bottom", fill="x")
        bottom.pack_propagate(False)

        left = ctk.CTkFrame(bottom, fg_color="transparent")
        left.pack(side="left", padx=25, pady=18)

        ctk.CTkLabel(left, text="Профиль", text_color="#888", font=ctk.CTkFont(size=12)).pack(anchor="w")

        self.play_var = ctk.StringVar(value="Нет профилей")
        self.play_menu = ctk.CTkOptionMenu(
            left, variable=self.play_var,
            values=["Нет профилей"], width=300, height=34
        )
        self.play_menu.pack(pady=(4, 0))

        self.play_btn = ctk.CTkButton(
            bottom, text="ИГРАТЬ", width=180, height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3cb371", hover_color="#2e8b57",
            command=self.launch_selected
        )
        self.play_btn.pack(side="right", padx=30, pady=26)

        self.status = ctk.CTkLabel(bottom, text="", text_color="#888")
        self.status.pack(side="right", padx=8)

        self.update_play_menu()

    def update_play_menu(self):
        if not self.widget_exists(self.play_menu):
            return
        names = list(self.installations.keys())
        if names:
            self.play_menu.configure(values=names)
            self.play_var.set(names[0])
        else:
            self.play_menu.configure(values=["Нет профилей"])
            self.play_var.set("Нет профилей")

    # ================== УСТАНОВКИ ==================
    def show_installations_page(self):
        self.set_active_tab("inst")
        self.clear_content()

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=15)

        ctk.CTkLabel(header, text="Установки", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")

        ctk.CTkButton(
            header, text="+ Новая установка", width=150, height=32,
            fg_color="#3cb371", hover_color="#2e8b57",
            command=lambda: self.open_install_dialog()
        ).pack(side="right")

        search_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        search_frame.pack(fill="x", padx=25, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Поиск по названию...", width=280
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_profiles_list())

        self.inst_scroll = ctk.CTkScrollableFrame(self.content, fg_color="#1b1b1b")
        self.inst_scroll.pack(fill="both", expand=True, padx=20, pady=5)

        self.refresh_profiles_list()

    def refresh_profiles_list(self):
        if not self.widget_exists(self.inst_scroll):
            return

        for w in self.inst_scroll.winfo_children():
            w.destroy()

        search = ""
        if self.widget_exists(self.search_entry):
            search = self.search_entry.get().lower()

        profiles = [
            (n, d) for n, d in self.installations.items()
            if not search or search in n.lower() or search in d.get("version", "").lower()
        ]

        if not profiles:
            ctk.CTkLabel(
                self.inst_scroll,
                text="Нет профилей.\nНажми «+ Новая установка»",
                text_color="#666", font=ctk.CTkFont(size=14)
            ).pack(pady=50)
            return

        for name, data in profiles:
            version = data.get("version", "")
            card = ctk.CTkFrame(self.inst_scroll, fg_color="#252525", corner_radius=8, height=56)
            card.pack(fill="x", pady=3, padx=4)
            card.pack_propagate(False)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=12)

            ctk.CTkLabel(
                left, text=name, font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
            ).pack(anchor="w")
            ctk.CTkLabel(
                left, text=version, font=ctk.CTkFont(size=11), text_color="#888", anchor="w"
            ).pack(anchor="w")

            ctk.CTkButton(
                card, text="Играть", width=70, height=28,
                fg_color="#3cb371", hover_color="#2e8b57",
                command=lambda n=name: self.quick_play(n)
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                card, text="⚙", width=32, height=28,
                fg_color="#333", hover_color="#444",
                command=lambda n=name: self.open_install_dialog(n)
            ).pack(side="right", padx=2)

            ctk.CTkButton(
                card, text="✕", width=32, height=28,
                fg_color="#c0392b", hover_color="#a93226",
                command=lambda n=name: self.delete_profile(n)
            ).pack(side="right", padx=4)

    # ================== ДИАЛОГ ==================
    def open_install_dialog(self, edit_name=None):
        is_edit = edit_name is not None
        data = self.installations.get(edit_name, {}) if is_edit else {}

        dialog = ctk.CTkToplevel(self)
        dialog.title("Настроить установку" if is_edit else "Новая установка")
        dialog.geometry("520x520")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#1b1b1b")
        dialog.focus()

        ctk.CTkLabel(
            dialog,
            text="Настроить установку" if is_edit else "Новая установка",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(18, 12))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", padx=40)

        # НАЗВАНИЕ
        ctk.CTkLabel(form, text="НАЗВАНИЕ", text_color="#aaa", font=ctk.CTkFont(size=11)).pack(anchor="w")
        name_entry = ctk.CTkEntry(form, width=420, height=32)
        name_entry.insert(0, edit_name if is_edit else "")
        name_entry.pack(pady=(2, 12), anchor="w")

        # ВЕРСИЯ
        ctk.CTkLabel(form, text="ВЕРСИЯ", text_color="#aaa", font=ctk.CTkFont(size=11)).pack(anchor="w")

        version_combo = ctk.CTkComboBox(form, width=420, height=32, values=["Загрузка..."])
        version_combo.set("Загрузка...")
        version_combo.pack(pady=(2, 6), anchor="w")

        status_ver = ctk.CTkLabel(
            form, text="Загружаю список...", text_color="#888", font=ctk.CTkFont(size=11)
        )
        status_ver.pack(anchor="w", pady=(0, 10))

        def load_versions():
            try:
                installed_list = self.get_installed_versions()
                remote = minecraft_launcher_lib.utils.get_version_list()
                releases = [v["id"] for v in remote if v["type"] == "release"]
                all_versions = installed_list + [v for v in releases if v not in installed_list]

                def apply():
                    if not all_versions:
                        version_combo.configure(values=["Нет версий"])
                        version_combo.set("Нет версий")
                        status_ver.configure(text="Нет версий")
                        return
                    version_combo.configure(values=all_versions)
                    if is_edit and data.get("version") in all_versions:
                        version_combo.set(data["version"])
                    else:
                        version_combo.set(all_versions[0])
                    status_ver.configure(
                        text=f"В Nexus: {len(installed_list)}  |  Всего: {len(all_versions)}"
                    )

                dialog.after(0, apply)
            except Exception:
                def err():
                    installed = self.get_installed_versions()
                    version_combo.configure(values=installed if installed else ["Ошибка"])
                    if installed:
                        version_combo.set(installed[0])
                    status_ver.configure(text="Только локальные версии Nexus")
                dialog.after(0, err)

        threading.Thread(target=load_versions, daemon=True).start()

        # ПАПКА ИГРЫ
        default_instance = os.path.join(self.launcher_dir, "instances", "default")
        ctk.CTkLabel(form, text="ПАПКА ИГРЫ", text_color="#aaa", font=ctk.CTkFont(size=11)).pack(anchor="w")
        dir_frame = ctk.CTkFrame(form, fg_color="transparent")
        dir_frame.pack(fill="x", pady=(2, 4))

        dir_entry = ctk.CTkEntry(dir_frame, width=340, height=32)
        dir_entry.insert(0, data.get("directory", default_instance))
        dir_entry.pack(side="left")

        def reset_dir():
            dir_entry.delete(0, "end")
            dir_entry.insert(0, default_instance)

        ctk.CTkButton(
            dir_frame, text="✕", width=32, height=32,
            fg_color="#333", hover_color="#444", command=reset_dir
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            dir_frame, text="Обзор", width=70, height=32,
            command=lambda: self.browse_dir(dir_entry)
        ).pack(side="left")

        ctk.CTkLabel(
            form,
            text=f"Версии хранятся в Nexus:\n{self.launcher_dir}",
            text_color="#666", font=ctk.CTkFont(size=10),
            wraplength=400, justify="left"
        ).pack(anchor="w", pady=(0, 12))

        # JVM
        ctk.CTkLabel(form, text="АРГУМЕНТЫ JVM", text_color="#aaa", font=ctk.CTkFont(size=11)).pack(anchor="w")
        jvm_entry = ctk.CTkEntry(form, width=420, height=32)
        jvm_entry.insert(0, data.get("jvm", "-Xms2G -Xmx4G"))
        jvm_entry.pack(pady=(2, 16), anchor="w")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=8)

        def save():
            name = name_entry.get().strip()
            version = version_combo.get()
            directory = dir_entry.get().strip() or default_instance
            jvm = jvm_entry.get().strip() or "-Xms2G -Xmx4G"

            if not name:
                messagebox.showwarning("Внимание", "Введи название")
                return
            if not version or version in ["Загрузка...", "Нет версий", "Ошибка"]:
                messagebox.showwarning("Внимание", "Выбери версию")
                return
            if not is_edit and name in self.installations:
                messagebox.showwarning("Внимание", "Такой профиль уже есть")
                return
            if is_edit and name != edit_name and name in self.installations:
                messagebox.showwarning("Внимание", "Такой профиль уже есть")
                return

            dialog.destroy()
            threading.Thread(
                target=self.save_profile,
                args=(edit_name, name, version, directory, jvm),
                daemon=True
            ).start()

        ctk.CTkButton(
            btn_frame, text="Отмена", width=110, height=36,
            fg_color="#333", hover_color="#444", command=dialog.destroy
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame, text="Сохранить", width=130, height=36,
            fg_color="#3cb371", hover_color="#2e8b57", command=save
        ).pack(side="left", padx=8)

    def browse_dir(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def save_profile(self, old_name, name, version, directory, jvm):
        try:
            # 1. Сразу сохраняем профиль
            profile = {
                "version": version,
                "directory": directory,
                "jvm": jvm
            }

            if old_name and old_name != name and old_name in self.installations:
                del self.installations[old_name]

            self.installations[name] = profile
            self.save_json(INSTALLATIONS_FILE, self.installations)

            self.after(0, self.update_play_menu)
            self.after(0, self.refresh_profiles_list)
            self.safe_set_status(f"Профиль «{name}» сохранён")

            # 2. Скачиваем версию в Nexus
            self.safe_set_status(f"Скачиваю {version}...")
            try:
                minecraft_launcher_lib.install.install_minecraft_version(
                    version, self.launcher_dir
                )
                self.safe_set_status(f"Готово: {name}")
                self.after(0, lambda: messagebox.showinfo(
                    "Готово",
                    f"Профиль «{name}»\nВерсия: {version}"
                ))
            except Exception as e:
                self.safe_set_status("Профиль сохранён (ошибка загрузки)")
                self.after(0, lambda: messagebox.showwarning(
                    "Профиль создан",
                    f"Профиль сохранён.\nОшибка скачивания:\n{e}"
                ))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.safe_set_status("Ошибка")

    # ================== ЗАПУСК ==================
    def quick_play(self, name):
        self.show_play_page()
        if self.play_var is not None:
            self.play_var.set(name)
        self.launch_selected()

    def launch_selected(self):
        if not self.play_var:
            return
        selected = self.play_var.get()
        if selected in ["Нет профилей", ""]:
            messagebox.showwarning("Внимание", "Сначала создай профиль")
            return

        data = self.installations.get(selected)
        if not data:
            return

        version = data["version"]
        directory = data.get(
            "directory",
            os.path.join(self.launcher_dir, "instances", "default")
        )
        jvm = data.get("jvm", "-Xms2G -Xmx4G")
        username = self.settings.get("username", "Player")

        if self.widget_exists(self.play_btn):
            self.play_btn.configure(state="disabled", text="ЗАПУСК...")

        threading.Thread(
            target=self._launch,
            args=(version, directory, jvm, username),
            daemon=True
        ).start()

    def _launch(self, version, directory, jvm, username):
        try:
            self.safe_set_status("Проверяю файлы...")

            try:
                minecraft_launcher_lib.install.install_minecraft_version(
                    version, self.launcher_dir
                )
            except Exception as e:
                print("Предупреждение:", e)

            options = {
                "username": username,
                "uuid": "00000000-0000-0000-0000-000000000000",
                "token": "0",
                "launcherName": "NexusLauncher",
                "launcherVersion": "1.0",
                "jvmArguments": jvm.split()
            }

            self.safe_set_status("Запускаю...")

            command = minecraft_launcher_lib.command.get_minecraft_command(
                version, self.launcher_dir, options
            )

            os.makedirs(directory, exist_ok=True)
            if "--gameDir" in command:
                idx = command.index("--gameDir")
                command[idx + 1] = directory
            else:
                command.extend(["--gameDir", directory])

            subprocess.run(command, cwd=directory)
            self.safe_set_status("Игра закрыта")
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.safe_set_status("Ошибка")
        finally:
            def restore():
                if self.widget_exists(self.play_btn):
                    self.play_btn.configure(state="normal", text="ИГРАТЬ")
            self.after(0, restore)

    def delete_profile(self, name):
        if messagebox.askyesno("Удаление", f"Удалить «{name}»?"):
            del self.installations[name]
            self.save_json(INSTALLATIONS_FILE, self.installations)
            self.update_play_menu()
            self.refresh_profiles_list()

    def safe_set_status(self, text):
        def _update():
            if self.widget_exists(self.status):
                self.status.configure(text=text)
        self.after(0, _update)


if __name__ == "__main__":
    app = NexusLauncher()
    app.mainloop()