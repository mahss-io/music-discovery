import json
import os

class FileManager():
    JSON_FILE_EXT = ".json"

    def __init__(self):
        pass

    def _read_file(self, file_path):
        with open(file_path, "r") as f:
            return json.loads(f.read())

    def _write_file(self, file_path, data):
        with open(file_path, "w") as f:
            f.write(json.dumps(data))
    
    def _delete_file(self, file_path):
        os.remove(file_path)