"""Limites do MVC e dependências entre módulos da aplicação."""

import ast
from importlib.util import resolve_name
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CAMADAS = {"config", "ui", "services"}


def _imports(arquivo, modulo, conhecidos):
    imports = set()
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            imports.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom):
            origem = no.module or ""
            if no.level:
                pacote = modulo if arquivo.stem == "__init__" else modulo.rpartition(".")[0]
                origem = resolve_name("." * no.level + origem, pacote)
            imports.add(origem)
            imports.update(alvo for a in no.names if (alvo := f"{origem}.{a.name}") in conhecidos)
    return imports


def _verificar_ciclos(grafo):
    visitados = set()

    def visitar(modulo, caminho):
        assert modulo not in caminho, f"Ciclo: {' -> '.join((*caminho, modulo))}"
        if modulo in visitados:
            return
        for dependencia in grafo[modulo]:
            visitar(dependencia, (*caminho, modulo))
        visitados.add(modulo)

    for modulo in grafo:
        visitar(modulo, ())


def test_imports_respeitam_mvc_e_nao_possuem_ciclos():
    arquivos = {
        ".".join(arquivo.relative_to(RAIZ).with_suffix("").parts).removesuffix(".__init__"): arquivo
        for pasta in CAMADAS
        for arquivo in (RAIZ / pasta).rglob("*.py")
    }
    entradas = {"main", "dlpdownloader"}
    arquivos.update({nome: RAIZ / f"{nome}.py" for nome in entradas})
    assert {
        "ui.window",
        "config.bootstrap",
        "config.controller",
        "services.downloader",
        "services.yt_dlp",
        "services.ffmpeg",
        "services.repair",
        "services.repair_console",
    } <= arquivos.keys()

    grafo = {}
    for modulo, arquivo in arquivos.items():
        imports = _imports(arquivo, modulo, arquivos.keys())
        camada = modulo.split(".")[0]
        grupos = {i.split(".")[0] for i in imports}
        assert not grupos & entradas, arquivo
        if camada == "ui":
            assert not grupos & {"config", "services"}, arquivo
        if camada == "services":
            assert not grupos & {"PyQt6", "ui"}, arquivo
            configuracao = {i for i in imports if i.partition(".")[0] == "config"}
            permitidos = {"config.paths"} if modulo == "services.repair_console" else set()
            assert configuracao <= permitidos, arquivo
        if modulo in {"config", "config.paths"}:
            assert not grupos & (CAMADAS | {"PyQt6"}), arquivo
        if modulo.startswith("services._models"):
            assert all(i.startswith("services._models") for i in imports & arquivos.keys()), arquivo
        if modulo in {"config.paths", "config.preferences"}:
            assert not grupos & {"PyQt6", "ui"}, arquivo
        if modulo in {"config.controller", "config.update_tasks", "config.worker"}:
            assert all(
                i.startswith("services._models") for i in imports if i.startswith("services")
            ), arquivo
        if modulo == "services.yt_dlp":
            assert not imports & {"services.ffmpeg", "services.downloader"}, arquivo
        if modulo == "services.ffmpeg":
            assert not imports & {"services.yt_dlp", "services.downloader"}, arquivo
        grafo[modulo] = imports & arquivos.keys()

    for entrada in entradas:
        assert grafo[entrada] == {"config.bootstrap"}
    assert {"services.ffmpeg", "services.yt_dlp"} <= grafo["services.downloader"]
    _verificar_ciclos(grafo)
