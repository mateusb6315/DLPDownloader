"""Job Object Windows: libera descendentes mesmo quando o processo pai já morreu."""

import ctypes
from ctypes import wintypes


class LimitesBasicos(ctypes.Structure):
    """Layout nativo JOBOBJECT_BASIC_LIMIT_INFORMATION."""

    _fields_ = [
        ("tempo_processo", ctypes.c_longlong),
        ("tempo_job", ctypes.c_longlong),
        ("flags", wintypes.DWORD),
        ("memoria_minima", ctypes.c_size_t),
        ("memoria_maxima", ctypes.c_size_t),
        ("processos_ativos", wintypes.DWORD),
        ("afinidade", ctypes.c_size_t),
        ("prioridade", wintypes.DWORD),
        ("agendamento", wintypes.DWORD),
    ]


class ContadoresIO(ctypes.Structure):
    """Layout nativo IO_COUNTERS."""

    _fields_ = [
        (nome, ctypes.c_ulonglong)
        for nome in (
            "leituras",
            "escritas",
            "outros",
            "bytes_lidos",
            "bytes_escritos",
            "bytes_outros",
        )
    ]


class LimitesEstendidos(ctypes.Structure):
    """Layout nativo JOBOBJECT_EXTENDED_LIMIT_INFORMATION."""

    _fields_ = [
        ("basicos", LimitesBasicos),
        ("io", ContadoresIO),
        ("memoria_processo", ctypes.c_size_t),
        ("memoria_job", ctypes.c_size_t),
        ("pico_processo", ctypes.c_size_t),
        ("pico_job", ctypes.c_size_t),
    ]


class ArvoreWindows:
    """Associa um processo recém-criado a um job com KILL_ON_JOB_CLOSE."""

    def __init__(self, processo):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        self.kernel.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limites = LimitesEstendidos()
        limites.basicos.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        configurou = self.kernel.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limites), ctypes.sizeof(limites)
        )
        associou = configurou and self.kernel.AssignProcessToJobObject(
            self.handle, int(processo._handle)
        )
        if not associou:
            erro = ctypes.WinError(ctypes.get_last_error())
            self.fechar()
            raise erro

    def fechar(self) -> None:
        """Fecha uma vez; o Windows encerra todos os processos ainda associados."""
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
