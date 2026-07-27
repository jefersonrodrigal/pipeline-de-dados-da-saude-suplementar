"""Download HTTP com retry/backoff - usado pelos extratores da ANS/CNES."""

from __future__ import annotations

from pathlib import Path

import requests
from src.utils.logging_config import get_logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

_RETRYABLE_EXCEPTIONS = (requests.ConnectionError, requests.Timeout, requests.HTTPError)


class DownloadError(RuntimeError):
    """Erro irrecuperavel ao baixar um arquivo de origem publica."""


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
)
def download_to_file(url: str, destination: Path, timeout_seconds: int = 60) -> Path:
    """Baixa `url` para `destination`, criando diretorios intermediarios.

    Streaming em blocos para nao carregar arquivos grandes (ex.: SP ~130MB)
    inteiros em memoria. Levanta `DownloadError` para respostas HTTP de erro
    (404/5xx) apos esgotar as tentativas de retry.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Iniciando download", extra={"url": url, "destination": str(destination)})
    try:
        with requests.get(url, stream=True, timeout=timeout_seconds) as response:
            response.raise_for_status()
            tmp_path = destination.with_suffix(destination.suffix + ".part")
            with tmp_path.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        fh.write(chunk)
            tmp_path.replace(destination)
    except _RETRYABLE_EXCEPTIONS:
        raise
    except requests.RequestException as exc:  # pragma: no cover - defensivo
        raise DownloadError(f"Falha ao baixar {url}: {exc}") from exc

    logger.info(
        "Download concluido",
        extra={
            "url": url,
            "destination": str(destination),
            "size_bytes": destination.stat().st_size,
        },
    )
    return destination
