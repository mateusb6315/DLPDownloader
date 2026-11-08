"""Comandos Git/GitHub explícitos, sem force-push ou resolução automática de conflitos."""

import argparse
import subprocess
from pathlib import Path


class GitWorkflow:
    """Executa cada ação no repositório confirmado e interrompe em qualquer erro."""

    def __init__(self, raiz: Path, executar=subprocess.run):
        self.raiz = raiz.resolve()
        self.executar = executar

    def comando(self, *args: str, capturar: bool = False) -> str:
        """Executa argumentos sem shell e preserva o código de falha."""
        resultado = self.executar(
            list(args),
            cwd=self.raiz,
            check=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=capturar,
        )
        return resultado.stdout.strip() if capturar else ""

    def git(self, *args: str, capturar: bool = False) -> str:
        """Invoca Git dentro da raiz do projeto."""
        return self.comando("git", *args, capturar=capturar)

    def exigir_limpa(self) -> None:
        """Recusa operações estruturais com alterações locais pendentes."""
        if self.git("status", "--porcelain", capturar=True):
            raise ValueError("Há alterações pendentes. Faça commit ou trate-as antes.")

    def remoto(self) -> str:
        """Escolhe o único remoto ou usa o remoto do upstream configurado."""
        branch = self.git("branch", "--show-current", capturar=True)
        remotos = self.git("remote", capturar=True).splitlines()
        if len(remotos) == 1:
            return remotos[0]
        configurado = self.git("config", "--get", f"branch.{branch}.remote", capturar=True)
        if configurado not in remotos:
            raise ValueError("Configure um remoto de upstream para esta branch.")
        return configurado

    def executar_acao(self, args) -> None:
        """Despacha somente a ação solicitada, sem publicar como efeito de commit."""
        topo = Path(self.git("rev-parse", "--show-toplevel", capturar=True)).resolve()
        if topo != self.raiz:
            raise ValueError("O script deve operar na raiz deste repositório.")
        acao = args.acao
        if acao == "status":
            self.git("status", "--short", "--branch")
        elif acao == "iniciar":
            self.exigir_limpa()
            self.git("switch", "-c", f"codex/{args.nome}")
        elif acao == "sincronizar":
            self.exigir_limpa()
            self.git("fetch", self.remoto())
            self.git("merge", "--ff-only", "@{upstream}")
        elif acao == "commit":
            self._commit(args)
        elif acao == "publicar":
            branch = self.git("branch", "--show-current", capturar=True)
            if not branch:
                raise ValueError("Selecione uma branch antes de publicar.")
            self.git("push", "-u", self.remoto(), f"{branch}:refs/heads/{branch}")
        elif acao == "pr":
            self.comando(
                "gh",
                "pr",
                "create",
                "--title",
                args.titulo,
                "--body-file",
                str(args.descricao.resolve()),
            )
        elif acao == "merge-local":
            self.exigir_limpa()
            self.git("merge", "--no-edit", args.origem)
        elif acao == "merge-pr":
            self.exigir_limpa()
            self.comando("gh", "pr", "merge", str(args.numero), "--merge")

    def _commit(self, args) -> None:
        if self.git("diff", "--cached", "--name-only", capturar=True):
            raise ValueError("Já há arquivos no stage. Revise-os antes de usar este comando.")
        for nome in args.arquivos:
            arquivo = (self.raiz / nome).resolve()
            if not arquivo.is_relative_to(self.raiz) or arquivo == self.raiz or arquivo.is_dir():
                raise ValueError("Indique arquivos individuais dentro do repositório.")
            if nome.startswith(":"):
                raise ValueError("Pathspecs especiais não são aceitos.")
        self.git("--literal-pathspecs", "add", "--", *args.arquivos)
        self.git("commit", "-m", args.mensagem)


def criar_parser() -> argparse.ArgumentParser:
    """Define a CLI pública da ferramenta."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="acao", required=True)
    sub.add_parser("status")
    iniciar = sub.add_parser("iniciar")
    iniciar.add_argument("nome")
    sub.add_parser("sincronizar")
    commit = sub.add_parser("commit")
    commit.add_argument("-m", "--mensagem", required=True)
    commit.add_argument("--arquivos", nargs="+", required=True)
    sub.add_parser("publicar")
    pr = sub.add_parser("pr")
    pr.add_argument("--titulo", required=True)
    pr.add_argument("--descricao", type=Path, required=True)
    merge = sub.add_parser("merge-local")
    merge.add_argument("--origem", required=True)
    merge_pr = sub.add_parser("merge-pr")
    merge_pr.add_argument("numero", type=int)
    return parser


def main() -> int:
    """Executa ação autorizada pela invocação explícita do subcomando."""
    args = criar_parser().parse_args()
    try:
        GitWorkflow(Path(__file__).resolve().parents[1]).executar_acao(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as erro:
        print(f"ERRO: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
