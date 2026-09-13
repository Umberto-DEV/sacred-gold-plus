#!/usr/bin/env python3
"""Applicatore in luogo delle correzioni testuali di SGP-1.2-LINGUA-03.

Cantiere L1 fase 4 (preparazione), SGP-1.2-LINGUA-04, 12 settembre 2026.

Metodo (eredita la 1.1, `private development notes` sezione 3.4): ogni banco di
messaggi e' un membro del NARC unico `a/0/2/7`. Un membro modificato puo' solo restare uguale o
rimpicciolirsi rispetto all'originale; viene sempre riempito di zeri in coda fino a tornare alla
lunghezza originale byte per byte. Con la lunghezza del membro invariata l'intero file `a/0/2/7`
ha la stessa lunghezza di prima e puo' essere reinserito nella ROM senza spostare nient'altro
(si riusa `rom_container.append_files(..., reuse_existing=True)`).

Nessun testo di gioco e' scritto in questo file: le stringhe sono lette da
`SGP-1.2-LINGUA-03/CORREZIONI.tsv` a runtime.

Uso:
    applica_testi.py --rom IN.nds --out OUT.nds --lang {EN,IT} --correzioni CORREZIONI.tsv \
        --pret-source DIR --report report.json
    applica_testi.py --in-luogo ROM.nds --lang {EN,IT} --correzioni CORREZIONI.tsv \
        --pret-source DIR --report report.json [--tmp-dir DIR]

`--in-luogo` copia la ROM in un file temporaneo e applica li'. Sostituisce l'originale solo se
non ci sono RIFIUTO "duri" (preimmagine diversa, spazio insufficiente, tag di controllo rotto,
banco/messaggio fuori intervallo): indicano un disallineamento fra CORREZIONI.tsv e la ROM
bersaglio, e vanno guardati prima di riprovare. Un RIFIUTATA_LARGHEZZA senza prova del limite del
banco (vedi CRITERI.md) e' invece "morbido": e' l'esito atteso e documentato per le righe senza
prova, non blocca la sostituzione delle altre, e resta comunque elencato riga per riga nel report.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANSLATION_DIR = HERE.parents[1] / 'translation'
QUALITY_DIR = HERE.parents[1] / 'quality-audit'
sys.path.insert(0, str(TRANSLATION_DIR))
sys.path.insert(0, str(QUALITY_DIR))

from message_codec import Bank, encode_text, pack_name  # noqa: E402
from rom_container import append_files  # noqa: E402
import misura_larghezza as mw  # noqa: E402
import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402

MSG_ARCHIVE = 'a/0/2/7'
FONT_ARCHIVE = 'a/0/1/6'

# Limiti di larghezza in pixel per banco, motivati banco per banco in
# SGP-1.2-LINGUA-03/RAPPORTO.md paragrafo 4. Default: finestra di dialogo generica (ipotesi
# prudente di LOCALIZATION.md).
DEFAULT_LIMIT_PX = 216
BANK_LIMIT_PX = {}
for _b in range(411, 421):
    BANK_LIMIT_PX[_b] = 224          # radio, sWindowTemplates[0].width = 28 tile
BANK_LIMIT_PX[309] = 224              # stesso banco radio-adiacente verificato dal retail EN
BANK_LIMIT_PX[803] = 222              # Pokedex, retail EN arriva a 222 nello stesso banco
BANK_LIMIT_PX[804] = 222
BANK_LIMIT_PX[180] = 256              # Sala d'Onore, register_hall_of_fame.c .width = 32 tile
BANK_LIMIT_PX[13] = 234               # retail EN nello stesso banco arriva a 234


def bank_limit_px(bank_index: int) -> int:
    return BANK_LIMIT_PX.get(bank_index, DEFAULT_LIMIT_PX)


def load_charmap(pret_source: Path):
    """Ricostruisce chars/commands da charmap.txt, come
    source/translation/audit_localization.py::mapping() -- reimplementato qui invece di
    importare quel modulo perche' quest'ultimo tiene stato globale mutabile pensato per un
    programma a riga di comando unico."""
    chars, commands = {}, {}
    for line in (pret_source / 'charmap.txt').read_text().splitlines():
        line = line.split('//')[0].lstrip()
        if not line or '=' not in line:
            continue
        code, text = line.split('=', 1)
        code = int(code, 16)
        if text.startswith('{') and text.endswith('}'):
            commands[code] = text[1:-1]
        else:
            chars[code] = text
    return chars, commands


def decode_text(words, chars, commands):
    """Rende un messaggio decodificato in notazione testuale (stessa di CORREZIONI.tsv).
    Ritorna (testo, ok) dove ok e' False se ci sono codici sconosciuti o controlli malformati."""
    reverse_commands = commands
    i = 0
    out = []
    ok = True
    n = len(words)
    while i < n:
        c = words[i]
        i += 1
        if c == 0xFFFF:
            break
        if c == 0xFFFE:
            if i + 2 > n:
                ok = False
                break
            command, count = words[i], words[i + 1]
            args = words[i + 2:i + 2 + count]
            if len(args) != count:
                ok = False
                break
            i += 2 + count
            name = reverse_commands.get(command)
            if not name and command & 0xFF00 in (0x100, 0x300, 0x400, 0x3400):
                name = f'STRVAR_{command >> 8:X}:{command & 255}'
            out.append('{' + (name or f'CMD_{command:04X}') + (':' if args else '') + ','.join(map(str, args)) + '}')
        elif c in chars:
            out.append(chars[c])
        else:
            out.append(f'<{c:04X}>')
            ok = False
    return ''.join(out), ok


def load_correzioni(path: Path, lang: str, include_c: bool = False):
    rows = []
    with path.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['lingua'] != lang:
                continue
            if row['priorita'] == 'C' and not include_c:
                continue
            variante = row['variante_corta'].strip()
            rows.append({
                'banco': int(row['banco']),
                'messaggio': int(row['id_messaggio']),
                'testo_attuale': row['testo_attuale'],
                'testo_proposto': row['testo_proposto'],
                'variante_corta_grezza': variante or None,
                'priorita': row['priorita'],
                'nome_simbolico': row['nome_simbolico'],
            })
    return rows


# Le uniche 3 correzioni in perimetro (A/B) la cui `variante_corta` contiene un'annotazione fra
# parentesi da scartare (byte risparmiati, condizioni): il testo puro di fallback e' scritto qui
# una sola volta, letto da CORREZIONI.tsv e verificato per intero (non troncato a occhio) da
# `test_variant_pure_text_matches_source` in mutanti/test_mutanti.py.
VARIANT_PURE_TEXT = {
    (219, 43): (
        '{STRVAR_1:3:0,0}!\\nAre you ready?\\rYour very own tale of grand adventure\\n'
        'is about to unfold.\\rLet’s go to the world of Pokémon!\\r'
        'I’ll see you later!\\r(If you ever want to find out some of\\n'
        'the changes, check the documents that\\fshould have come with your game.\\r'
        'Most, if not all, information you need\\nshould be in there somewhere.\\r'
        'But play as you like, for you might\\nenjoy playing the unknown! Either way,\\f'
        'be sure to have fun! -- Dray)\\r'
    ),
    (749, 6): (
        'The user stares at\\nthe target with\\nbaby-doll eyes,\\nlowering its\\nAttack stat.'
    ),
    (279, 201): 'Centr. Elettrica',
}


def variant_pure_text(banco, messaggio, variante_grezza):
    key = (banco, messaggio)
    if key in VARIANT_PURE_TEXT:
        return VARIANT_PURE_TEXT[key]
    # Fallback generico per una futura riga con variante non ancora ricondotta a mano: il testo
    # puro e' tutto cio' che precede la prima annotazione "  (" (due spazi e parentesi), che nella
    # sorgente di LINGUA-03 introduce sempre la nota sui byte risparmiati.
    if variante_grezza is None:
        return None
    marker = variante_grezza.find('  (')
    return variante_grezza[:marker] if marker >= 0 else variante_grezza


class Rejection(Exception):
    def __init__(self, reason, detail=None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def encode_words(text, chars, commands, is_packed_name):
    try:
        words = encode_text(text, chars, commands)
    except ValueError as exc:
        raise Rejection('RIFIUTATA_CONTROLLO_NON_VALIDO', str(exc))
    if is_packed_name:
        words = pack_name(words)
    return words


def process_bank(bank_index, raw_member, edits, chars, commands, width_table, report_rows):
    """Applica tutte le correzioni destinate a un banco. Ritorna (nuovo_raw_o_None, modificato)."""
    try:
        bank = Bank(raw_member)
    except ValueError as exc:
        for e in edits:
            report_rows.append(row_result(bank_index, e, 'RIFIUTATA_BANCO_NON_VALIDO', str(exc)))
        return None, False

    limit_px = bank_limit_px(bank_index)
    original_len = len(raw_member)
    touched = False

    for edit in edits:
        msg = edit['messaggio']
        if not (0 <= msg < len(bank.words)):
            report_rows.append(row_result(bank_index, edit, 'RIFIUTATA_MESSAGGIO_FUORI_BANCO',
                                           f'{msg} fuori da [0,{len(bank.words)})'))
            continue

        words = bank.words[msg]
        current_text, current_ok = decode_text(words, chars, commands)

        pure_variant = variant_pure_text(bank_index, msg, edit['variante_corta_grezza'])

        if current_text == edit['testo_proposto']:
            report_rows.append(row_result(bank_index, edit, 'GIA_APPLICATA', 'testo_proposto'))
            continue
        if pure_variant is not None and current_text == pure_variant:
            report_rows.append(row_result(bank_index, edit, 'GIA_APPLICATA', 'variante_corta'))
            continue
        if current_text != edit['testo_attuale']:
            report_rows.append(row_result(bank_index, edit, 'RIFIUTATA_PREIMMAGINE',
                                           f'attuale={current_text!r}'))
            continue

        is_packed_name = bool(words) and words[0] == 0xF100

        # Prova (b) di SGP-1.2-LINGUA-03 sezione "Passo 4": una riga non e' un overflow se il
        # testo GIA' SPEDITO nello stesso identificatore di messaggio raggiunge o supera la sua
        # larghezza. Il limite di contesto (216 px di default, piu' alto nei banchi elencati in
        # BANK_LIMIT_PX) e' quindi un minimo, non un massimo: una correzione che non allarga la
        # riga oltre quanto la ROM gia' spedisce non puo' essere un regresso, anche se supera
        # l'ipotesi prudente di LOCALIZATION.md. Cresce SOLO se la correzione stessa peggiora la
        # situazione oltre il piu' alto fra i due.
        current_width = mw.measure(width_table, words, None)['max_width_px']
        effective_limit = max(limit_px, current_width)

        def try_candidate(text, label):
            try:
                new_words = encode_words(text, chars, commands, is_packed_name)
            except Rejection as rej:
                return None, rej.reason, rej.detail
            saved_words = bank.words[msg]
            bank.words[msg] = new_words
            candidate_raw = bank.save()
            bank.words[msg] = saved_words
            if len(candidate_raw) > original_len:
                return None, 'RIFIUTATA_SPAZIO', (
                    f'{label}: membro cresce a {len(candidate_raw)} B > originale {original_len} B')
            report = mw.measure(width_table, new_words, effective_limit)
            if report['any_over_limit']:
                return None, 'RIFIUTATA_LARGHEZZA', (
                    f'{label}: {report["max_width_px"]} px > limite effettivo {effective_limit} px '
                    f'(banco {bank_index}, contesto {limit_px} px, gia spedito {current_width} px)')
            return new_words, None, None

        new_words, reason, detail = try_candidate(edit['testo_proposto'], 'principale')
        applied_label = 'testo_proposto'
        if new_words is None and reason in ('RIFIUTATA_SPAZIO', 'RIFIUTATA_LARGHEZZA') and pure_variant is not None:
            new_words2, reason2, detail2 = try_candidate(pure_variant, 'variante_corta')
            if new_words2 is not None:
                new_words, reason, detail = new_words2, None, None
                applied_label = 'variante_corta'
            else:
                reason, detail = reason2, f'{detail} | poi {detail2}'

        if new_words is None:
            report_rows.append(row_result(bank_index, edit, reason, detail))
            continue

        bank.words[msg] = new_words
        touched = True
        report_rows.append(row_result(bank_index, edit, 'APPLICATA', applied_label))

    if not touched:
        return None, False

    final_raw = bank.save()
    if len(final_raw) > original_len:
        raise Rejection('BANCO_CRESCIUTO_INASPETTATAMENTE',
                         f'banco {bank_index}: {len(final_raw)} > {original_len}')
    if len(final_raw) < original_len:
        final_raw = final_raw + b'\x00' * (original_len - len(final_raw))
    return final_raw, True


def row_result(banco, edit, esito, dettaglio):
    return {
        'banco': banco,
        'messaggio': edit['messaggio'],
        'nome_simbolico': edit['nome_simbolico'],
        'priorita': edit['priorita'],
        'esito': esito,
        'dettaglio': dettaglio,
    }


def apply_to_rom_bytes(rom_bytes, lang, correzioni_path, pret_source, include_c=False):
    """Nucleo puro: prende i byte di una ROM, ritorna (nuovi_byte_o_None, report_dict)."""
    chars, commands = load_charmap(pret_source)
    rom = ndspy.rom.NintendoDSRom(rom_bytes)
    msg_raw = rom.getFileByName(MSG_ARCHIVE)
    narc = ndspy.narc.NARC(msg_raw)
    font_narc = ndspy.narc.NARC(rom.getFileByName(FONT_ARCHIVE))
    width_table = mw.extract_width_table(font_narc.files[0])
    check = mw.self_check(width_table)

    rows = load_correzioni(correzioni_path, lang, include_c=include_c)
    by_bank = {}
    for r in rows:
        by_bank.setdefault(r['banco'], []).append(r)

    report_rows = []
    replaced_any = False
    for bank_index, edits in sorted(by_bank.items()):
        if not (0 <= bank_index < len(narc.files)):
            for e in edits:
                report_rows.append(row_result(bank_index, e, 'RIFIUTATA_BANCO_FUORI_NARC',
                                               f'{bank_index} fuori da [0,{len(narc.files)})'))
            continue
        original_member = narc.files[bank_index]
        new_member, touched = process_bank(bank_index, original_member, edits, chars, commands,
                                            width_table, report_rows)
        if touched:
            assert len(new_member) == len(original_member)
            narc.files[bank_index] = new_member
            replaced_any = True

    summary = {
        'lingua': lang,
        'font_self_check_ok': check['ok'],
        'font_self_check_mismatches': check['mismatches'],
        'righe_totali_in_perimetro': len(rows),
        'righe': report_rows,
        'conteggi_esito': {},
    }
    for r in report_rows:
        summary['conteggi_esito'][r['esito']] = summary['conteggi_esito'].get(r['esito'], 0) + 1

    if not replaced_any:
        summary['narc_modificato'] = False
        return None, summary

    new_msg_raw = narc.save()
    if len(new_msg_raw) != len(msg_raw):
        raise Rejection('NARC_LUNGHEZZA_CAMBIATA', f'{len(new_msg_raw)} != {len(msg_raw)}')

    new_rom_bytes, changes = append_files(rom_bytes, {MSG_ARCHIVE: new_msg_raw}, reuse_existing=True)
    if len(new_rom_bytes) != len(rom_bytes):
        raise Rejection('ROM_LUNGHEZZA_CAMBIATA', f'{len(new_rom_bytes)} != {len(rom_bytes)}')
    for change in changes:
        if not change['reused_extent']:
            raise Rejection('FILE_RILOCATO', json.dumps(change))

    summary['narc_modificato'] = True
    summary['rom_container_changes'] = changes
    return new_rom_bytes, summary


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--in-luogo', type=Path, dest='in_luogo')
    p.add_argument('--lang', choices=('EN', 'IT'), required=True)
    p.add_argument('--correzioni', type=Path, required=True)
    p.add_argument('--pret-source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--include-c', action='store_true', help='Applica anche le righe di priorita C (non usato in fase 4).')
    p.add_argument('--tmp-dir', type=Path, default=None)
    args = p.parse_args(argv)

    if bool(args.rom or args.out) == bool(args.in_luogo):
        p.error('Usare esattamente uno fra --rom/--out e --in-luogo')

    if args.in_luogo:
        target = args.in_luogo
        original_bytes = target.read_bytes()
        try:
            new_bytes, summary = apply_to_rom_bytes(original_bytes, args.lang, args.correzioni,
                                                      args.pret_source, args.include_c)
        except Rejection as rej:
            summary = {'errore_fatale': rej.reason, 'dettaglio': rej.detail}
            args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return 2
        all_rejected = [r for r in summary.get('righe', []) if r['esito'].startswith('RIFIUTATA')]
        # RIFIUTATA_LARGHEZZA su un banco senza costante di finestra verificata e' l'esito
        # atteso (vedi CRITERI.md): non e' un segnale di ROM/CORREZIONI.tsv disallineati come lo
        # sono invece gli altri RIFIUTATA_*, quindi da solo non blocca la sostituzione.
        hard_rejected = [r for r in all_rejected if r['esito'] != 'RIFIUTATA_LARGHEZZA']
        summary['modalita'] = 'in-luogo'
        summary['sostituito'] = False
        summary['righe_rifiutate_morbide_larghezza'] = len(all_rejected) - len(hard_rejected)
        if new_bytes is None:
            summary['nota'] = 'Nessuna correzione da applicare (tutte gia applicate o rifiutate).'
        elif hard_rejected:
            summary['nota'] = f'{len(hard_rejected)} righe rifiutate (dure): originale NON sostituito.'
        else:
            tmp_dir = args.tmp_dir or target.parent
            # apply_to_rom_bytes ha gia' verificato (e solleva Rejection altrimenti) che
            # new_bytes abbia la stessa lunghezza di original_bytes.
            with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False, suffix='.nds.tmp') as tf:
                tf.write(new_bytes)
                tmp_path = Path(tf.name)
            # La verifica indipendente vera e propria e' `rileggi_testi.py --before <originale
            # salvato altrove> --after <questo file>`, da eseguire separatamente: qui si sostituisce
            # solo se tutte le righe in perimetro sono verdi (nessun RIFIUTATA_*).
            shutil.move(str(tmp_path), str(target))
            summary['sostituito'] = True
            summary['nota'] = 'Originale sostituito: tutte le righe applicabili sono verdi. Eseguire comunque rileggi_testi.py con una copia separata del "prima".'
        args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
        print(json.dumps({k: v for k, v in summary.items() if k != 'righe'}, indent=2, ensure_ascii=False))
        return 0

    if args.out.exists():
        p.error(f'{args.out} esiste gia: nessun file viene sovrascritto')
    rom_bytes = args.rom.read_bytes()
    try:
        new_bytes, summary = apply_to_rom_bytes(rom_bytes, args.lang, args.correzioni,
                                                  args.pret_source, args.include_c)
    except Rejection as rej:
        summary = {'errore_fatale': rej.reason, 'dettaglio': rej.detail}
        args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 2
    summary['modalita'] = 'rom-out'
    if new_bytes is None:
        summary['nota'] = 'Nessuna correzione applicabile: nessun file scritto.'
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('xb') as f:
            f.write(new_bytes)
    args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'righe'}, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
