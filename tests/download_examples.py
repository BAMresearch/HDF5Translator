import requests
import os 
import zipfile

url = "https://zenodo.org/records/10925972/files/example_configurations.zip"
r = requests.get(url, stream=True)

file_name = 'example_configurations.zip'
download_path = '.'
unzip_path = '.'

with open(file_name, 'wb') as f:
    for chunk in r.iter_content(chunk_size=16*1024):
        f.write(chunk)

with zipfile.ZipFile(os.path.join('.', file_name), 'r') as zip_ref:
    zip_ref.extractall(unzip_path)
