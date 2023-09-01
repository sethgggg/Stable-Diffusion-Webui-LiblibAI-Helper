# -*- coding: utf-8 -*-
import os
import time
from . import util
from . import model
from . import liblibai
from . import downloader


def send_info(message):
    util.log(message)
    return message


def scan_model(scan_model_types, max_size_preview):
    util.log("Start scan_model")

    # check model types
    if not scan_model_types:
        return send_info("Model Types is None, can not scan.")
    
    model_types = []
    # check type if it is a string
    if type(scan_model_types) == str:
        model_types.append(scan_model_types)
    else:
        model_types = scan_model_types
    
    model_count, image_count = 0, 0
    # scan_log = ""
    for model_type, model_folder in model.folders.items():
        if model_type not in model_types:
            continue

        util.log("Scanning path: " + model_folder)
        for root, dirs, files in os.walk(model_folder, followlinks=True):
            for filename in files:
                # check ext
                item = os.path.join(root, filename)
                base, ext = os.path.splitext(item)
                if ext in model.exts:
                    # ignore vae file
                    if len(base) > 4:
                        if base[-4:] == model.vae_suffix:
                            # find .vae
                            util.log("This is a vae file: " + filename)
                            continue

                    # find a model
                    # get info file
                    info_file = base + liblibai.suffix + model.info_ext
                    # check info file
                    if not os.path.isfile(info_file):
                        util.log("Creating model info for: " + filename)
                        # get model's sha256
                        hash = util.gen_file_sha256(item)

                        if not hash:
                            return send_info("failed generating SHA256 for model:" + filename)
                        
                        # use this sha256 to get model info from liblibai
                        model_info = liblibai.get_model_info_by_hash(hash)
                        print(hash)
                        print(model_info)
                        # delay 1 second for ti
                        if model_type == "ti":
                            util.log("Delay 1 second for TI")
                            time.sleep(1)

                        if model_info is None:
                            return send_info("Connect to Liblibai API service failed. Wait a while and try again")

                        # write model info to file
                        model.write_model_info(info_file, model_info)

                    # set model_count
                    model_count = model_count+1

                    # check preview image
                    liblibai.get_preview_image_by_model_path(item, max_size_preview)
                    image_count = image_count + 1

    return send_info(f"Done. Scanned {model_count} models, checked {image_count} images")


def get_model_info_by_input(model_type, model_name, model_url_or_id, max_size_preview):
    output = ""
    # parse model uuid
    model_uuid = liblibai.get_model_uuid_from_url(model_url_or_id)
    if not model_uuid:
        return send_info(f"failed to parse model id from url: {model_url_or_id}")

    # get model file path
    # model could be in subfolder
    result = model.get_model_path_by_type_and_name(model_type, model_name)
    if not result:
        return send_info("failed to get model file path")
    
    model_root, model_path = result
    if not model_path:
        return send_info("model path is empty")
    
    # get info file path
    base, ext = os.path.splitext(model_path)
    info_file = base + liblibai.suffix + model.info_ext

    # get model info    
    model_info = liblibai.get_version_info_by_model_uuid(model_uuid)

    if not model_info:
        return send_info(f"failed to get model info from url: {model_url_or_id}")

    # write model info to file
    model.write_model_info(info_file, model_info)

    util.log("Saved model info to: "+ info_file)

    # check preview image
    liblibai.get_preview_image_by_model_path(model_path, max_size_preview)

    output = "Model Info saved to: " + info_file
    return output


def check_models_new_version_to_md(model_types:list) -> str:
    new_versions = liblibai.check_models_new_version_by_model_types(model_types, 1)

    count = 0
    output = ""
    if not new_versions:
        output = "No model has new version"
    else:
        output = "Found new version for following models:  <br>"
        for new_version in new_versions:
            count = count+1
            model_path, model_id, model_name, new_verion_id, new_version_name, description, download_url, img_url = new_version
            # in md, each part is something like this:
            # [model_name](model_url)
            # [version_name](download_url)
            # version description
            url = liblibai.url_dict["page"]+str(model_id)

            part = f'<div style="font-size:20px;margin:6px 0px;"><b>Model: <a href="{url}" target="_blank"><u>{model_name}</u></a></b></div>'
            part = part + f'<div style="font-size:16px">File: {model_path}</div>'
            if download_url:
                # replace "\" to "/" in model_path for windows
                model_path = model_path.replace('\\', '\\\\')
                part = part + f'<div style="font-size:16px;margin:6px 0px;">New Version: <u><a href="{download_url}" target="_blank" style="margin:0px 10px;">{new_version_name}</a></u>'
                # add js function to download new version into SD webui by python
                part = part + "    "
                # in embed HTML, onclick= will also follow a ", never a ', so have to write it as following
                part = part + f"<u><a href='#' style='margin:0px 10px;' onclick=\"ch_dl_model_new_version(event, '{model_path}', '{new_verion_id}', '{download_url}')\">[Download into SD]</a></u>"
                
            else:
                part = part + f'<div style="font-size:16px;margin:6px 0px;">New Version: {new_version_name}'
            part = part + '</div>'

            # description
            if description:
                part = part + '<blockquote style="font-size:16px;margin:6px 0px;">'+ description + '</blockquote><br>'

            # preview image            
            if img_url:
                part = part + f"<img src='{img_url}'><br>"
                

            output = output + part

    util.log(f"Done. Find {count} models have new version. Check UI for detail.")

    return output


def get_model_info_by_url(model_url_or_id:str) -> tuple:
    util.log("Getting model info by: " + model_url_or_id)

    # parse model id
    model_id = liblibai.get_model_uuid_from_url(model_url_or_id)
    if not model_id:
        util.log("failed to parse model id from url or id")
        return    

    model_info = liblibai.get_model_info_by_uuid(model_id)
    if model_info is None:
        util.log("Connect to Liblibai API service failed. Wait a while and try again")
        return
    
    if not model_info:
        util.log("failed to get model info from url or id")
        return
    
    # parse model type, model name, subfolder, version from this model info
    # get model type
    if "modelType" not in model_info.keys():
        util.log("model type is not in model_info")
        return
    
    liblibai_model_type = str(model_info["modelType"])
    if liblibai_model_type not in liblibai.model_type_dict.keys():
        util.log("This model type is not supported:"+liblibai_model_type)
        return
    
    model_type = liblibai.model_type_dict[str(liblibai_model_type)]

    # get model type
    if "name" not in model_info.keys():
        util.log("model name is not in model_info")
        return

    model_name = model_info["name"]
    if not model_name:
        util.log("model name is empty")
        model_name = ""

    # get version list
    if "versions" not in model_info.keys():
        util.log("model versions is not in model info")
        return
    
    model_versions = model_info["versions"]
    if not model_versions:
        util.log("model versions is empty")
        return
    
    version_strs = [version["name"] for version in model_versions]

    # get folder by model type
    folder = model.folders[model_type]
    # get subfolders
    subfolders = util.get_subfolders(folder)
    if not subfolders:
        subfolders = []

    # add default root folder
    subfolders.append("/")

    util.log("Get following info for downloading:")
    util.log(f"model_name:{model_name}")
    util.log(f"model_type:{model_type}")
    util.log(f"subfolders:{subfolders}")
    util.log(f"version_strs:{version_strs}")

    return (model_info, model_name, model_type, subfolders, version_strs)


def get_ver_info_by_ver_str(version_str:str, model_info:dict) -> dict:
    if not version_str:
        util.log("version_str is empty")
        return
    
    if not model_info:
        util.log("model_info is None")
        return
    
    # get version list
    if "versions" not in model_info.keys():
        util.log("model_versions is not in model_info")
        return

    model_versions = model_info["versions"]
    if not model_versions:
        util.log("model_versions is Empty")
        return
    
    # find version by version name
    version = list(filter(lambda ver: ver["name"]==version_str, model_versions))
    if not version:
        util.log("can not find version by version name: " + version_str)
        return
    else:
        version = version[0]

    if any([key not in version for key in ["id", "name"]]):
        util.log("this version is not valid")
        return
    
    return version


def get_id_and_dl_url_by_version_str(version_str:str, model_info:dict) -> tuple:
    if not version_str:
        util.log("version_str is empty")
        return
    
    if not model_info:
        util.log("model_info is None")
        return
    
    # get version list
    if "model_versions" not in model_info.keys():
        util.log("model_versions is not in model_info")
        return

    model_versions = model_info["model_versions"]
    if not model_versions:
        util.log("model_versions is Empty")
        return
    
    # find version by version_str
    version = list(filter(lambda ver: ver["name"]==version_str, model_versions))

    if not version:
        util.log("can not find version by version string: " + version_str)
        return
    else:
        version = version[0]
    
    # get version id
    if any([key not in version for key in ["id", "name"]]):
        util.log("this version is not valid")
        return
    
    version_id = version["id"]
    if not version_id:
        util.log("version id is Empty")
        return

    # get download url
    if "downloadUrl" not in version or not version["downloadUrl"]:
        util.log("downloadUrl is not in this version")
        return
    
    downloadUrl = version["downloadUrl"] 
    util.log("Get Download Url: " + downloadUrl)
    
    return (version_id, downloadUrl)
    

def download_model_by_input(model_info:dict, model_type:str, subfolder:str, version_str:str, max_size_preview:bool):
    verify_arg_with_error = [
        (model_info, 'model info is empty'),
        (model_type, 'model type is empty'),
        (subfolder, 'subfolder string is empty'),
        (version_str, 'version string is empty'),
        (model_type in model.folders, f'unknown model type: {model_type}')
    ]
    for verified in verify_arg_with_error:
        if not verified[0]:
            return send_info(verified[1])
    
    model_root_folder = model.folders[model_type]
    subfolder = (subfolder[:1] != "/" and subfolder[:1] != "\\") and subfolder or subfolder[1:]
    model_folder = os.path.join(model_root_folder, subfolder)
    if not os.path.isdir(model_folder):
        return send_info(f'model folder is not a dir: {model_folder}')
    
    # get version info
    ver_info = get_ver_info_by_ver_str(version_str, model_info)
    if not ver_info:
        return send_info("Fail to get version info, check console log for detail")
    
    version_id = ver_info["id"]

    response = liblibai.search_local_model_info_by_version_id(model_folder, version_id)
    if response:
        output = "This model version is already existed"
        util.log(output)
        return output
    else:
        url = ver_info['attachment']['modelSource']
        filename = ver_info['attachment']['modelSourceName']
        if not url:
            return send_info("Fail to get download url, check console log for detail")
        
        # download
        filepath = downloader.dl(url, model_folder, filename, None)
        if not filepath:
            return send_info("Downloading failed, check console log for detail")
        liblibai.record_local_info({"model_version_id": version_id, "model_id": ver_info["modelId"]}, False)

    # get version info
    version_info = liblibai.get_version_info_by_version_id(model_info,version_id)
    if not version_info:
        return send_info("Model downloaded, but failed to get version info, check console log for detail. Model saved to: " + filepath)

    # write version info to file
    base, ext = os.path.splitext(filepath)
    info_file = base + liblibai.suffix + model.info_ext
    model.write_model_info(info_file, version_info)

    # then, get preview image
    liblibai.get_preview_image_by_model_path(filepath, max_size_preview)
    
    return send_info(f'Done. Model downloaded to: {filepath}')
