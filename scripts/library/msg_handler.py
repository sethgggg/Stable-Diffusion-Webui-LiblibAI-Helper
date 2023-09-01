# -*- coding: utf-8 -*-
import json
from . import util

# action list
js_actions = ("open_url", "add_trigger_words", "use_preview_prompt", "dl_model_new_version")
py_actions = ("open_url")


def parse_js_msg(msg):
    util.log("Start parse js msg")
    msg_dict = json.loads(msg)

    # in case client side run JSON.stringify twice
    if (type(msg_dict) == str):
        msg_dict = json.loads(msg_dict)

    if "action" not in msg_dict.keys():
        util.log("Can not find action from js request")
        return

    action = msg_dict["action"]
    if not action:
        util.log("Action from js request is None")
        return

    if action not in js_actions:
        util.log("Unknow action: " + action)
        return

    util.log("End parse js msg")

    return msg_dict


def build_py_msg(action:str, content:dict):
    util.log("Start build_msg")
    if not content:
        util.log("Content is None")
        return
    
    if not action:
        util.log("Action is None")
        return

    if action not in py_actions:
        util.log("Unknow action: " + action)
        return

    msg = {
        "action" : action,
        "content": content
    }


    util.log("End build_msg")
    return json.dumps(msg)