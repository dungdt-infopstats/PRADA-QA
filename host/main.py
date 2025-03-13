import modal
import yaml

def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}


vllm_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm==0.7.3",
        "huggingface_hub[hf_transfer]==0.26.2",
        "flashinfer-python==0.2.0.post2",  # pinning, very unstable
        extra_index_url="https://flashinfer.ai/whl/cu124/torch2.5",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})  # faster model transfers
)

# vllm_image = vllm_image.env({"VLLM_USE_V1": "1"})

hf_cache_vol = modal.Volume.from_name(
    "huggingface-cache", create_if_missing=True
)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)


app = modal.App("example-vllm-openai-compatible-1")

N_GPU = 1  # tip: for best results, first upgrade to more powerful GPUs, and only then increase GPU count
API_KEY = "super-secret-key"  # api key, for auth. for production use, replace with a modal.Secret

MINUTES = 60  # seconds

VLLM_PORT = 8000

#specifying model
    # MODELS_DIR = "/llamas"
    
    # MODEL_REVISION = config['model_revision']
MODEL_NAME = "Groq/Llama-3-Groq-8B-Tool-Use"

@app.function(
    image=vllm_image,
    gpu=f"H100:{N_GPU}",
    # how many requests can one replica handle? tune carefully!
    allow_concurrent_inputs=1000,
    # how long should we stay up with no requests?
    # scaledown_window=15 * MINUTES,
    container_idle_timeout = 1200,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.web_server(port=VLLM_PORT, startup_timeout=5 * MINUTES)
def serve():
    import subprocess
    from huggingface_hub import login
    token_hf = "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"
    login(token_hf)
    cmd = [
        "vllm",
        "serve",
        "--uvicorn-log-level=info",
        MODEL_NAME,
        # "--revision",
        # MODEL_REVISION,
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--api-key",
        API_KEY,
        "--trust-remote-code",
        "--disable-sliding-window"
    ]

    subprocess.Popen(" ".join(cmd), shell=True)