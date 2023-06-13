import ast
import mimetypes
import os
import time
from typing import List

import gradio as gr
import gradio.routes

from scripts.mo.data.init_storage import initialize_storage
from scripts.mo.environment import *
from scripts.mo.ui_main import main_ui_block

SETTINGS_FILE = 'settings_dev.txt'

mimetypes.init()
mimetypes.add_type("application/javascript", ".js")


class ScriptLoader:
    path_map = {
        "js": os.path.abspath(os.path.join(os.path.dirname(__file__), "javascript")),
    }

    def __init__(self, script_type):
        self.script_type = script_type
        self.path = ScriptLoader.path_map[script_type]
        self.loaded_scripts = []

    @staticmethod
    def get_scripts(path: str, file_type: str) -> List:
        """Returns list of tuples
        Each tuple contains the full filepath and filename as strings
        """
        scripts = []
        dir_list = [os.path.join(path, f) for f in os.listdir(path)]
        files_list = [f for f in dir_list if os.path.isfile(f)]
        for s in files_list:
            # Don't forget the "." for file extension
            if os.path.splitext(s)[1] == f".{file_type}":
                scripts.append((s, os.path.basename(s)))
        return scripts


class JavaScriptLoader(ScriptLoader):
    def __init__(self):
        # Script type set here
        super().__init__("js")
        # Copy the template response
        self.original_template = gradio.routes.templates.TemplateResponse
        # Prep the js files
        self.load_js()
        # reassign the template response to your method, so gradio calls your method instead
        gradio.routes.templates.TemplateResponse = self.template_response

    def load_js(self):
        js_scripts = ScriptLoader.get_scripts(self.path, self.script_type)
        for file_path, file_name in js_scripts:
            with open(file_path, 'r', encoding="utf-8") as file:
                self.loaded_scripts.append(f"\n<!--{file_name}-->\n<script>\n{file.read()}\n</script>")

    def template_response(self, *args, **kwargs):
        """Once gradio calls your method, you call the original, you modify it to include
        your scripts and you return the modified version
        """
        response = self.original_template(*args, **kwargs)
        response.body = response.body.replace(
            '</head>'.encode('utf-8'), f"{''.join(self.loaded_scripts)}\n</head>".encode("utf-8")
        )
        response.init_headers()
        return response


def read_settings():
    with open(SETTINGS_FILE) as f:
        lines = f.readlines()

    result = {}
    for line in lines:
        key, value = line.strip().split(': ')
        result[key] = value
        logger.info(f'{key}: {value}')
    logger.info('Settings loaded.')
    return result


settings = read_settings()

env.storage_type = lambda: settings['storage_type']
env.download_preview = lambda: ast.literal_eval(settings['download_preview'])
env.model_path = lambda: settings['model_path']
env.vae_path = lambda: settings['vae_path']
env.lora_path = lambda: settings['lora_path']
env.hypernetworks_path = lambda: settings['hypernetworks_path']
env.lycoris_path = lambda: settings['lycoris_path']
env.embeddings_path = lambda: settings['embeddings_path']
env.script_dir = ''
env.layout = lambda: settings['layout']
env.card_width = lambda: settings['card_width'] if settings['card_width'] else DEFAULT_CARD_WIDTH
env.card_height = lambda: settings['card_height'] if settings['card_height'] else DEFAULT_CARD_HEIGHT
env.theme = lambda: settings['theme']
initialize_storage()


def storage_type_change(value):
    settings['storage_type'] = value
    logger.info(f'storage_type updated: {value}')


def download_preview_change(value):
    settings['download_preview'] = value
    logger.info(f'download_preview updated: {value}')


def model_path_change(value):
    settings['model_path'] = value
    logger.info(f'model_path updated: {value}')


def vae_path_change(value):
    settings['vae_path'] = value
    logger.info(f'vae_path updated: {value}')


def lora_path_change(value):
    settings['lora_path'] = value
    logger.info(f'lora_path updated: {value}')


def hypernetworks_path_change(value):
    settings['hypernetworks_path'] = value
    logger.info(f'hypernetworks_path updated: {value}')


def embeddings_path_change(value):
    settings['embeddings_path'] = value
    logger.info(f'embeddings_path updated: {value}')


def layout_type_change(value):
    settings['layout'] = value
    logger.info(f'layout updated: {value}')


def card_width_change(value):
    settings['card_width'] = value
    logger.info(f'card_width updated: {value}')


def card_height_change(value):
    settings['card_height'] = value
    logger.info(f'card_height updated: {value}')


def theme_change(value):
    settings['theme'] = value
    logger.info(f'theme updated: {value}')


def save_click():
    with open(SETTINGS_FILE, 'w') as f:
        for key, value in settings.items():
            f.write(f'{key}: {value}\n')
        logger.info('Settings saved')


def settings_block():
    with gr.Column():
        layout_type = gr.Dropdown([LAYOUT_CARDS, LAYOUT_TABLE], value=[env.layout()],
                                  label="Layout type:", info='Select records layout type.')
        card_width = gr.Textbox(env.card_width(), label='Cards width:')
        card_height = gr.Textbox(env.card_height(), label='Cards height:')

        storage_type = gr.Dropdown([STORAGE_SQLITE, STORAGE_FIREBASE], value=[env.storage_type()],
                                   label="Storage type:", info='Select storage type to save data.')

        download_preview = gr.Checkbox(value=env.download_preview(), label='Download Preview')

        model_path = gr.Textbox(env.model_path(), label='Model path:')
        vae_path = gr.Textbox(env.vae_path(), label='VAE path:')
        lora_path = gr.Textbox(env.lora_path(), label='LORA path:')
        hypernetworks_path = gr.Textbox(env.hypernetworks_path(), label='Hypernetworks path:')
        embeddings_path = gr.Textbox(env.embeddings_path(), label="Embeddings path:")
        theme_widget = gr.Textbox(env.theme(), label='Theme:')
        button = gr.Button("Save")

    storage_type.change(storage_type_change, inputs=storage_type)
    model_path.change(model_path_change, inputs=model_path)
    download_preview.change(download_preview_change, inputs=download_preview)
    vae_path.change(vae_path_change, inputs=vae_path)
    lora_path.change(lora_path_change, inputs=lora_path)
    hypernetworks_path.change(hypernetworks_path_change, inputs=hypernetworks_path)
    embeddings_path.change(embeddings_path_change, inputs=embeddings_path)
    layout_type.change(layout_type_change, inputs=layout_type)
    card_width.change(card_width_change, inputs=card_height)
    card_height.change(card_height_change, inputs=card_height)
    theme_widget.change(theme_change, inputs=theme_widget)

    button.click(save_click)


def generator_outer():
    numbers = [1, 2, 3, 4, 5]
    yield 'start'
    for number in numbers:
        yield from generator_inner(number)
    yield 'end'


def generator_inner(number):
    time.sleep(1)
    yield f'my number is {number}'


def testing_block():
    with gr.Column():
        output_widget = gr.Textbox("Tab block for feature testing", interactive=False)
        button = gr.Button("Start")
    button.click(generator_outer, outputs=output_widget)


with gr.Blocks() as demo:
    init_home_button = gr.Button('Init home state')
    with gr.Tab("Model Organizer"):
        main_ui_block()
    with gr.Tab("Settings"):
        settings_block()
    with gr.Tab("Testing"):
        testing_block()

    init_home_button.click(fn=None, _js='invokeHomeInitialStateLoad')

js_loader = JavaScriptLoader()
demo.queue()
demo.launch()
