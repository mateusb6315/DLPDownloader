"""Restrições de dependência e ciclos entre módulos internos."""

import ast
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

    def visitar(modulo, caminho):
        assert modulo not in caminho, f"Ciclo: {caminho} -> {modulo}"
        for dependencia in grafo.get(modulo, []):
            visitar(dependencia, caminho | {modulo})

    for modulo in grafo:
        visitar(modulo, set())
