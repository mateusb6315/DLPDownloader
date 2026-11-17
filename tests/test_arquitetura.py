"""Restrições de dependência e ciclos entre módulos internos."""

import ast
from importlib.util import resolve_name
from pathlib import Path


def test_imports_respeitam_mvc_e_nao_possuem_ciclos():
    raiz = Path(__file__).resolve().parents[1] / "src/dlpdownloader"
    grafo = {}
    for arquivo in raiz.rglob("*.py"):
        modulo = "dlpdownloader." + ".".join(arquivo.relative_to(raiz).with_suffix("").parts)
        imports = []
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.ImportFrom) and no.module:
                imports.append(no.module)
            elif isinstance(no, ast.Import):
                imports.extend(alias.name for alias in no.names)
        camada = arquivo.relative_to(raiz).parts[0]
        if camada in {"modelos", "servicos", "config"}:
            assert not any(i.startswith("PyQt6") for i in imports), arquivo
        if camada == "visoes":
            assert not any(
                i.startswith(f"dlpdownloader.{c}")
                for i in imports
                for c in ("modelos", "servicos", "controladores")
            ), arquivo
        grafo[modulo] = [i for i in imports if i.startswith("dlpdownloader.")]

    _verificar_ciclos(grafo)


def _verificar_ciclos(grafo):
    def visitar(modulo, caminho):
        assert modulo not in caminho, f"Ciclo: {caminho} -> {modulo}"
        for dependencia in grafo.get(modulo, []):
            visitar(dependencia, caminho | {modulo})

    for modulo in grafo:
        visitar(modulo, set())


def test_arquitetura_raiz_independe_do_legado_e_respeita_mvc():
    raiz = Path(__file__).resolve().parents[1]
    arquivos = {
        ".".join(arquivo.relative_to(raiz).with_suffix("").parts).removesuffix(".__init__"): arquivo
        for pasta in ("ui", "config", "services")
        for arquivo in (raiz / pasta).rglob("*.py")
    }
    assert {"ui.window", "config.bootstrap", "config.controller", "services.downloader"} <= (
        arquivos.keys()
    )
    grafo = {}
    for modulo, arquivo in arquivos.items():
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
                imports.update(alvo for a in no.names if (alvo := f"{origem}.{a.name}") in arquivos)
        grupos = {i.split(".")[0] for i in imports}
        assert "dlpdownloader" not in grupos, arquivo
        if modulo.startswith("ui."):
            assert not grupos & {"config", "services"}, arquivo
        if modulo.startswith("services.") or modulo in {"config.paths", "config.preferences"}:
            assert not grupos & {"PyQt6", "ui"}, arquivo
        if modulo == "config.controller":
            assert not any(
                i.startswith(("services._infra", "services.downloader")) for i in imports
            )
        grafo[modulo] = imports & arquivos.keys()

    _verificar_ciclos(grafo)
