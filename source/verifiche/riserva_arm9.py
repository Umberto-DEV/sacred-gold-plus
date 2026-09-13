#!/usr/bin/env python3
"""Legge il layout della riserva ARM9 di una candidata e dice quanto e' LIBERO.

Serve perche' la riserva e' contesa: piu' lavori indipendenti ci scrivono dentro,
ognuno progettato sulla stessa base, e "2080 byte" non vuol dire "2080 disponibili".
L'11/09/2026 la riserva della candidata risultava da 2080 byte con soli 140 liberi
in coda, mentre tre lavori pronti ne chiedevano 2280 in piu'.

CORREZIONE DEL 12/09/2026 (rimedio P2 di STATO-1.2.md (ex 01-AUDIT-1.1.md), dettagliata in
STATO-1.2.md §b (ex 04-RISERVA-ARM9-F0.md §5) e §7): il vecchio `--stato 140` era CABLATO su un layout che
non esiste piu' (124 B di stato borsa + 16 di coda, ARENA-INNESTO-01). Misurato sulla
riserva 1.1 finale, il numero giusto per quel layout e' 32 B (20 del "buco" fra
`.bss` borsa e stato camera + 12 di padding), non 140: `max(0, 3 - 140) = 0` mentiva
per la ragione sbagliata due volte (vedi il documento). Lo strumento ora preferisce
leggere un MANIFEST (`source/docs/arm9-reserve-map.json` o compatibile) che
elenca i blocchi dichiarati: il libero vero e' la somma dei blocchi `tipo: "libero"`
che risultano DAVVERO a zero nella ROM, non un numero cablato. Senza `--manifest`,
lo strumento stampa la coda azzerata e AVVISA che senza manifest non puo' dire quanto
e' davvero libero (invece di stampare uno zero che sembra un verdetto).

REVISIONE 02 (12/09/2026, C16/C17 di SGP-1.2-RISERVA-01, revisione privata): il libero
"vero" sommava anche blocchi 'libero' dichiarati NON assegnabili dal manifest stesso
(es. il "buco" di zona 1.1, 20 B, che il manifest marca intoccabile): 27 412 invece di
27 392. Ora distingue LIBERO ASSEGNABILE da libero-ma-non-assegnabile, ed esce con
codice 4 (non piu' 0) quando un blocco del manifest cade FUORI DALLA SEZIONE.

Distingue tre cose che vengono confuse:
  - la DIMENSIONE della sezione;
  - l'OCCUPATO, cioe' fin dove arrivano i byte non nulli;
  - il LIBERO vero, che i blocchi `tipo: "libero"` del manifest che sono
    effettivamente a zero nella ROM (non una coda azzerata meno una costante).

Uso:  python3 riserva_arm9.py <rom.nds> [--manifest MAPPA-RISERVA-ARM9.json]
                                          [--stato N]
      --manifest FILE: legge i blocchi dichiarati e calcola il libero vero da li'
        (uso raccomandato dal 12/09/2026 in poi).
      --stato N: uso LEGACY, solo se non si passa --manifest: byte di stato a riposo
        da NON contare come liberi. NON ha piu' un default cablato: se ne omesso e
        non si passa --manifest, lo strumento stampa la coda azzerata e dichiara
        esplicitamente che il libero vero e' SCONOSCIUTO senza manifest.
"""
import json
import struct
import sys

RISERVA_ATTESA = None  # trovata da sola: la sezione autoload in MAINEX (0x023xxxxx)
MAINEX_LO, MAINEX_HI = 0x02380000, 0x02400000


def sezioni(percorso):
    with open(percorso, "rb") as fh:
        testa = fh.read(0x200)
        rom_off, _entry, ram, size = struct.unpack_from("<IIII", testa, 0x20)
        fh.seek(rom_off)
        blob = fh.read(size)
    import ndspy.code
    return ndspy.code.MainCodeFile(blob, ram).sections, rom_off, ram, size


def libero_da_manifest(b, base_sezione, manifest_path):
    """Somma i blocchi tipo 'libero' E 'assegnabile' (default True) del manifest che
    risultano DAVVERO a zero nella ROM. Ogni altro blocco (guardia/dati/codice/stato/
    padding/riservato, o un 'libero' con assegnabile:false) NON e' disponibile, anche se
    e' a zero a riposo: e' il punto che il vecchio '--stato N' cablato non poteva
    cogliere, e che la vecchia versione di QUESTA funzione sbagliava ancora (REVISIONE
    02, C16/D9 della revisione privata: sommava anche il 'buco' di zona 1.1, dando 27 412
    invece di 27 392 — un blocco 'libero' ma dichiarato intoccabile dal manifest
    stesso). Ritorna anche il FUORI_SEZIONE trovato, cosi' il chiamante puo' segnalarlo.

    Torna: (libero_assegnabile, libero_non_assegnabile, righe, per_tipo, fuori_sezione)."""
    m = json.loads(open(manifest_path).read())
    blocchi = sorted(m["blocchi"], key=lambda x: int(x["base"], 16))
    righe = []
    libero_assegnabile = 0
    libero_non_assegnabile = 0
    per_tipo = {}
    fuori_sezione = []
    for blk in blocchi:
        lo = int(blk["base"], 16) - base_sezione
        hi = lo + blk["bytes"]
        if lo < 0 or hi > len(b):
            righe.append((blk["nome"], blk["tipo"], blk["bytes"], None, "FUORI DALLA SEZIONE"))
            fuori_sezione.append(blk["nome"])
            continue
        seg = b[lo:hi]
        davvero_zero = all(x == 0 for x in seg)
        per_tipo[blk["tipo"]] = per_tipo.get(blk["tipo"], 0) + blk["bytes"]
        if blk["tipo"] == "libero":
            assegnabile = blk.get("assegnabile", True)
            if not assegnabile:
                libero_non_assegnabile += blk["bytes"]
                righe.append((blk["nome"], blk["tipo"], blk["bytes"], davvero_zero,
                              "libero ma NON assegnabile (manifest lo dichiara intoccabile): NON conta"))
            elif davvero_zero:
                libero_assegnabile += blk["bytes"]
                righe.append((blk["nome"], blk["tipo"], blk["bytes"], True, "conta come libero assegnabile"))
            else:
                righe.append((blk["nome"], blk["tipo"], blk["bytes"], False,
                              "dichiarato libero ma NON e' a zero: NON conta"))
        else:
            righe.append((blk["nome"], blk["tipo"], blk["bytes"], davvero_zero, "non disponibile"))
    return libero_assegnabile, libero_non_assegnabile, righe, per_tipo, fuori_sezione


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    rom = argv[0]
    manifest_path = None
    if "--manifest" in argv:
        manifest_path = argv[argv.index("--manifest") + 1]
    stato = None
    if "--stato" in argv:
        stato = int(argv[argv.index("--stato") + 1])
    secs, rom_off, ram, size = sezioni(rom)
    print(f"{rom}\n  ARM9: rom_off={rom_off:#x} ram={ram:#010x} size={size} ({size} B)")
    trovata = None
    for s in secs:
        marca = ""
        if MAINEX_LO <= s.ramAddress < MAINEX_HI:
            marca = "  <-- riserva"
            trovata = s
        print(f"  sezione ram={s.ramAddress:#010x} len={len(s.data):7d} bss={s.bssSize}{marca}")
    if trovata is None:
        print(f"\n  RISERVA NON TROVATA in {MAINEX_LO:#010x}..{MAINEX_HI:#010x}:"
              f" questa immagine non ha una sezione di riserva")
        return 1
    b = trovata.data
    nonnulli = [i for i, x in enumerate(b) if x]
    if not nonnulli:
        print("\n  riserva tutta a zero: non e' stata popolata")
        return 1
    ultimo = max(nonnulli)
    coda = len(b) - (ultimo + 1)
    print(f"\n  dimensione        {len(b):6d} B")
    print(f"  occupata fino a   +{ultimo:<5d} ({ultimo + 1} B)  "
          f"(ultimo byte NON nullo: non vede i buchi IN MEZZO alla sezione)")
    print(f"  coda azzerata     {coda:6d} B  (vede solo la coda, non i buchi in mezzo)")
    print(f"  cima              {trovata.ramAddress:#010x}   fine {trovata.ramAddress+len(b):#010x}")

    if manifest_path:
        libero_ass, libero_non_ass, righe, per_tipo, fuori_sezione = libero_da_manifest(
            b, trovata.ramAddress, manifest_path)
        print(f"\n  manifest          {manifest_path}")
        for nome, tipo, nbyte, zero, nota in righe:
            marcatura = "?" if zero is None else ("OK" if zero else "NON-ZERO")
            print(f"    {nome:20s} {tipo:10s} {nbyte:6d} B  {marcatura:9s}  {nota}")
        print(f"\n  LIBERO ASSEGNABILE (da manifest)      {libero_ass:6d} B")
        if libero_non_ass:
            print(f"  libero MA NON assegnabile (escluso)   {libero_non_ass:6d} B  "
                  f"(REVISIONE 02: prima veniva sommato insieme, C16/D9 della revisione privata)")
        print(f"  per tipo: " + ", ".join(f"{t}={n}" for t, n in sorted(per_tipo.items())))
        if fuori_sezione:
            print(f"\n  ERRORE: {len(fuori_sezione)} blocco/i del manifest FUORI DALLA SEZIONE: "
                  f"{fuori_sezione}. Il manifest non corrisponde a questa ROM.")
            print("  (REVISIONE 02, C17/D9 della revisione privata: prima questo caso usciva "
                  "0 senza avvisare)")
            return 4
        return 0

    if stato is not None:
        libero = max(0, coda - stato)
        print(f"\n  [LEGACY --stato {stato}]  stato a riposo {stato} B  ->  "
              f"LIBERO VERO (legacy) {libero} B")
        print("  ATTENZIONE: questo calcolo vede solo la CODA e sottrae una costante "
              "scelta a mano: usare --manifest per un numero che si puo' verificare.")
        return 0

    print("\n  LIBERO VERO       SCONOSCIUTO senza --manifest o --stato: la coda "
          "azzerata da sola non dice quanto e' davvero disponibile (i buchi in mezzo "
          "alla sezione non si vedono). Passare --manifest "
          "docs/arm9-reserve-map.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
