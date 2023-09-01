# -*- coding: utf-8 -*-
import os
import json
from . import util
from modules import shared

root_path = os.getcwd()
folders = {
    "ti": os.path.join(root_path, "embeddings"),
    "hyper": os.path.join(root_path, "models", "hypernetworks"),
    "ckpt": os.path.join(root_path, "models", "Stable-diffusion"),
    "lora": os.path.join(root_path, "models", "Lora"),
    "vae": os.path.join(root_path, "models", "VAE")
}

exts = (".bin", ".pt", ".safetensors", ".ckpt")
info_ext = ".info"
vae_suffix = ".vae"


def get_custom_model_folder():
    util.log("Get Custom Model Folder")

    global folders

    if shared.cmd_opts.embeddings_dir and os.path.isdir(shared.cmd_opts.embeddings_dir):
        folders["ti"] = shared.cmd_opts.embeddings_dir

    if shared.cmd_opts.hypernetwork_dir and os.path.isdir(shared.cmd_opts.hypernetwork_dir):
        folders["hyper"] = shared.cmd_opts.hypernetwork_dir

    if shared.cmd_opts.ckpt_dir and os.path.isdir(shared.cmd_opts.ckpt_dir):
        folders["ckpt"] = shared.cmd_opts.ckpt_dir

    if shared.cmd_opts.lora_dir and os.path.isdir(shared.cmd_opts.lora_dir):
        folders["lora"] = shared.cmd_opts.lora_dir


def write_model_info(path, model_info):
    util.log("Write model info to file: " + path)
    with open(os.path.realpath(path), 'w') as f:
        f.write(json.dumps(model_info, indent=4))


def load_model_info(path):
    # util.log("Load model info from file: " + path)
    model_info = None
    with open(os.path.realpath(path), 'r') as f:
        try:
            model_info = json.load(f)
        except Exception as e:
            util.log("Selected file is not json: " + path)
            util.log(e)
            return
        
    return model_info


def get_model_names_by_type(model_type:str) -> list:
    
    model_folder = folders[model_type]

    # get information from filter
    # only get those model names don't have a liblibai model info file
    model_names = []
    for root, dirs, files in os.walk(model_folder, followlinks=True):
        for filename in files:
            item = os.path.join(root, filename)
            # check extension
            base, ext = os.path.splitext(item)
            if ext in exts:
                # find a model
                model_names.append(filename)


    return model_names


def get_model_path_by_type_and_name(model_type:str, model_name:str) -> str:
    util.log("Run get_model_path_by_type_and_name")
    if model_type not in folders.keys():
        util.log("unknown model_type: " + model_type)
        return
    
    if not model_name:
        util.log("model name can not be empty")
        return
    
    folder = folders[model_type]

    # model could be in subfolder, need to walk.
    model_root = ""
    model_path = ""
    for root, dirs, files in os.walk(folder, followlinks=True):
        for filename in files:
            if filename == model_name:
                # find model
                model_root = root
                model_path = os.path.join(root, filename)
                return (model_root, model_path)

    return



