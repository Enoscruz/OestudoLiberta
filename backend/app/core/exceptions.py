"""Exceções de domínio e conversão para respostas HTTP.

Permite que as camadas de serviço sinalizem erros de negócio sem conhecer
detalhes de HTTP. Os handlers registrados em ``main.py`` traduzem cada exceção
para o status correspondente.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Erro de negócio que se converte em uma resposta HTTP previsível."""

    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class ForbiddenError(DomainError):
    """Ação não permitida para o estado/perfil atual."""

    status_code = 403


class NotFoundError(DomainError):
    """Recurso inexistente."""

    status_code = 404


class ConflictError(DomainError):
    """Conflito com o estado atual (duplicidade, dependência, etc.)."""

    status_code = 409


class BusinessRuleError(DomainError):
    """Entrada bem formada, mas que viola uma regra de negócio."""

    status_code = 422


class UpstreamError(DomainError):
    """Falha em um serviço externo."""

    status_code = 502


class ServiceUnavailableError(DomainError):
    """Serviço externo não configurado ou indisponível."""

    status_code = 503


def register_exception_handlers(app: FastAPI) -> None:
    """Registra a tradução de ``DomainError`` para respostas JSON."""

    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
