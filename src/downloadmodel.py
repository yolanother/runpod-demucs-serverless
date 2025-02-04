
import runpod
import demucs.api

# If your handler runs inference on a model, load the model here.
# You will want models to be loaded into memory before starting serverless.
global model
model = "mdx_extra"
# Use another model and segment:
global separator
separator = demucs.api.Separator(model="mdx_extra", segment=12)