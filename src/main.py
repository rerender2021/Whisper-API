#!/usr/bin/python
# -*- coding: UTF-8 -*-

import argparse
import os
import sys
import textwrap

from mugwort import Logger

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# args parse
parser = argparse.ArgumentParser(
    description='This is a project that wraps Whisper API by FastAPI.',
    formatter_class=argparse.RawTextHelpFormatter,
    epilog=r'''''')
parser.add_argument('--host', type=str, help='listen host')
parser.add_argument('--port', type=int, help='listen port')
parser.add_argument('--model-path', type=str, help='model path')
parser.set_defaults(host='127.0.0.1', port=8300, model_path="./model/base.en.pt")
params = parser.parse_args()

# init logger
log = Logger('Whisper-API', Logger.INFO)
log.info('Whisper API is starting, please wait...')

# init fastapi & init Whisper backend
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import PlainTextResponse
    import whisper
    from whisper.utils import get_writer

    import time

    import torch
    print("torch info:")
    print(torch.__version__)
    print(torch.version.cuda)
    print(torch.cuda.is_available())

    app = FastAPI(openapi_url=None)
    model = whisper.load_model(params.model_path)
    log.info("whisper model loaded")
    print("model path: ", params.model_path.encode('utf8'))

except Exception as exc:
    log.exception(exc)
    sys.exit(1)


@app.on_event('startup')
async def print_startup_config():
    log.info(
        textwrap.dedent('''
            Whisper API has been started
              Endpoint: POST http://%s:%d/transcribe
        ''').strip(),
        params.host,
        params.port
    )


@app.get('/ping')
async def pingpong_endpoint():
    return PlainTextResponse('pong')

@app.get('/gpu')
async def gpu_endpoint():
    response = {}
    response["gpu"] = str(torch.cuda.is_available())
    return response
    
@app.post('/transcribe')
async def transcribe(
        *, request: Request
):
    if 'content-type' in request.headers:
        content_type = request.headers.get('content-type').lower()
        log.info('Request ContentType: %s', content_type)

        response = {}
        if content_type == 'application/json':
            data = await request.json()
            input_file = data["input_file"]
            output_directory = data["output_directory"]
            initial_prompt = data.get("initial_prompt", "")
            
            print("input_file: ", input_file.encode('utf8'))
            print("output_directory: ", output_directory.encode('utf8'))
            print("initial_promt: ", initial_prompt.encode('utf8'))

            #
            log.info("transcribe start")
            start = time.time()
            if initial_prompt != "":
                result = model.transcribe(input_file, verbose=True, initial_prompt=initial_prompt)
            else:
                result = model.transcribe(input_file, verbose=True)
            end = time.time()
            log.info("transcribe end in: " + str(end - start))

            #
            srt_writer = get_writer("srt", output_directory)
            srt_writer(result, input_file)

            #
            response["result"] = result
            return response
        else:
            log.warning('Unsupported Content-Type: %s', type(content_type))
            return response
    else:
        log.warning('No Content-Type')
        return None


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host=params.host,
        port=params.port,
        log_level='error',
        access_log=False,
        timeout_keep_alive=60 * 60 * 24 # force no timeout
    )
