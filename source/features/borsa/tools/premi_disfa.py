#!/usr/bin/env python3
"""premi_disfa.py — SGP-1.2-BORSA-GEN-05.

Riporta al vanilla i 4 percorsi introdotti da `SGP-1.1-REWARD-01` dentro il
NARC `a/0/1/2` (membri 843, 859, 877 — 843 ne porta due, al laboratorio di
Elm). Lavora SEMPRE su una copia: l'uscita e' un file nuovo, mai la sorgente.

I 352 B liberati servono alle appendici del messaggio 199#10.

--- Il vanilla NON e' la HeartGold ------------------------------------------

Il pacchetto chiedeva di prendere il vanilla dei tre membri dalla HeartGold
ORIGINALE della stessa lingua. Verificato PRIMA di scrivere codice (vedi
RAPPORTO.md, sezione «Il vanilla non e' la HeartGold», dati riproducibili con
`python3 -m test_premi -v` classe A):

    membro   HeartGold US/IT   Sacred Gold Plus 1.03/1.01   SGP 1.2.1 (patchato)
    843      4440 B            5468 B                       5644 B
    859       516 B             516 B                        604 B
    877       424 B             457 B                        545 B

Sacred Gold ha GIA' cambiato i membri 843 e 877 rispetto alla HeartGold
PRIMA di REWARD-01 (probabilmente il proprio disegno del laboratorio di Elm
e dell'incontro con Furio/Chuck): usare la HeartGold come vanilla
cancellerebbe quel lavoro di Sacred Gold, non solo REWARD. Il membro 859
(Falkner) e' invece bit-per-bit identico fra HeartGold e Sacred Gold 1.03: li'
la scelta non avrebbe fatto danno, ma per coerenza dei tre membri si usa
un'unica fonte.

La 1.03 e la 1.01 di Sacred Gold Plus hanno i tre membri IDENTICI byte per
byte (nessuna deriva 1.01->1.03): baseline stabile. E la prova decisiva:
`reward_fix.patch_member` applicato ai tre membri della 1.03 riproduce
ESATTAMENTE (sha256 uguale) i membri patchati della 1.2.1 attuale, EN e IT
(che sono anch'essi identici fra loro: lo script non porta testo). La 1.03 e'
dunque la vera preimmagine su cui REWARD-01 fu costruito, non la HeartGold.
Il pubblico conserva soltanto lunghezze e impronte crittografiche come
post-condizioni, senza distribuire la ROM usata per stabilirle.

--- Come si toglie -----------------------------------------------------------

REWARD-01 sostituisce, per ciascun gancio, l'istruzione
`HasSpaceForItem` originale con un `GoTo` a 6 byte
verso una routine di 88 B accodata in fondo al membro; i due byte finali della
vecchia istruzione restano intoccati e irraggiungibili. L'inverso e'
quindi: ripristinare quei 6 byte e troncare il membro alla lunghezza vanilla —
le routine accodate stanno solo in coda, quindi il troncamento le toglie tutte
in un colpo, anche per gli 843 (due ganci, due routine, 88+88=176 B).

Il gate vero non e' quello strutturale (e' solo la ricetta, documentata sopra
per essere leggibile): e' lo sha256 dell'INTERO membro, prima e dopo
(preimmagine = patchato atteso, postimmagine = vanilla atteso). Qualunque
divergenza, anche di un bit fuori dai ganci, fa rifiutare la scrittura.

--- Il NARC che si accorcia (352 B) -------------------------------------------

`a/0/1/2` e' un file NitroFS con nome, non un blocco ARM9: `sgp12.rom.Rom` non
ha un risolutore di nomi (FNT), sa solo camminare la FAT per id numerico — va
bene per ARM9/overlay ma non per «dammi il file che si chiama a/0/1/2». Si usa
percio' `ndspy.rom.NintendoDSRom`/`ndspy.narc.NARC` per leggere e ricostruire
l'archivio (come fa gia' `reward_fix.py` e come fa `applica_testi.py`), e
**`source/translation/rom_container.append_files(..., reuse_existing=True)`**
per riscriverlo nella ROM: e' la funzione che gia' usa `applica_testi.py` per
lo stesso identico problema (un membro di un NARC NitroFS che DIMINUISCE di
lunghezza) — commento suo, testuale: «un membro modificato puo' solo restare
uguale o rimpicciolirsi [...] puo' essere reinserito nella ROM senza spostare
nient'altro». Qui il file intero si accorcia (non viene riempito di zeri: il
container NARC ricostruito da `narc.save()` e' gia' piu' corto, non c'e' nulla
da imbottire), quindi `reuse_existing=True` lo riscrive IN LUOGO: stesso
offset di inizio, fine della voce FAT ridotta di 352 B, nessun altro file si
sposta, la ROM resta della stessa lunghezza byte per byte. E' esattamente la
via "preferita" dal pacchetto. Non si usa `reward_fix.build_rom`/
`append_files(reuse_existing=False)`: quella APPENDE sempre in coda alla ROM e
fa CRESCERE l'immagine — corretto quando REWARD-01 aggiungeva byte, sbagliato
qui che li toglie.

Uso:
    premi_disfa.py SORGENTE.nds USCITA.nds [--report report.json]

`USCITA.nds` non deve esistere gia' (si sceglie sempre un percorso fresco,
come fa `reward_fix.py`). Il programma rifiuta (niente scrittura) se:
  * un membro non e' ne' nello stato patchato atteso ne' gia' vanilla
    (preimmagine ignota: ROM diversa da quella per cui questo script e' stato
    scritto);
  * la ROM sorgente e' gia' vanilla sui tre membri (idempotenza: seconda
    corsa rifiutata con codice di uscita 3, «gia' vanilla»).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANSLATION_DIR = HERE.parents[2] / 'translation'
sys.path.insert(0, str(TRANSLATION_DIR))

from rom_container import append_files  # noqa: E402
import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402

ARCHIVE_NAME = 'a/0/1/2'
N_MEMBERS_ATTESI = 965

# Gancio (offset, successo, fallimento, quantita', tetto, script comune),
# identico a reward_fix.CALLERS: 843 ha due doni (lab di Elm, due ingressi),
# 859 e 877 uno solo ciascuno (Falkner/MT51, Furio-Chuck/MT01).
CALLERS = {
    859: [(306, 331, 350, 1, 99, 2033)],
    877: [(306, 331, 414, 1, 99, 2033)],
    843: [(2387, 2424, 3658, 5, 999, 2008), (4165, 4202, 3658, 5, 999, 2008)],
}

# I 6 byte del GoTo che REWARD-01 innesta al posto della testa della
# HasSpaceForItem originale (comando 22, poi il delta a 4 byte con segno).
GOTO_OPCODE = 22

# Preimmagine attesa: il membro PATCHATO (stato 1.2.1 corrente, prima di
# questo script), identico EN/IT perche' lo script non porta testo.
PATCHATO = {
    843: (5644, '26751ad51c98cb15cc90a7a1b54965615a5fc60a73708984858659a7fd23016c'),
    859: (604, 'ff51dc47b46cfa9a27544f313b0bd502dea4e3ddd7f32a5e602a6ce8241a8615'),
    877: (545, '73e28d4c22c66e12a74fcaa86b6b46b35a426ccc6d7fbb78e3884004a2ed4a93'),
}

# Postimmagine attesa: il membro precedente a REWARD-01. Stessi sha256 del
# contratto di REWARD-01 (che li chiama
# "preimmagine" dal SUO punto di vista, cioe' prima che REWARD-01 patchasse).
VANILLA = {
    843: (5468, 'cb690bc3b229515e11dda13d691f354e0d39905597b7b2d2abd3bafb200862d1'),
    859: (516, '5abff969bd83c4975cf0815c2f5c7c28d581cb2ecae994ca3049123918d41f9e'),
    877: (457, '742f3f4fe75ecc952fa8fbbdc9ecee56c5f743f5199d864eb2725721cc2f4f00'),
}

ARCHIVIO_PATCHATO = 442616
ARCHIVIO_VANILLA = 442264


class Rifiuto(Exception):
    """Nessun byte viene scritto quando questo vola."""


class GiaVanilla(Rifiuto):
    """I tre membri sono gia' allo stato vanilla: idempotenza, si rifiuta."""


def sha(data: bytes) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()


def _stato(data: bytes, member: int):
    taglia, firma = len(data), sha(data)
    if (taglia, firma) == PATCHATO[member]:
        return 'patchato'
    if (taglia, firma) == VANILLA[member]:
        return 'vanilla'
    return None


def restore_member(data: bytes, member: int) -> bytes:
    """Inverte `reward_fix.patch_member` su un singolo membro.

    Rifiuta (Rifiuto) se la preimmagine non e' esattamente quella patchata
    attesa. Solleva GiaVanilla se e' gia' quella vanilla attesa.
    """
    stato = _stato(data, member)
    if stato == 'vanilla':
        raise GiaVanilla(member)
    if stato != 'patchato':
        raise Rifiuto(
            "membro %d: preimmagine inattesa (%d B, sha256 %s...) - non e' patchata"
            " ne' vanilla, questo script e' scritto per lo stato esatto della 1.2.1"
            % (member, len(data), sha(data)[:16]))

    out = bytearray(data)
    van_size, van_sha = VANILLA[member]
    for hook, success, failure, qty, cap, std in CALLERS[member]:
        coda = bytes(out[hook + 6:hook + 8])
        if coda != bytes.fromhex('0c80'):
            raise Rifiuto(
                'membro %d: coda del gancio a %#x alterata (attesi 0c80, letti %s)'
                % (member, hook, coda.hex()))
        opcode = int.from_bytes(out[hook:hook + 2], 'little')
        if opcode != GOTO_OPCODE:
            raise Rifiuto(
                "membro %d: gancio a %#x non e' un GoTo (opcode %d atteso %d)"
                % (member, hook, opcode, GOTO_OPCODE))
        # Ripristina gli 8 byte originali della HasSpaceForItem stretta.
        out[hook:hook + 8] = bytes.fromhex('7f00048005800c80')

    # Le routine accodate stanno tutte in coda, in ordine: troncare alla
    # lunghezza vanilla le toglie tutte in un colpo solo (176 B per 843,
    # due ganci; 88 B per 859 e 877, un gancio ciascuno).
    del out[van_size:]

    if len(out) != van_size or sha(out) != van_sha:
        raise Rifiuto(
            'membro %d: il ripristino strutturale non riproduce il vanilla atteso '
            '(bug in premi_disfa.py, non nella ROM)' % member)
    return bytes(out)


def disfa_rom(source_bytes: bytes) -> tuple[bytes, dict]:
    rom = ndspy.rom.NintendoDSRom(source_bytes)
    try:
        archive_bytes = rom.getFileByName(ARCHIVE_NAME)
    except Exception as exc:  # ndspy solleva vari tipi a seconda della versione
        raise Rifiuto('%s assente dalla ROM: %s' % (ARCHIVE_NAME, exc)) from exc
    narc = ndspy.narc.NARC(archive_bytes)
    if len(narc.files) != N_MEMBERS_ATTESI:
        raise Rifiuto('%s: %d membri, attesi %d' % (ARCHIVE_NAME, len(narc.files), N_MEMBERS_ATTESI))

    esiti, gia_vanilla = {}, []
    for member in sorted(CALLERS):
        prima = bytes(narc.files[member])
        try:
            dopo = restore_member(prima, member)
        except GiaVanilla:
            gia_vanilla.append(member)
            continue
        narc.files[member] = dopo
        esiti[member] = {
            'prima': {'byte': len(prima), 'sha256': sha(prima)},
            'dopo': {'byte': len(dopo), 'sha256': sha(dopo)},
        }

    if len(gia_vanilla) == len(CALLERS):
        raise GiaVanilla("tutti i membri (%s) sono gia' vanilla" % sorted(CALLERS))
    if gia_vanilla:
        raise Rifiuto("stato misto: %s gia' vanilla, %s ancora patchati - ROM incoerente"
                       % (gia_vanilla, sorted(esiti)))

    nuovo_archivio = narc.save()
    if len(nuovo_archivio) != ARCHIVIO_VANILLA:
        raise Rifiuto('archivio ricostruito: %d B, atteso %d B' % (len(nuovo_archivio), ARCHIVIO_VANILLA))

    result_bytes, changes = append_files(
        source_bytes, {ARCHIVE_NAME: nuovo_archivio}, reuse_existing=True)
    if len(changes) != 1 or not changes[0]['reused_extent']:
        raise Rifiuto('rom_container non ha riscritto %s in luogo (changes=%r)' % (ARCHIVE_NAME, changes))
    if len(result_bytes) != len(source_bytes):
        raise Rifiuto("la dimensione della ROM e' cambiata (%d -> %d): non doveva"
                       % (len(source_bytes), len(result_bytes)))

    report = {
        'archivio': {
            'nome': ARCHIVE_NAME,
            'prima': {'byte': len(archive_bytes), 'sha256': sha(archive_bytes)},
            'dopo': {'byte': len(nuovo_archivio), 'sha256': sha(nuovo_archivio)},
        },
        'rom': {
            'prima': {'byte': len(source_bytes), 'sha256': sha(source_bytes)},
            'dopo': {'byte': len(result_bytes), 'sha256': sha(result_bytes)},
        },
        'membri': esiti,
        'rom_container_changes': changes,
    }
    return result_bytes, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, default=None)
    args = parser.parse_args(argv)

    if args.output.exists():
        parser.error("%s esiste gia': scegliere un percorso di uscita fresco" % args.output)

    source_bytes = args.source.read_bytes()
    try:
        result_bytes, report = disfa_rom(source_bytes)
    except GiaVanilla as exc:
        print("RIFIUTO (gia' vanilla): %s" % exc, file=sys.stderr)
        return 3
    except Rifiuto as exc:
        print('RIFIUTO: %s' % exc, file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result_bytes)
    testo = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(testo, encoding='utf-8')
    print(testo)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
