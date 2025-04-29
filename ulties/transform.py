from dotenv import load_dotenv, set_key
import os
import re
import json
import os
import json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
import pprint


# <--------------------- Clear Functions -------------------->

def clean_text(text:str) -> str:
    text = text.replace("\n", " ").replace("\t", " ")
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'[.,!؟،؛:]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clear_text(text:str) -> str:
    
    # text type checking
    if type(text) == list:
        temp = []
        for i in text:
            if type(i) != dict:
                temp.append(i)

        text = " ".join(temp)
        text = clean_text(text)
        return text
    else:
        text = clean_text(text)
        return text

# <--------------------- Clear Functions -------------------->


class ToELK:
    def __init__(self, input_file, output_file):
        self.input_file = input_file 
        self.output_file = output_file
        
        self.var_list = self.get_varibles()


    # TODO: effect to all
    @staticmethod
    def open_js_file(file_path, mode="r", encoding="utf-8"):
        with open(file_path, mode, encoding=encoding) as f:
            return json.load(f)

    def transform(self):
        with open(self.input_file, "r", encoding="utf-8") as js:
            data = json.load(js)

        with open(self.output_file, "w", encoding="utf-8") as file:
            file.write("[\n")  # Start JSON array
            first = True

            len_all_msg = len(data["messages"])
            for i in range(len_all_msg):
                # check type
                type_id = data["messages"][i]["type"]
                if type_id == "message":

                    item = {
                        "id_num":  data["messages"][i]["id"],
                        "from_person": data["messages"][i]["date"],
                        "date": data["messages"][i]["date_unixtime"],
                        "text": clear_text(data["messages"][i]["text"]),
                    }

                    if not first:
                        file.write(",\n")  # Add a comma between JSON objects
                    json.dump(item, file, ensure_ascii=False, indent=4)
                    first = False
            file.write("\n]")  # End JSON array

    @staticmethod
    def check_varibles(var_list):
        """_summary_
        Raises:
            EnvironmentError: check assertion for continuous operation.
        """
        if not all(var_list):
            raise EnvironmentError("all Varible not exist !")
        else:
            print("All Varibles exist!")

    def get_varibles(self, env_path_file:str = "./data/.env",) -> list:
        """_summary_

        Args:
            env_vars (_type_): path of .env file, no directory.

        Returns:
            list: list of env variables from path.
        """
        
        load_dotenv(env_path_file)
        USR = os.getenv("ELASTIC_USER")
        PASS = os.getenv("ELASTIC_PASS")
        CRT_Adre = os.getenv("ELASTIC_CERT")
        index_name = os.getenv("ELASTIC_INDEX")
        export_file = os.getenv("EXPORT_FILE")
        return [USR, PASS, CRT_Adre, index_name, export_file]
    
    def connect_elk(self, localhost:str="https://localhost:9200"):
        """_summary_

        Args:
            var_list (_type_): use diffrent host and port for connect to elastic.

        Returns:
            _type_: return elastic connector
        """


        self.check_varibles(self.var_list)
        es = Elasticsearch(
            localhost,
            ca_certs=self.var_list[2],
            basic_auth=(self.var_list[0], self.var_list[1])
        )
        # # Check connection
        if es.ping():
            print("Connected to Elasticsearch")
            return es
        else:
            print("Could not connect to Elasticsearch")

    def insert_data(self, var_list, elastic_connector):
        with open(self.output_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            data_insert = [
                {
                    "_index": var_list[3],       # Index name
                    # Unique identifier for the document
                    "_id": doc["id_num"],
                    "_source": doc              # Document content
                }
                for doc in data
            ]
            helpers.bulk(elastic_connector, data_insert)
            print("data inserted successfully!")

    def raw_query(self, query_file="query.json"):
        
        
        with open(query_file, "r", encoding="utf-8") as file:
            query = json.load(file)
            return query
    def read_data(self, elastic_connector, query):
        response = elastic_connector.search(index=self.var_list[3], body=query)
        pprint.pp(dict(response))

    def get_messages_from_elasticsearch(self, varl_list, elastic_connector, query):

        response = elastic_connector.search(index=varl_list[3], body=query)
        messages = [hit['_source']['text'] for hit in response['hits']['hits']]
        all_id = [hit["_id"] for hit in response["hits"]["hits"]]
        total_msg = response["hits"]["total"]["value"]
        return messages, all_id, total_msg


# TODO: for all platform connector 
# TODO: add all automation to connector and varibles

if __name__ == "__main__":
    PATH = "./data/"
    inp = PATH + "result.json"
    out = PATH +"exported.json"
    env_path_file = PATH +".env"
    
    toelk = ToELK(inp, out)
    connector = toelk.connect_elk()
    query = toelk.raw_query(query_file="../data/query.json")
    toelk.read_data(connector, query )
    

