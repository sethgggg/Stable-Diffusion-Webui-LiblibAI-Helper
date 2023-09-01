# -*- coding: utf-8 -*-
import os
import io
import hashlib
import requests
import shutil

version = "1.0.0"
def_headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
proxies = None


def log(message):
    print(f'LiblibAI Helper: {message}')


def read_chunks(file, size=io.DEFAULT_BUFFER_SIZE):
    """Yield pieces of data from a file-like object until EOF."""
    while True:
        chunk = file.read(size)
        if not chunk:
            break
        yield chunk


def gen_file_sha256(filname):
    log("Use Memory Optimized SHA256")
    blocksize=1 << 20
    h = hashlib.sha256()
    length = 0
    with open(os.path.realpath(filname), 'rb') as f:
        for block in read_chunks(f, size=blocksize):
            length += len(block)
            h.update(block)

    hash_value =  h.hexdigest()
    log("sha256: " + hash_value)
    log("length: " + str(length))
    return hash_value


def download_file(url, path):
    log("Downloading file from: " + url)
    # get file
    r = requests.get(url, stream=True, headers=def_headers, proxies=proxies)
    if not r.ok:
        log("Get error code: " + str(r.status_code))
        log(r.text)
        return
    
    # write to file
    with open(os.path.realpath(path), 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)

    log("File downloaded to: " + path)


def get_subfolders(folder:str) -> list:
    log("Get subfolder for: " + folder)
    if not folder:
        log("folder can not be None")
        return
    
    if not os.path.isdir(folder):
        log("path is not a folder")
        return
    
    prefix_len = len(folder)
    subfolders = []
    for root, dirs, files in os.walk(folder, followlinks=True):
        for dir in dirs:
            full_dir_path = os.path.join(root, dir)
            # get subfolder path from it
            subfolder = full_dir_path[prefix_len:]
            subfolders.append(subfolder)

    return subfolders


def get_relative_path(item_path:str, parent_path:str) -> str:
    if not item_path:
        return ""
    if not parent_path:
        return ""
    if not item_path.startswith(parent_path):
        return item_path

    relative = item_path[len(parent_path):]
    if relative[:1] == "/" or relative[:1] == "\\":
        relative = relative[1:]

    # log("relative:"+relative)
    return relative