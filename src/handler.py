""" Example handler file. """

import runpod
import demucs.api

# If your handler runs inference on a model, load the model here.
# You will want models to be loaded into memory before starting serverless.
global model
model = "mdx_extra"
# Use another model and segment:
global separator
separator = demucs.api.Separator(model="mdx_extra", segment=12)

def download_url_to_tempfile(url):
    """ Helper function to download a file from a URL to a temporary file. """
    import tempfile
    import requests

    with tempfile.NamedTemporaryFile(delete=False) as f:
        response = requests.get(url)
        f.write(response.content)

    return f.name


def handler(job):
    """ Handler function that will be used to process jobs. """
    global separator
    job_input = job['input']
    newmodel = job_input.get('model', model)
    if newmodel != model:
        separator = demucs.api.Separator(model=newmodel, segment=12)
    if 'url' in job_input:
        url = job_input['url']
        input_file = download_url_to_tempfile(url)
        origin, separated = separator.separate_audio_file(input_file)
        # compress separated into a zip and serve it back as a json base64
        import zipfile
        import base64
        import io
        import os
        import json
        data = {
            "origin": origin,
            "files": separated,
            "data": None
        }
        with io.BytesIO() as buf:
            with zipfile.ZipFile(buf, 'w') as zipf:
                zipf.write(origin, os.path.basename(origin))
                for file in separated:
                    zipf.write(file, os.path.basename(file))
            buf.seek(0)
            data['data'] = base64.b64encode(buf.read()).decode('utf-8')

        return data
    else:
        return {"error": "No URL provided."}


runpod.serverless.start({"handler": handler})
