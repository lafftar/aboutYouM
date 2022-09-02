import asyncio
import subprocess
import sys
from asyncio import sleep
from asyncio.subprocess import Process
from os import system

from colorama import Fore

from utils.custom_logger import Log
from utils.root import get_project_root
from utils.terminal import color_wrap


class TLSLauncher:
    tls_processes: list[Process] = []
    log = Log('[TLSLauncher]')

    @staticmethod
    async def start_port():
        if sys.platform == 'linux':
            proc = 'tlsapi'
        elif sys.platform == 'win32':
            proc = 'tls.exe'
        else:
            raise Exception("UnsupportedSystem - What the fuck are you running me on.")
        TLSLauncher.tls_processes.append(await asyncio.create_subprocess_exec(f'{get_project_root()}/.clients/{proc}',
                                                                              stdout=subprocess.PIPE))

    async def __aenter__(self):
        system('TASKKILL /F /IM tls.exe')
        await self.start_port()
        self.log.info(color_wrap(Fore.WHITE + 'Started.'))

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.tls_processes:
            for tls_proc in self.tls_processes:
                try:
                    tls_proc.kill()
                except ProcessLookupError:
                    continue
        self.log.info(color_wrap(Fore.WHITE + 'Ended.'))


async def test():
    async with TLSLauncher():
        await sleep(10)


if __name__ == "__main__":
    asyncio.run(test())
