# -*- coding: utf-8 -*-
import os
import json
import requests
import webbrowser
from . import util
from . import model
from . import liblibai
from . import msg_handler
from . import downloader


def open_model_url(msg, open_url_with_js):
    util.log("Start open_model_url")

    output = ""
    result = msg_handler.parse_js_msg(msg)
    if not result:
        util.log("Parsing js ms failed")
        return
    
    model_type = result["model_type"]
    search_term = result["search_term"]

    model_info = liblibai.load_model_info_by_search_term(model_type, search_term)
    if not model_info:
        util.log(f"Failed to get model info for {model_type} {search_term}")
        return ""

    if "modelId" not in model_info.keys():
        util.log(f"Failed to get model id from info file for {model_type} {search_term}")
        return ""

    model_id = model_info["modelId"]
    if not model_id:
        util.log(f"model id from info file of {model_type} {search_term} is None")
        return ""

    url = liblibai.url_dict["modelPage"]+str(model_id)


    # msg content for js
    content = {
        "url":""
    }

    if not open_url_with_js:
        util.log("Open Url: " + url)
        # open url
        webbrowser.open_new_tab(url)
    else:
        util.log("Send Url to js")
        content["url"] = url
        output = msg_handler.build_py_msg("open_url", content)

    util.log("End open_model_url")
    return output


def add_trigger_words(msg):
    util.log("Start add_trigger_words")

    result = msg_handler.parse_js_msg(msg)
    if not result:
        util.log("Parsing js ms failed")
        return
    
    model_type = result["model_type"]
    search_term = result["search_term"]
    prompt = result["prompt"]


    model_info = liblibai.load_model_info_by_search_term(model_type, search_term)
    if not model_info:
        util.log(f"Failed to get model info for {model_type} {search_term}")
        return [prompt, prompt]
    
    if "trainedWords" not in model_info.keys():
        util.log(f"Failed to get trainedWords from info file for {model_type} {search_term}")
        return [prompt, prompt]
    
    trainedWords = model_info["trainedWords"]
    if not trainedWords:
        util.log(f"No trainedWords from info file for {model_type} {search_term}")
        return [prompt, prompt]
    
    if len(trainedWords) == 0:
        util.log(f"trainedWords from info file for {model_type} {search_term} is empty")
        return [prompt, prompt]
    
    # get ful trigger words
    trigger_words = ""
    for word in trainedWords:
        trigger_words = trigger_words + word + ", "

    new_prompt = prompt + " " + trigger_words
    util.log("trigger_words: " + trigger_words)
    util.log("prompt: " + prompt)
    util.log("new_prompt: " + new_prompt)

    util.log("End add_trigger_words")

    # add to prompt
    return [new_prompt, new_prompt]


def use_preview_image_prompt(msg):
    util.log("Start use_preview_image_prompt")

    result = msg_handler.parse_js_msg(msg)
    if not result:
        util.log("Parsing js ms failed")
        return
    
    model_type = result["model_type"]
    search_term = result["search_term"]
    prompt = result["prompt"]
    neg_prompt = result["neg_prompt"]


    model_info = liblibai.load_model_info_by_search_term(model_type, search_term)
    if not model_info:
        util.log(f"Failed to get model info for {model_type} {search_term}")
        return [prompt, neg_prompt, prompt, neg_prompt]
    
    if "images" not in model_info.keys():
        util.log(f"Failed to get images from info file for {model_type} {search_term}")
        return [prompt, neg_prompt, prompt, neg_prompt]
    
    images = model_info["images"]
    if not images:
        util.log(f"No images from info file for {model_type} {search_term}")
        return [prompt, neg_prompt, prompt, neg_prompt]
    
    if len(images) == 0:
        util.log(f"images from info file for {model_type} {search_term} is empty")
        return [prompt, neg_prompt, prompt, neg_prompt]
    
    # get prompt from preview images' meta data
    preview_prompt = ""
    preview_neg_prompt = ""
    for img in images:
        if "meta" in img.keys():
            if img["meta"]:
                if "prompt" in img["meta"].keys():
                    if img["meta"]["prompt"]:
                        preview_prompt = img["meta"]["prompt"]
                
                if "negativePrompt" in img["meta"].keys():
                    if img["meta"]["negativePrompt"]:
                        preview_neg_prompt = img["meta"]["negativePrompt"]

                # we only need 1 prompt
                if preview_prompt:
                    break
            
    if not preview_prompt:
        util.log(f"There is no prompt of {model_type} {search_term} in its preview image")
        return [prompt, neg_prompt, prompt, neg_prompt]
    
    util.log("End use_preview_image_prompt")
    
    return [preview_prompt, preview_neg_prompt, preview_prompt, preview_neg_prompt]


def dl_model_new_version(msg, max_size_preview, skip_nsfw_preview):
    util.log("Start dl_model_new_version")

    output = ""

    result = msg_handler.parse_js_msg(msg)
    if not result:
        output = "Parsing js ms failed"
        util.log(output)
        return output
    
    model_path = result["model_path"]
    version_id = result["version_id"]
    download_url = result["download_url"]

    util.log("model_path: " + model_path)
    util.log("version_id: " + str(version_id))
    util.log("download_url: " + download_url)

    # check data
    if not model_path:
        output = "model_path is empty"
        util.log(output)
        return output

    if not version_id:
        output = "version_id is empty"
        util.log(output)
        return output
    
    if not download_url:
        output = "download_url is empty"
        util.log(output)
        return output

    if not os.path.isfile(model_path):
        output = "model_path is not a file: "+ model_path
        util.log(output)
        return output

    # get model folder from model path
    model_folder = os.path.dirname(model_path)

    # no need to check when downloading new version, since checking new version is already checked
    # check if this model is already existed
    # r = liblibai.search_local_model_info_by_version_id(model_folder, version_id)
    # if r:
    #     output = "This model version is already existed"
    #     util.log(output)
    #     return output

    # download file
    new_model_path = downloader.dl(download_url, model_folder, None, None)
    if not new_model_path:
        output = "Download failed, check console log for detail. Download url: " + download_url
        util.log(output)
        return output

    # get version info
    version_info = liblibai.get_version_info_by_version_id(version_id)
    if not version_info:
        output = "Model downloaded, but failed to get version info, check console log for detail. Model saved to: " + new_model_path
        util.log(output)
        return output

    # now write version info to file
    base, ext = os.path.splitext(new_model_path)
    info_file = base + liblibai.suffix + model.info_ext
    model.write_model_info(info_file, version_info)

    # then, get preview image
    liblibai.get_preview_image_by_model_path(new_model_path, max_size_preview, skip_nsfw_preview)
    
    output = "Done. Model downloaded to: " + new_model_path
    util.log(output)
    return output
