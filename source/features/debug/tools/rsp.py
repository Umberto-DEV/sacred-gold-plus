#!/usr/bin/env python3
"""Client GDB Remote Serial Protocol minimo per il gdbstub di melonDS 906e9ebb.

Sola libreria standard (socket). Serve a pilotare `hg_runtime-gdb --gdb-port N`.

Dettagli del dialetto implementato dal core 906e9ebb (letti in src/debug/GdbProto.cpp e
GdbStub.cpp, non supposti):
  * alla connessione il server fa `WaitAckBlocking` e si aspetta un '+' dal client, poi
    risponde con un '+' proprio (`SendAck`);
  * il server NON manda '+' in risposta ai pacchetti del client (la SendAck nel ramo
    CmdRecvd di GdbStub::Poll e' commentata nel sorgente);
  * il server manda `$...#cs` e ASPETTA il nostro '+' (GdbStub::Resp, 3 tentativi, 2 s
    di attesa ciascuno): il client deve quindi ackare ogni risposta, altrimenti il core
    si blocca due secondi per pacchetto;
  * a ogni evento di fermata il server manda spontaneamente la risposta di `?`
    (GdbStub::Poll: `if (StatFlag) Handle_Question(...)`), cioe' `S05`.

GPL-3.0-or-later, come il resto del kit del banco.
"""
import socket
import time

REG_NAMES = [f"r{i}" for i in range(13)] + ["sp", "lr", "pc", "cpsr"]


class RspError(RuntimeError):
    pass


class Rsp:
    def __init__(self, host="127.0.0.1", port=3333, timeout=30.0, retries=400,
                 tentativi_handshake=5):
        """Il banco apre il socket nel costruttore di NDS ma accetta solo al primo confine
        di fotogramma: fra il connect del kernel e la prima accept possono passare secondi,
        e se qualcosa va storto in quella finestra il server chiude. Percio' l'intero
        handshake, non solo il connect, viene ritentato."""
        ultimo = None
        for _ in range(tentativi_handshake):
            try:
                self._apri(host, port, timeout, retries)
                self._senza_ack()                     # toglie di mezzo il ballo degli ack
                self.why()                            # prova viva: il server risponde?
                return
            except (OSError, RspError) as e:
                ultimo = e
                try:
                    self.s.close()
                except Exception:
                    pass
                time.sleep(0.5)
        raise RspError(f"handshake fallito su {host}:{port}: {ultimo}")

    def _apri(self, host, port, timeout, retries):
        last = None
        for _ in range(retries):
            try:
                self.s = socket.create_connection((host, port), timeout=1.0)
                break
            except OSError as e:                      # il banco non ha ancora fatto bind
                last = e
                time.sleep(0.05)
        else:
            raise RspError(f"nessuna connessione a {host}:{port}: {last}")
        self.s.settimeout(timeout)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buf = b""
        self.noack = False
        self._alt = False
        self.s.sendall(b"+")                          # handshake atteso dal server
        self._expect_ack()

    def _senza_ack(self):
        """QStartNoAckMode. Nel core 906e9ebb il lettore del server e' doppio: `Resp` legge
        l ack con una recv(1) diretta (GdbProto.cpp:248-295) mentre i comandi passano da
        `MsgRecv`/`TryParsePacket`, che accumula in un buffer proprio. Con le due letture in
        gara su uno stream full-duplex la sincronia si perde ogni tanto, e il sintomo e'
        esattamente quello visto: `Received unknown character 6` seguito da WUT/EOF. In modo
        senza-ack nessuna delle due parti manda o aspetta piu ack e la gara sparisce.
        `Handle_Q_StartNoAckMode` (GdbCmds.cpp:921) imposta NoAck PRIMA di rispondere, quindi
        la risposta a questo stesso comando non va ackata."""
        self.send("QStartNoAckMode")
        self.noack = True
        r = self.read_packet()
        if r != "OK":
            self.noack = False
            raise RspError(f"QStartNoAckMode -> {r!r}")

    # --- livello di trasporto -------------------------------------------------
    def _recv(self, n=4096):
        d = self.s.recv(n)
        if not d:
            raise RspError("connessione chiusa dal banco")
        self.buf += d

    def _expect_ack(self):
        while not self.buf:
            self._recv()
        c, self.buf = self.buf[0:1], self.buf[1:]
        if c != b"+":
            raise RspError(f"atteso '+', ricevuto {c!r}")

    def hx(self, v: int) -> str:
        """Esadecimale con la cassa ALTERNATA a ogni chiamata.

        Non e cosmesi: `GdbStub::ParseAndSetupPacket` (GdbProto.cpp) tratta due pacchetti
        IDENTICI consecutivi nel proprio buffer come un rinvio dello stesso comando e ne
        risponde UNO SOLO. Due letture di seguito dello stesso indirizzo sono byte per byte
        identiche: se finiscono insieme nel buffer del server, una risposta sparisce e il
        flusso si sfasa di un pacchetto (sintomo osservato: la risposta a `m` che arriva
        come `S05`). Alternando la cassa dell esadecimale due pacchetti consecutivi non
        sono mai identici e la deduplicazione non puo scattare.
        """
        self._alt = not self._alt
        return f"{v:X}" if self._alt else f"{v:x}"

    @staticmethod
    def _cksum(data: bytes) -> int:
        return sum(data) & 0xFF

    traccia = None      # se impostato a un file aperto, registra ogni pacchetto

    def _tr(self, verso, testo):
        if Rsp.traccia:
            Rsp.traccia.write(f"{verso} {testo}\n")
            Rsp.traccia.flush()

    def send(self, cmd: str):
        self._tr(">", cmd)
        d = cmd.encode()
        self.s.sendall(b"$" + d + b"#" + f"{self._cksum(d):02x}".encode())

    def read_packet(self) -> str:
        """Legge un pacchetto `$...#cs`, lo acka e ne rende il contenuto."""
        while True:
            i = self.buf.find(b"$")
            if i >= 0:
                j = self.buf.find(b"#", i)
                if j >= 0 and len(self.buf) >= j + 3:
                    body = self.buf[i + 1:j]
                    got = int(self.buf[j + 1:j + 3], 16)
                    self.buf = self.buf[j + 3:]
                    if got != self._cksum(body):
                        self.s.sendall(b"-")
                        raise RspError("checksum sbagliato dal banco")
                    if not self.noack:
                        self.s.sendall(b"+")          # il server aspetta questo ack
                    r = body.decode(errors="replace")
                    self._tr("<", r)
                    return r
            self._recv()

    def cmd(self, c: str) -> str:
        self.send(c)
        return self.read_packet()

    # --- comandi ---------------------------------------------------------------
    def why(self) -> str:
        return self.cmd("?")

    def regs(self):
        """`g`: 17 parole little-endian (r0..r12, sp, lr, pc, cpsr)."""
        h = self.cmd("g")
        vals = [int.from_bytes(bytes.fromhex(h[i:i + 8]), "little")
                for i in range(0, len(h) - 7, 8)]
        return dict(zip(REG_NAMES, vals))

    def reg(self, n: int) -> int:
        h = self.cmd("p" + self.hx(n).rjust(2, "0"))
        if h.startswith("E"):
            raise RspError(f"p{n:02x} -> {h}")
        return int.from_bytes(bytes.fromhex(h), "little")

    def set_reg(self, n: int, value: int):
        """`P<n>=<valore>`: n secondo GdbArch (0..12 = r0..r12, 13 = sp, 14 = lr,
        15 = pc — scriverlo fa un JumpTo, quindi il bit 0 sceglie ARM/Thumb — 16 = cpsr)."""
        r = self.cmd("P" + self.hx(n).rjust(2, "0") + "=" + value.to_bytes(4, "little").hex())
        if r != "OK":
            raise RspError(f"P{n:02x} -> {r!r}")

    def mem(self, addr: int, length: int) -> bytes:
        h = self.cmd(f"m{self.hx(addr)},{length:x}")
        try:
            return bytes.fromhex(h)
        except ValueError:
            raise RspError(f"m{addr:x},{length:x} -> risposta non esadecimale {h!r}")

    def u32(self, addr: int) -> int:
        return int.from_bytes(self.mem(addr, 4), "little")

    def write_mem(self, addr: int, data: bytes):
        r = self.cmd(f"M{self.hx(addr)},{len(data):x}:{data.hex()}")
        if r != "OK":
            raise RspError(f"M -> {r}")

    def add_bkpt(self, addr: int, kind: int = 4):
        r = self.cmd(f"Z1,{self.hx(addr)},{kind}")
        if r != "OK":
            raise RspError(f"Z1 -> {r!r}")

    def del_bkpt(self, addr: int, kind: int = 4):
        self.cmd(f"z1,{self.hx(addr)},{kind}")

    def add_watch_write(self, addr: int, length: int = 4):
        """Z2 = watchpoint di scrittura. ATTENZIONE: nel core 906e9ebb il pacchetto
        riempie WpList ma nessuno la consulta; serve l'aggancio in ARMv5::DataWrite*
        aggiunto da questo pacchetto (kit-gdb/watchpoint-hook.patch)."""
        r = self.cmd(f"Z2,{self.hx(addr)},{length}")
        if r != "OK":
            raise RspError(f"Z2 -> {r!r}")

    def del_watch_write(self, addr: int, length: int = 4):
        self.cmd(f"z2,{self.hx(addr)},{length}")

    def cont(self, attesa=None) -> str:
        """`c`: il server non risponde subito; alla prossima fermata manda `S05`.

        `attesa` e' il timeout in secondi per l'attesa della fermata: None = nessun
        limite. Serve un timeout diverso da quello dei comandi perche' fra un `c` e la
        fermata successiva possono passare minuti di emulazione."""
        vecchio = self.s.gettimeout()
        self.s.settimeout(attesa)
        try:
            self.send("c")
            return self.read_packet()
        finally:
            self.s.settimeout(vecchio)

    def attendi_fermata(self, attesa=None) -> str:
        """Aspetta la prossima fermata SENZA mandare `c`: si usa quando il bersaglio sta
        gia' correndo (un `c` mandato a un bersaglio che corre non serve a niente e nel
        core 906e9ebb lascia il flusso in uno stato che ha prodotto fermate doppie)."""
        vecchio = self.s.gettimeout()
        self.s.settimeout(attesa)
        try:
            return self.read_packet()
        finally:
            self.s.settimeout(vecchio)

    def cont_nowait(self):
        self.send("c")

    def step(self) -> str:
        self.send("s")
        return self.read_packet()

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass
