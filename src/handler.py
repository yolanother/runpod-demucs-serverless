""" Example handler file. """

import runpod
from runpod.serverless.utils import rp_upload
import demucs.api
import os

# If your handler runs inference on a model, load the model here.
# You will want models to be loaded into memory before starting serverless.
global model
model = "mdx_extra"
# Use another model and segment:
global separator
separator = demucs.api.Separator(model="mdx_extra", segment=12)

def log(message):
    """ Helper function to log messages. """
    print(f'[runpod-demucs-worker] {message}')

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
        log(f"Received job with URL: {url}, downloading...")
        input_file = download_url_to_tempfile(url)
        log(f"Downloaded file from {url} to {input_file}")
        # separate audio file
        log("Separating audio file...")
        origin, separated = separator.separate_audio_file(input_file)

        data = {
            "url": url,
            "files": []
        }

        # if there is a job_input['id'] then use that for the guid, otherwise generate one
        if 'id' in job_input:
            data["guid"] = job_input['id']
        else:
            import uuid
            data["guid"] = str(uuid.uuid4())

        # Remember to create the destination folder before calling `save_audio`
        # Or you are likely to recieve `FileNotFoundError`
        for stem in separated:
            source = separated[stem]
            log(f"Saving separated audio file {stem}...")
            demucs.api.save_audio(source, f"{stem}.mp3", samplerate=separator.samplerate)

            if os.environ.get("BUCKET_ENDPOINT_URL"):
                log(f"Uploading {stem}.mp3 to bucket...")
                url = rp_upload.upload_file_to_bucket(f"{data['guid']}.{stem}.mp3", f"{stem}.mp3")
                log(f"Uploaded {stem}.mp3 to {url}")
                data["files"].append({
                    "filename": f"{stem}.mp3",
                    "url": url
                })
            else:
                # Encode the file to base64 and add it to the files list {"filename": "file.mp3", "data": "base64encoded"}
                with open(f"{stem}.mp3", "rb") as f:
                    log(f"Encoding {stem}.mp3 to base64...")
                    data["files"].append({
                        "filename": f"{stem}.mp3",
                        "data": f.read().hex()
                    })

        # log the data as formatted json string
        log(f"Returning data: {data}")

        return data
    else:
        return {"error": "No URL provided."}


runpod.serverless.start({"handler": handler})
