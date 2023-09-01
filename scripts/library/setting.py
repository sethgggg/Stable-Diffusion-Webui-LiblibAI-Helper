# -*- coding: UTF-8 -*-
# collecting settings to here
import json
import os
import modules.scripts as scripts
from . import util


name = "setting.json"
path = os.path.join(scripts.basedir(), name)

data = {
    "model":{
        "max_size_preview": True,
    },
    "tool":{
    }
}


def save():
    print("Saving setting to: " + path)

    json_data = json.dumps(data, indent=4)

    output = ""

    #write to file
    try:
        with open(path, 'w') as f:
            f.write(json_data)
    except Exception as e:
        util.log("Error when writing file:"+path)
        output = str(e)
        util.log(str(e))
        return output

    output = "Setting saved to: " + path
    util.log(output)

    return output


def load():
    # load data into globel data
    global data

    util.log("Load setting from: " + path)

    if not os.path.isfile(path):
        util.log("No setting file, use default")
        return

    json_data = None
    with open(path, 'r') as f:
        json_data = json.load(f)

    # check error
    if not json_data:
        util.log("load setting file failed")
        return

    data = json_data
    return


def save_from_input(max_size_preview, open_url_with_js, always_display, show_btn_on_thumb, proxy):
    global data
    data = {
        "model":{
            "max_size_preview": max_size_preview,
        },
        "tool":{
        }
    }

    output = save()

    if not output:
        output = ""

    return output

