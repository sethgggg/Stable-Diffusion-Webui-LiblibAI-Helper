# -*- coding: utf-8 -*-
import sys
import requests
import os
from . import util

requests.packages.urllib3.disable_warnings()
dl_ext = ".downloading"


def dl(url, folder, filename, filepath):
    util.log(f'start downloading from: {url}')
    if not folder or not os.path.isdir(folder):
        util.log(f'folder is empty or does not exist: {folder}')
        return
    file_path = filepath or (filename and os.path.join(folder, filename)) or ''

    # first request for header
    ressponse = requests.get(url, stream=True, verify=False, headers=util.def_headers, proxies=util.proxies)
    total_size = int(ressponse.headers['Content-Length'])
    util.log(f"File size: {total_size}")
    util.log(f"Target file path: {file_path}")
    base, ext = os.path.splitext(file_path)

    # check if file is already exist
    count = 2
    new_base = base
    while os.path.isfile(file_path):
        util.log("Target file already exist.")
        new_base = base + "_" + str(count)
        file_path = new_base + ext
        count += 1

    dl_file_path = new_base + dl_ext

    util.log(f"Downloading to temp file: {dl_file_path}")

    downloaded_size = 0
    if os.path.exists(dl_file_path):
        downloaded_size = os.path.getsize(dl_file_path)

    util.log(f"Downloaded size: {downloaded_size}")

    # create header range
    headers = {'Range': 'bytes=%d-' % downloaded_size}
    headers['User-Agent'] = util.def_headers['User-Agent']

    response = requests.get(url, stream=True, verify=False, headers=headers, proxies=util.proxies)

    # write to file
    with open(dl_file_path, "ab") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                downloaded_size += len(chunk)
                f.write(chunk)
                f.flush()

                # progress
                progress = int(50 * downloaded_size / total_size)
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stdout.write("\r[%s%s] %d%%" % ('-' * progress, ' ' * (50 - progress), 100 * downloaded_size / total_size))
                sys.stdout.flush()

    # rename file
    os.rename(dl_file_path, file_path)
    util.log(f"File Downloaded to: {file_path}")
    return file_path

