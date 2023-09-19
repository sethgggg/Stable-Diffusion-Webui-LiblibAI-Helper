# -*- coding: utf-8 -*-
import os
import time
import uuid
import json
import re
import requests
from . import util
from . import model
from pathlib import Path
from copy import deepcopy

suffix = ".liblibai"

url_dict = {
    "page": "https://www.liblib.ai/modelinfo/",
    "uuid": "https://www.liblib.ai/model/getByUuid/",
    "hash": "https://www.liblib.ai/model-version/hash/",
    "log": "https://www.liblib.ai/api/www/log/acceptor/f"
}

model_type_dict = {
    "1": "ckpt",        # Checkpoint
    "2": "ti",          # Textual Inversion
    "3": "hyper",       # Hypernetwork,
    "5": "lora",        # LoRA
    "6": "lora",        # LyCORIS
    "11": "vae"         # VAE
}


def record_local_info(data={}, show=True):
    log_headers = deepcopy(util.def_headers)
    log_headers.update({"Content-Type":"application/json", "Cookie": "", "Pragma": "no-cache"})
    body = {
        "t": show and 1 or 2,
        "e": show and "LHelper.page.show" or "LHelper.page.download",
        "ct": int(time.time() * 1000),
        "sys": "L-Helper",
        "cid": uuid.UUID(int=uuid.getnode()).hex[-12:],
        "page": 11,
        "pageUrl": "https://www.liblib.ai",
        "ua": log_headers["User-Agent"],
        "var": data
    }
    requests.post(url_dict["log"], data=json.dumps(body), headers=log_headers)


def get_full_size_image_url(image_url, width):
    return re.sub('/width=\d+/', '/width=' + str(width) + '/', image_url)


def get_model_info_by_hash(hash:str):
    util.log("Request model info from liblibai")

    if not hash:
        util.log("hash is empty")
        return

    r = requests.get(url_dict["hash"]+hash, headers=util.def_headers, proxies=util.proxies)
    if not r.ok:
        if r.status_code == 404:
            # this is not a liblibai model
            util.log("Liblibai does not have this model")
            return {}
        else:
            util.log("Get error code: " + str(r.status_code))
            util.log(r.text)
            return
    # try to get content
    content = None
    try:
        content = r.json()
    except Exception as e:
        print(f'parser json response failed: {e}')
        return
    
    if not content:
        util.log("error, content from liblibai is None")
        return
    
    return content


def get_model_info_by_uuid(model_uuid):
    util.log("request model info from liblibai")

    if not model_uuid:
        util.log("model uuid is empty")
        return

    response = requests.post(url_dict["uuid"]+str(model_uuid), headers=util.def_headers, proxies=util.proxies)
    if not response.ok:
        if response.status_code == 404:
            util.log("liblibai does not have this model")
            return 
        else:
            util.log(f'error {response.status_code}: {response.text}')
            return

    try:
        content = response.json()
    except Exception as e:
        util.log(f'parser response failed: {str(e)}')
        util.log(f'response: {response.text}')
        return
    if not content:
        util.log("error, content from liblibai is None")
        return
    return content.get("data")


def get_version_info_by_version_id(model_info:dict, version_id:str) -> dict:
    util.log("extract version info")

    if not version_id:
        util.log("version id is empty")
        return

    if "versions" not in model_info:
        util.log('not find version info from model info')
        return

    valid_version = list(filter(lambda version: version['id']==version_id, model_info['versions']))
    if not valid_version:
        return

    content = deepcopy(model_info)
    content["versions"] = valid_version
    return content
    

def get_version_info_by_model_uuid(id:str) -> dict:
    model_info = get_model_info_by_uuid(id)
    if not model_info:
        util.log(f"Failed to get model info by id: {id}")
        return
    
    # check content to get version id
    if "versions" not in model_info.keys():
        util.log("There is no model versions in this model_info")
        return
    
    if not model_info["versions"]:
        util.log("model versions is None")
        return
    
    if len(model_info["versions"])==0:
        util.log("model versions is Empty")
        return
    
    def_version = model_info["versions"][0]
    if not def_version:
        util.log("default version is None")
        return
    
    if "id" not in def_version.keys():
        util.log("default version has no id")
        return
    
    version_id = def_version["id"]
    
    if not version_id:
        util.log("default version's id is None")
        return

    version_info = get_version_info_by_version_id(model_info, version_id)
    if not version_info:
        util.log(f"Failed to get version info by version_id: {version_id}")
        return
    return version_info


def load_model_info_by_search_term(model_type, search_term):
    util.log(f"Load model info of {search_term} in {model_type}")
    if model_type not in model.folders.keys():
        util.log("unknow model type: " + model_type)
        return
    
    # search_term = subfolderpath + model name + ext. And it always start with a / even there is no sub folder
    base, ext = os.path.splitext(search_term)
    model_info_base = base
    if base[:1] == "/":
        model_info_base = base[1:]

    model_folder = model.folders[model_type]
    model_info_filename = model_info_base + suffix + model.info_ext
    model_info_filepath = os.path.join(model_folder, model_info_filename)

    if not os.path.isfile(model_info_filepath):
        util.log("Can not find model info file: " + model_info_filepath)
        return
    
    return model.load_model_info(model_info_filepath)


def get_model_names_by_type_and_filter(model_type:str, filter:dict) -> list:
    
    model_folder = model.folders[model_type]

    # set filter
    # only get models don't have a liblibai info file
    no_info_only = False
    empty_info_only = False

    if filter:
        if "no_info_only" in filter.keys():
            no_info_only = filter["no_info_only"]
        if "empty_info_only" in filter.keys():
            empty_info_only = filter["empty_info_only"]

    # only get those model names don't have a liblibai model info file
    model_names = []
    for root, dirs, files in os.walk(model_folder, followlinks=True):
        for filename in files:
            item = os.path.join(root, filename)
            # check extension
            base, ext = os.path.splitext(item)
            if ext in model.exts:
                # find a model

                # check filter
                if no_info_only:
                    # check model info file
                    info_file = base + suffix + model.info_ext
                    if os.path.isfile(info_file):
                        continue

                if empty_info_only:
                    # check model info file
                    info_file = base + suffix + model.info_ext
                    if os.path.isfile(info_file):
                        # load model info
                        model_info = model.load_model_info(info_file)
                        # check content
                        if model_info:
                            if "id" in model_info.keys():
                                # find a non-empty model info file
                                continue

                model_names.append(filename)

    return model_names


def get_model_names_by_input(model_type, empty_info_only):
    return get_model_names_by_type_and_filter(model_type, {"empty_info_only":empty_info_only})
    

def get_model_uuid_from_url(url:str) -> str:
    util.log("extract model uuid from url")
    if not url:
        util.log("url or model uuid can not be empty")
        return ""

    if re.match("^[a-zA-Z0-9]{32}$", url):
        return str(url)
    
    s = re.sub("\\?.+$", "", url).split("/")
    if len(s) < 2:
        util.log("url is not valid")
        return ""
    elif re.match("^[a-zA-Z0-9]{32}$", s[-1]):
        return s[-1]
    else:
        util.log("There is no model id in this url")
        return ""


def get_preview_image_by_model_path(model_path:str, max_size_preview):
    if not model_path:
        util.log("model_path is empty")
        return

    if not os.path.isfile(model_path):
        util.log("model_path is not a file: "+model_path)
        return

    base, ext = os.path.splitext(model_path)
    sec_preview = base + ".preview.png"
    info_file = base + suffix + model.info_ext

    # check preview image
    if not os.path.isfile(sec_preview):
        # need to download preview image
        util.log("Checking preview image for model: " + model_path)
        # load model_info file
        if os.path.isfile(info_file):
            model_info = model.load_model_info(info_file)
            if not model_info:
                util.log("Model Info is empty")
                return
            if "versions" in model_info.keys() and len(model_info["versions"]) > 0:
                version_info = model_info["versions"][0]
                image_group = version_info.get("imageGroup")
                if image_group and "images" in image_group and image_group["images"]:
                    for img_dict in image_group["images"]:
                        if "imageUrl" in img_dict.keys():
                            img_url = img_dict["imageUrl"]
                            if max_size_preview:
                                if "width" in img_dict.keys() and img_dict["width"]:
                                    img_url = get_full_size_image_url(img_url, img_dict["width"])
                            util.download_file(img_url, sec_preview)
                            break


def search_local_model_info_by_version_id(folder:str, version_id:int) -> dict:
    util.log("Searching local model by version id")
    util.log("folder: " + folder)
    util.log("version_id: " + str(version_id))

    if not folder:
        util.log("folder is none")
        return

    if not os.path.isdir(folder):
        util.log("folder is not a dir")
        return
    
    if not version_id:
        util.log("version_id is none")
        return
    
    # search liblibai model info file
    for filename in os.listdir(folder):
        # check ext
        base, ext = os.path.splitext(filename)
        if ext == model.info_ext:
            # find info file
            if len(base) < 9:
                # not a liblibai info file
                continue

            if base[-9:] == suffix:
                # find a liblibai info file
                path = os.path.join(folder, filename)
                model_info = model.load_model_info(path)
                if not model_info:
                    continue

                if "versions" not in model_info.keys():
                    continue
                if not model_info["versions"] or "id" not in model_info["versions"][0]:
                    continue

                find_id = model_info["versions"][0]["id"]
                if not find_id:
                    continue

                # util.log(f"Compare version id, src: {id}, target:{version_id}")
                if str(find_id) == str(version_id):
                    # find the one
                    return model_info
    return


def check_model_new_version_by_path(model_path):
    if not model_path:
        util.log("model path is empty")
        return

    if not os.path.isfile(model_path):
        util.log(f'model path is not a file: {model_path}')
        return
    
    base, ext = os.path.splitext(model_path)
    info_file = base + suffix + model.info_ext
    
    if not os.path.isfile(info_file):
        return
    
    model_info_file = model.load_model_info(info_file)
    if not model_info_file or "versions" not in model_info_file:
        return
    
    local_version_id = model_info_file["versions"][0]["id"]
    if not local_version_id:
        return

    if "uuid" not in model_info_file:
        return
    
    model_uuid = model_info_file["uuid"]
    if not model_uuid:
        return

    model_info = get_model_info_by_uuid(model_uuid)
    if not model_info or "versions" not in model_info:
        return
    
    model_versions = model_info["versions"]
    if not model_versions:
        return
    
    latest_version = model_versions[0]
    if not latest_version or "id" not in latest_version:
        return
    
    latest_version_id = latest_version["id"]
    if not latest_version_id:
        return

    util.log(f"Compare version id, local: {local_version_id}, remote: {latest_version_id} ")
    if latest_version_id == local_version_id:
        return

    model_name = 'name' in model_info and model_info['name'] or ''
    latest_version_name = 'name' in latest_version and latest_version['name'] or ''
    description = 'description' in latest_version and latest_version['description'] or ''
    download_url = 'downloadUrl' in latest_version and latest_version['downloadUrl'] or ''

    img_url = ""
    if "images" in latest_version.keys():
        if latest_version["images"] and latest_version["images"][0]:
            if "url" in latest_version["images"][0].keys():
                img_url = latest_version["images"][0]["url"] or ''

    return (model_path, model_uuid, model_name, latest_version_id, latest_version_name, description, download_url, img_url)


def check_models_new_version_by_model_types(model_types:list, delay:float=1) -> list:
    util.log("Checking models' new version")

    if not model_types:
        return []

    # check model types, which cloud be a string as 1 type
    mts = []
    if type(model_types) == str:
        mts.append(model_types)
    elif type(model_types) == list:
        mts = model_types
    else:
        util.log(f"Unknow model types: {model_types}")
        return []

    new_versions = []
    # walk all models
    for model_type, model_folder in model.folders.items():
        if model_type not in mts:
            continue

        util.log("Scanning path: " + model_folder)
        for root, dirs, files in os.walk(model_folder, followlinks=True):
            for filename in files:
                # check ext
                item = os.path.join(root, filename)
                base, ext = os.path.splitext(item)
                if ext in model.exts:
                    # find a model
                    response = check_model_new_version_by_path(item)

                    if not response or not response[3]:
                        continue

                    new_version_id = response[3]
                    if any([version[3] == new_version_id for version in new_versions]):
                        util.log("New version is already in list")
                        continue

                    # search this new version id to check if this model is already downloaded
                    target_model_info = search_local_model_info_by_version_id(root, new_version_id)
                    if target_model_info:
                        util.log("New version is already existed")
                        continue
                    new_versions.append(response)
    return new_versions



