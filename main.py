import customtkinter as ctk
from elasticsearch import Elasticsearch
import json
import os
from dotenv import load_dotenv
from ulties.transform import ToELK
import arabic_reshaper
from bidi.algorithm import get_display

# Load environment variables
load_dotenv()


class MessageViewerApp(ctk.CTk):
    def __init__(self, toelk, var_list, elastic_connector):
        super().__init__()

        self.toelk = toelk
        self.var_list = var_list
        self.elastic_connector = elastic_connector
        self.current_index = 0
        self.query = {"query": {"match_all": {}}, "size": 60}

        self.messages, self.all_id, self.total_msg = toelk.get_messages_from_elasticsearch(
            var_list, elastic_connector, self.query)

        self.configure_window()
        self.create_widgets()
        self.update_message()

    def configure_window(self):
        self.title("SEnaCH")
        self.geometry("500x720")
        self.minsize(500, 720)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

    def create_widgets(self):
        self.message_label = ctk.CTkLabel(self, text=self.messages[self.current_index],
                                          font=("Kalameh", 18), wraplength=400)
        self.message_label.pack(pady=20)

        self.update_query_frame = ctk.CTkFrame(self)
        self.update_query_frame.pack(side="bottom", fill="x")
        self.update_button = ctk.CTkButton(self.update_query_frame, text="Update", command=self.query_embedd)
        self.update_button.pack(padx=20, pady=10)

        self.nav_frame = ctk.CTkFrame(self)
        self.nav_frame.pack(side="bottom", fill="x")

        self.back_button = ctk.CTkButton(self.nav_frame, text="Previous", command=self.show_previous_message)
        self.back_button.pack(side="left", padx=20, pady=10)

        self.page_label = ctk.CTkLabel(self.nav_frame, text="", font=("Kalameh", 12))
        self.page_label.pack(side="left", padx=20, pady=10)

        self.next_button = ctk.CTkButton(self.nav_frame, text="Next", command=self.show_next_message)
        self.next_button.pack(side="right", padx=20, pady=10)

        self.bottom_input_frame = ctk.CTkFrame(self)
        self.bottom_input_frame.pack(side="bottom", fill="x", pady=2)
        self.entry1 = ctk.CTkEntry(self.bottom_input_frame, font=("Kalameh", 18),
                                   placeholder_text="MustBe ==> thecodez:2", width=220, justify="right")
        self.entry1.pack(side="left", padx=10)

        self.entry3 = ctk.CTkEntry(self.bottom_input_frame, font=("Kalameh", 18),
                                   placeholder_text="MustNot", width=220, justify="right")
        self.entry3.pack(side="right", padx=10)

        self.top_input_frame = ctk.CTkFrame(self)
        self.top_input_frame.pack(side="bottom", fill="x")

        self.entry2 = ctk.CTkEntry(self.top_input_frame, font=("Kalameh", 18),
                                   placeholder_text="ShouldBe...", width=220, justify="right")
        self.entry2.pack(side="left", padx=10)

        self.entry4 = ctk.CTkEntry(self.top_input_frame, font=("Kalameh", 18),
                                   placeholder_text="Size:60", width=220, justify="right")
        self.entry4.pack(side="right", padx=10)

    def show_previous_message(self):
        if self.current_index > 0:
            self.current_index -= 1
        self.update_message()

    def show_next_message(self):
        if self.current_index < len(self.messages) - 1:
            self.current_index += 1
        self.update_message()

    def update_message(self):
        max_length = 700
        full_message = self.messages[self.current_index]
        displayed_message = full_message[:max_length] + "...\n[Show More]" if len(full_message) > max_length else full_message

        self.message_label.configure(text=displayed_message)
        self.page_label.configure(
            text=f"ID: {self.all_id[self.current_index]} | {self.current_index + 1}/{self.total_msg}")

    def get_entry(self, entry_input):
        return [i.strip() for i in entry_input.get().split("|")]

    @staticmethod
    def sperete_fuzziness_boost(text):
        fuzziness = "AUTO"
        boost = 1

        if ":" in text:
            parts = text.split(":")
            if len(parts) == 3:
                text, fuzziness, boost = parts
            else:
                text, fuzziness = parts[0], parts[1]

        return text, fuzziness, boost

    def query_embedd(self):
        must = [self.create_match_query(term) for term in self.get_entry(self.entry1) if term]
        must_not = [{"match": {"text": {"query": self.convert_arabic_to_persian(term)}}}
                    for term in self.get_entry(self.entry3) if term]
        should = [self.create_match_query(term) for term in self.get_entry(self.entry2) if term]

        size = 60
        entry4_val = self.get_entry(self.entry4)
        if entry4_val and entry4_val[0].isdigit():
            size = int(entry4_val[0])

        query = {
            "query": {
                "bool": {
                    "must": must if must else [{"match_all": {}}],
                    "must_not": must_not,
                    "should": should
                }
            },
            "size": size
        }

        print("Generated Query:", json.dumps(query, indent=2, ensure_ascii=False))

        self.messages, self.all_id, self.total_msg = self.toelk.get_messages_from_elasticsearch(
            self.var_list, self.elastic_connector, query)

        self.current_index = 0
        self.update_message()

    def create_match_query(self, term):
        text, fuzziness, boost = self.sperete_fuzziness_boost(self.convert_arabic_to_persian(term))
        return {"match": {"text": {"query": text, "fuzziness": fuzziness, "boost": boost}}}

    @staticmethod
    def convert_arabic_to_persian(text):
        arabic_to_persian_map = {
            "ي": "ی", "ك": "ک", "ة": "ه",
            "ﻷ": "لا", "ﻵ": "لا", "ﻹ": "لا", "ﻺ": "لا",
            "ٱ": "ا"
        }
        return "".join(arabic_to_persian_map.get(char, char) for char in text)


if __name__ == "__main__":
    PATH = "./data/"
    input_file = PATH + "result.json"
    output_file = PATH + "eport.json"

    toelk = ToELK(input_file, output_file)
    var_list = toelk.get_varibles(PATH)
    elastic_connector = toelk.connect_elk()

    if os.getenv("TRANSFORM_REQUEST"):
        toelk.transform()
        toelk.insert_data(var_list, elastic_connector)

    app = MessageViewerApp(toelk, var_list, elastic_connector)
    app.mainloop()