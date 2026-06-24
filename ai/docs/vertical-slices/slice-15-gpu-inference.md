# Slice 15 — GPU-Enabled Faster Whisper Inference

> Source: `vertical-slice-implementation-plan.md` Slice 15

## Goal

Let the worker use an NVIDIA GPU for Faster Whisper inference via Docker
Compose, for faster transcription than CPU-only inference.

## Scope

This slice only changes Docker/dependency configuration and documentation.
No application code changes — `app/settings.py`'s `faster_whisper_device`
and `faster_whisper_compute_type` and `FasterWhisperTranscriber` already
forward these values untouched to `WhisperModel(...)`. See
[Settings Architecture](../architecture/13-settings-architecture.md) and
[Transcriber Architecture](../architecture/11-transcriber-architecture.md).

## Tasks

Host prerequisites (document, not automated by this repo):

1. Install the NVIDIA GPU driver on the host; verify with `nvidia-smi` on
   the host.
2. Install the NVIDIA Container Toolkit:
   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
   ```bash
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```
3. Verify before touching this repo's compose file:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
   ```

Add `gpu` optional dependency group to `pyproject.toml`:

```toml
[project.optional-dependencies]
gpu = [
    "nvidia-cublas-cu12",
    "nvidia-cudnn-cu12==9.*",
]
```

Update `Dockerfile`:

- Install the extra: `uv sync --frozen --no-dev --extra gpu`
- Set `LD_LIBRARY_PATH` to the nvidia cublas/cudnn lib dirs so
  `ctranslate2` finds them at runtime:
  ```dockerfile
  ENV LD_LIBRARY_PATH="/opt/venv/lib/python3.13/site-packages/nvidia/cublas/lib:/opt/venv/lib/python3.13/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH}"
  ```
- Base image stays `python:3.13-slim` — no CUDA base image swap. (Fallback
  if this proves unreliable: switch to an `nvidia/cuda:*-cudnn-runtime`
  base image instead.)

Update `docker-compose.yml` — reserve a GPU for the `worker` service only.
See [Docker Architecture §20.11](../architecture/18-docker-architecture.md#2011-gpu-support):

```yaml
worker:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Update `.env.example` — make GPU values the active Docker defaults, CPU
the commented fallback. See
[Configuration Requirements](../functional/17-configuration-requirements.md):

```env
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16

# CPU fallback (host without an NVIDIA GPU / Container Toolkit):
# FASTER_WHISPER_DEVICE=cpu
# FASTER_WHISPER_COMPUTE_TYPE=int8
```

Update `README.md` with a "GPU Host Setup" section (driver, Container
Toolkit, verification command) and a "GPU not detected" troubleshooting
entry.

## Tests

Add `tests/integration/test_faster_whisper_transcriber_gpu.py`: marked
`@pytest.mark.integration` and additionally `skipif` when
`ctranslate2.get_cuda_device_count() == 0`, so it's inert on CPU-only
machines and runs for real on a GPU host. Instantiates
`FasterWhisperTranscriber(model_size='tiny', device='cuda',
compute_type='float16')` and asserts a real transcription succeeds.

Manual verification on a GPU host:

```bash
docker compose up --build
```

1. Worker logs show `device=cuda, compute_type=float16` at the
   "Loading Faster Whisper model" line.
2. `docker exec <worker_container> nvidia-smi` shows the GPU.
3. Upload a sample audio file; job completes; compare wall-clock time
   against a CPU run.
4. `uv run pytest -m integration` picks up and passes the new GPU test on
   the GPU host; reports it skipped on a CPU-only machine.

## Acceptance Criteria

This slice is complete when:

1. `docker compose up --build` starts the worker with GPU access on a host
   with the NVIDIA Container Toolkit configured.
2. Worker startup logs show `device=cuda`.
3. `nvidia-smi` works inside the running worker container.
4. The system still runs correctly on a CPU-only host by switching
   `FASTER_WHISPER_DEVICE`/`FASTER_WHISPER_COMPUTE_TYPE` to `cpu`/`int8`.
5. The GPU integration test is skipped (not failed) on CPU-only machines
   and passes on a GPU host.
6. README documents host GPU setup end-to-end.
