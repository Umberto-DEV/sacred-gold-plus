#!/usr/bin/env python3
"""SGP-1.2-ANIM-A0-01 / M1 passo 1.

Estrae da una ROM NDS i moduli di codice (ARM9 + tutti gli overlay ARM9) in una
cartella di lavoro, con il loro indirizzo di caricamento in RAM, e stampa SOLO
metadati (id, indirizzo, lunghezza, sha256). Non stampa mai byte della ROM.

Uso: estrai_moduli.py <rom.nds> <cartella-uscita>
"""
import hashlib
import json
import sys
from pathlib import Path

import ndspy.rom
import ndspy.codeCompression


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    rom_path = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))

    moduli = []

    arm9 = rom.arm9
    # ndspy espone arm9 gia' scompattato se lo era; proviamo comunque il BLZ.
    try:
        dec = ndspy.codeCompression.decompress(arm9)
        if len(dec) > len(arm9):
            arm9 = dec
            compresso = True
        else:
            compresso = False
    except Exception:
        compresso = False
    (out / "arm9.bin").write_bytes(arm9)
    moduli.append({
        "modulo": "arm9",
        "id": -1,
        "ram": rom.arm9RamAddress,
        "len": len(arm9),
        "compresso_in_rom": compresso,
        "sha256": sha(arm9),
    })

    ovs = rom.loadArm9Overlays()
    for oid in sorted(ovs):
        ov = ovs[oid]
        data = ov.data
        (out / f"ov{oid:03d}.bin").write_bytes(data)
        moduli.append({
            "modulo": f"ov{oid:03d}",
            "id": oid,
            "ram": ov.ramAddress,
            "len": len(data),
            "bss": ov.bssSize,
            "compresso_in_rom": bool(ov.compressed),
            "sha256": sha(data),
        })

    (out / "moduli.json").write_text(json.dumps(moduli, indent=1))
    print(f"rom={rom_path.name} sha256={sha(rom_path.read_bytes())}")
    print(f"moduli={len(moduli)} (arm9 + {len(ovs)} overlay)")
    for m in moduli[:3]:
        print(" ", m["modulo"], hex(m["ram"]), m["len"], m["sha256"][:16])
    tot = sum(m["len"] for m in moduli)
    print(f"byte di codice totali={tot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
