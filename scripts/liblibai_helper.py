# -*- coding: utf-8 -*-

import os
import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks
from scripts.library import (
    model, 
    setting, 
    liblibai, 
    model_action_liblibai, 
)

root_path = os.getcwd()
extension_path = scripts.basedir()
model.get_custom_model_folder()
liblibai.record_local_info()
setting.load()


def on_ui_tabs():
    # ====Event's function====
    def get_model_names_by_input(model_type, empty_info_only):
        names = liblibai.get_model_names_by_input(model_type, empty_info_only)
        return model_name_drop.update(choices=names)

    def get_model_info_by_url(url):
        response = model_action_liblibai.get_model_info_by_url(url)
        model_info, model_name, model_type, subfolders, version_strs = response if response else ({}, "", "", [], [])
        return [model_info, model_name, model_type, dl_subfolder_drop.update(choices=subfolders), dl_version_drop.update(choices=version_strs)]

    # ====UI====
    with gr.Blocks(analytics_enabled=False) as liblibai_helper:
        with gr.Row():
            with gr.Column(elem_id="left_block", scale=3):
                # init
                max_size_preview = setting.data["model"]["max_size_preview"]
                model_types = list(model.folders.keys())
                no_info_model_names = liblibai.get_model_names_by_input("ckpt", False)

                # session data
                dl_model_info = gr.State({})

                with gr.Box(elem_classes="helper_box"):
                    with gr.Column():
                        gr.Markdown("### 扫描本地模型")
                        with gr.Row():
                            with gr.Column(scale=4):
                                scan_model_types_ckbg = gr.CheckboxGroup(choices=model_types, label="模型种类", value=model_types)
                            with gr.Column(scale=3):
                                max_size_preview_ckb = gr.Checkbox(label="下载最大尺寸的预览图", value=max_size_preview, elem_id="ch_max_size_preview_ckb")

                        scan_model_liblibai_btn = gr.Button(value="开始扫描", variant="primary", elem_id="ch_scan_model_liblibai_btn")
                        scan_model_log_md = gr.Markdown(value="扫描会持续一段时间，请在控制台查看详细信息。", elem_id="ch_scan_model_log_md")

                with gr.Box(elem_classes="helper_box"):
                    with gr.Column():
                        gr.Markdown("### 使用URL从LiblibAI获取模型信息")
                        gr.Markdown("在LiblibAI扫描不到对应的本地模型时可以使用这个功能")
                        with gr.Row():
                            model_type_drop = gr.Dropdown(choices=model_types, label="模型种类", value="ckpt", multiselect=False)
                            model_name_drop = gr.Dropdown(choices=no_info_model_names, label="模型名称", value="", multiselect=False)
                            empty_info_only_ckb = gr.Checkbox(label="只显示没有信息的模型", value=False, elem_id="ch_empty_info_only_ckb", elem_classes="ch_vpadding")

                        model_url_or_id_txtbox = gr.Textbox(label="LiblibAI URL", lines=1, value="")
                        get_liblibai_model_info_by_id_btn = gr.Button(value="获取模型信息", variant="primary")
                        get_model_by_id_log_md = gr.Markdown("")

                with gr.Box(elem_classes="helper_box"):
                    with gr.Column():
                        gr.Markdown("### 模型下载")
                        gr.Markdown("1. 通过LiblibAI URL获取模型信息")
                        dl_model_url_or_id_txtbox = gr.Textbox(label="LiblibAI URL", lines=1, value="")
                        dl_model_info_btn = gr.Button(value="下载模型信息", variant="primary")

                        gr.Markdown(value="2. 选择子文件夹和模型版本")
                        with gr.Row():
                            dl_model_name_txtbox = gr.Textbox(label="模型名称", interactive=False, lines=1, value="")
                            dl_model_type_txtbox = gr.Textbox(label="模型类型", interactive=False, lines=1, value="")
                            dl_subfolder_drop = gr.Dropdown(choices=[], label="子文件夹", value="", interactive=True, multiselect=False)
                            dl_version_drop = gr.Dropdown(choices=[], label="模型版本", value="", interactive=True, multiselect=False)
                        gr.Markdown(value="3. 从LiblibAI下载模型")
                        dl_liblibai_model_by_id_btn = gr.Button(value="下载模型", variant="primary")
                        dl_log_md = gr.Markdown(value="下载状态显示在控制台中。")

                with gr.Box(elem_classes="helper_box"):
                    with gr.Column():
                        gr.Markdown("### 通过LiblibAI检查模型的新版本")
                        model_types_ckbg = gr.CheckboxGroup(choices=model_types, label="模型种类", value=["lora"])
                        check_models_new_version_btn = gr.Button(value="检查模型版本", variant="primary")
                        check_models_new_version_log_md = gr.HTML("这将会花费一些时间，请在控制台中查看详细信息。")

                # ====events====
                # Scan Models for Liblibai
                scan_model_liblibai_btn.click(model_action_liblibai.scan_model, inputs=[scan_model_types_ckbg, max_size_preview_ckb], outputs=scan_model_log_md)

                # Get Liblibai Model Info by Model Page URL
                model_type_drop.change(get_model_names_by_input, inputs=[model_type_drop, empty_info_only_ckb], outputs=model_name_drop)
                empty_info_only_ckb.change(get_model_names_by_input, inputs=[model_type_drop, empty_info_only_ckb], outputs=model_name_drop)

                get_liblibai_model_info_by_id_btn.click(model_action_liblibai.get_model_info_by_input, inputs=[model_type_drop, model_name_drop, model_url_or_id_txtbox, max_size_preview_ckb], outputs=get_model_by_id_log_md)

                # Download Model
                dl_model_info_btn.click(get_model_info_by_url, inputs=dl_model_url_or_id_txtbox, outputs=[dl_model_info, dl_model_name_txtbox, dl_model_type_txtbox, dl_subfolder_drop, dl_version_drop])
                dl_liblibai_model_by_id_btn.click(model_action_liblibai.download_model_by_input, inputs=[dl_model_info, dl_model_type_txtbox, dl_subfolder_drop, dl_version_drop, max_size_preview_ckb], outputs=dl_log_md)

                # Check models' new version
                check_models_new_version_btn.click(model_action_liblibai.check_models_new_version_to_md, inputs=model_types_ckbg, outputs=check_models_new_version_log_md)

            with gr.Column(elem_id="right_block", scale=4):
                with gr.Box(elem_classes="helper_box"):
                    gr.HTML("""
                        <iframe id="liblibai-iframe" 
                            height="1100vh"
                            width="100%" scrolling="auto"
                            src="https://www.liblib.ai/"
                        >
                        </iframe>
                    """)
    
    return (liblibai_helper , "L站助手", "liblibai_helper"),


script_callbacks.on_ui_tabs(on_ui_tabs)



