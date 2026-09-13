#!/usr/bin/env python3
"""SGP-1.2-ANIM-SOLIDO-01 — il banco Unicorn per la **v4**.

Estende `banco2.py` di `SGP-1.2-ANIM-B-01` (che resta invariato nel suo
pacchetto) senza riscriverlo: stessa RAM, stesso ARM9 e stesso `ov012` VERI
della base 1.1, stesso `Pokepic_SetAttr` vero, stesso task vanilla vero,
stessi frammenti di `PokepicManager_DrawAll` eseguiti per il disegno.

Tre cose sono nuove, e sono esattamente le tre differenze della v4:

1. **l'entrata non è più l'inizio del blocco.** Nel blob v4 la prima funzione
   è `sgp_pulisci`; il task sta a `sgp_idle_task2` e la trampolina a
   `sgp_idle_stop`. Gli indirizzi si leggono dal `manifesto.json`, non si
   indovinano.
2. **l'abilitazione viene dal chunk di D1**, non da `st->flags`. Il banco
   costruisce il blocco `SgpStato` a 0x023D8700 (guardia 0x5A a +4,
   `load_status` a +3, chunk a +0x10, `anim` a +0x16) e lo pilota con
   `accendi()`/`spegni()`.
3. **si può chiamare la trampolina** come la chiama il gioco: con `r4` =
   OpponentData e `r2` = 0, e si controlla che al ritorno `r0`/`r1`/`r2` siano
   quelli che le due istruzioni sostituite avrebbero lasciato.

GPL-3.0-or-later.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import banco2  # noqa: E402
from banco2 import (Banco2, OD0, OD1, PIC0, PIC1, TASK, SP0, RITORNO,  # noqa: F401,E402
                    PP_SIZE, PP_YOFFSET, PP_AFFINEW, PP_AFFINEH, PP_ANIMACTIVE,
                    PP_ANIMSTEP, PP_SHADOW_FLAGS, PP_SHADOW_YOFF, PP_SHADOW_Y,
                    PP_YCENTER, OD_POKEPIC, OD_TASK, OD_DEGREES,
                    SL_OD, SL_PIC, SL_USATO, SL_SIZE, ST_FLAGS, ST_GUARD)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,  # noqa: E402
                               UC_ARM_REG_R4, UC_ARM_REG_SP)

# Pianta del blocco `sgp.plus` di D1 (`sorgenti/sgp_chunk.h`, fonte unica).
STATO_PLUS = 0x023D8700
OFF_LOAD_STATUS = 0x03
OFF_GUARD = 0x04
OFF_CHUNK = 0x10
OFF_C_ANIM = 0x06
GUARD = 0x5A
LOAD_NONE, LOAD_ABSENT, LOAD_VALID, LOAD_REJECT = 0, 1, 2, 3

# offset nuovi dello stato v4 (dentro la coda riservata della fase 2b)
ST_STOP_VISTI, ST_PULITI = 0x20, 0x24


class Banco4(Banco2):
    """`Banco2` con il blob v4 e il chunk di D1."""

    def __init__(self, build, codice, tabelle, stato, slot, blob="blob.bin"):
        b = Path(build)
        # `Banco2` carica `blob2.bin` (il nome della fase 1b). Invece di
        # modificare `banco2.py`, che appartiene a un altro pacchetto, si
        # deposita accanto una copia con quel nome: un file, non una scorciatoia.
        if blob != "blob2.bin":
            (b / "blob2.bin").write_bytes((b / blob).read_bytes())
        super().__init__(build, codice, tabelle, stato, slot)
        self.man = json.loads((b / "manifesto.json").read_text())
        self.simboli = {k: int(v, 16) for k, v in self.man["simboli"].items()}
        self.entrata = self.simboli.get("sgp_idle_task2", codice | 1) & ~1
        self.trampolina = self.simboli.get("sgp_idle_stop")
        self.ha_pulizia = self.trampolina is not None
        if self.ha_pulizia:
            self.trampolina &= ~1
        self.prepara_chunk()

    # ---------------------------------------------------------- chunk di D1
    def prepara_chunk(self, guard=GUARD, load_status=LOAD_VALID, anim=0):
        s = bytearray(0x20)
        s[OFF_LOAD_STATUS] = load_status
        s[OFF_GUARD] = guard
        s[OFF_CHUNK + 0] = 0x47   # magic 'SG'
        s[OFF_CHUNK + 1] = 0x53
        s[OFF_CHUNK + 2] = 2      # versione
        s[OFF_CHUNK + OFF_C_ANIM] = anim
        self.wr(STATO_PLUS, s)

    def accendi(self, anim=1, guard=GUARD, load_status=LOAD_VALID):
        self.prepara_chunk(guard=guard, load_status=load_status, anim=anim)

    def spegni(self):
        self.prepara_chunk(anim=0)

    # ------------------------------------------------------------ esecuzione
    def nostro(self, od=OD0, **kw):
        """Il task, all'entrata dichiarata dal manifesto."""
        return self.chiama(self.entrata, r0=TASK, r1=od, **kw)

    def ferma(self, od=OD0, **kw):
        """La trampolina, chiamata come la chiama il gioco dalla coda di
        `ov12_02262014`: `r4` = OpponentData, `r2` = 0, `lr` = ritorno."""
        if not self.ha_pulizia:
            raise RuntimeError("questo blob non ha sgp_idle_stop (è la v3)")
        sp_prima = SP0
        r = self.chiama(self.trampolina, r4=od, r2=0, **kw)
        # `chiama` non rende r2 ne' r4, e conta r4 fra i "callee-saved
        # corrotti" perche' glielo abbiamo impostato noi: qui si legge la
        # verita' del contratto con il sito 0x02262032.
        r["r2"] = self.uc.reg_read(UC_ARM_REG_R2)
        r["r4"] = self.uc.reg_read(UC_ARM_REG_R4)
        r["sp_invariato"] = (self.uc.reg_read(UC_ARM_REG_SP) == sp_prima)
        r["callee_saved_corrotti"] = {k: v for k, v in
                                      r["callee_saved_corrotti"].items() if k != "r4"}
        return r

    def ferma_come_il_gioco(self, od=OD0, pic=PIC0):
        """Tutta la coda di `ov12_02262014`: la trampolina (se c'è) e poi la
        sola cosa che il gioco ripulisce da sé, `Pokepic_SetAttr(pic, 4, 0)`.
        Restituisce i registri al ritorno della trampolina, che sono il
        contratto con il sito."""
        r = None
        if self.ha_pulizia:
            r = self.ferma(od=od)
        self.chiama(banco2.SETATTR & ~1, r0=pic, r1=4, r2=0)
        return r

    # --------------------------------------------------------------- letture
    def stato_u32(self, off):
        return self.u32(self.stato + off)

    def voci_occupate(self):
        return [i for i in range(4) if self.u32(self.slot + i * SL_SIZE + SL_OD)]
