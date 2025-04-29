import os
import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv, set_key
from ulties.config import ELK


class ConfigWindow:
    def __init__(self, root):
        self.root = root
        self._setup_window()
        self._create_fields()
        self._create_save_button()

    def _setup_window(self):
        self.root.title("ELS Config")
        self.root.geometry("250x530")
        self.root.resizable(False, False)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.content_frame = ctk.CTkFrame(self.root, width=600, height=400, corner_radius=10)
        self.content_frame.place(x=0, y=0)

    def _create_fields(self):
        self.fields = {
            "Docker_Name": "es01",
            "ELASTIC_USER": "elastic",
            "ELASTIC_PASS": "uPI3+iREZ*mIihc8gP8+",
            "ELASTIC_CERT": "http_ca.crt",
            "ELASTIC_INDEX": "telegram",
            "SEARCH_CONFIG": "path/export.json"
        }

        self.entries = {}

        for label_text, default_value in self.fields.items():
            self._create_input_field(label_text, default_value)

    def _create_input_field(self, label_text, default_value):
        label = ctk.CTkLabel(self.content_frame, text=label_text, font=("Arial", 12))
        label.pack(pady=5)

        entry = ctk.CTkEntry(self.content_frame, font=("Arial", 12))
        entry.insert(0, default_value)
        entry.pack(pady=5)

        self.entries[label_text] = entry

    def _create_save_button(self):
        save_button = ctk.CTkButton(
            self.content_frame,
            text="Save Configuration",
            command=self.save_config,
            width=250,
            height=50
        )
        save_button.pack(pady=20)

    def save_config(self):
        try:
            dotenv_path = os.path.join(os.getcwd(), "data", ".env")
            load_dotenv(dotenv_path)

            values = {key: entry.get() for key, entry in self.entries.items()}
            values["Docker_Name"] = self._validate_docker_name(values["Docker_Name"])
            values["ELASTIC_PASS"] = self._validate_password(values)
            values["ELASTIC_CERT"] = self._validate_certificate(values)

            for key, val in values.items():
                if key != "Docker_Name":  # We don't save Docker_Name in .env
                    set_key(dotenv_path, key, val)

            messagebox.showinfo("Success", "Configuration saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def _is_invalid(self, text):
        return not text.strip() or text.strip().lower() == "no"

    def _validate_docker_name(self, docker_name):
        return "es01" if self._is_invalid(docker_name) else docker_name

    def _validate_password(self, values):
        if self._is_invalid(values["ELASTIC_PASS"]):
            elk = ELK(values["ELASTIC_USER"], values["Docker_Name"])
            return elk.get_password()
        return values["ELASTIC_PASS"]

    def _validate_certificate(self, values):
        if self._is_invalid(values["ELASTIC_CERT"]):
            elk = ELK(values["ELASTIC_USER"], values["Docker_Name"])
            elk.get_certificate()
            return "./data/http_ca.crt"
        return values["ELASTIC_CERT"]


if __name__ == "__main__":
    root = ctk.CTk()
    app = ConfigWindow(root)
    root.mainloop()
