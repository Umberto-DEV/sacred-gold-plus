#!/usr/bin/env python3
"""Rilettore indipendente per le correzioni applicate da SGP-1.2-LINGUA-04/applica_testi.py.

Non importa nulla da `applica_testi.py`: condivide solo `message_codec.py` (il codec byte-esatto
del banco, non una scelta editoriale di quello script). La resa testuale dei codici, la tabella
dei banchi radio/Pokedex/Sala d'Onore a limite di larghezza diverso e la lettura della "variante
corta" pura sono riscritte qui da zero, cosi' un bug logico nell'applicatore non si nasconderebbe
dietro lo stesso codice riusato dal suo stesso rilettore.

Verifica, dati una ROM "prima" e una "dopo":
  1. ogni file della ROM diverso da `a/0/2/7` e' byte-identico (implica FAT/dimensioni invariate
     per tutti gli altri file, e nessuna ricollocazione);
  2. `a/0/2/7` ha la stessa lunghezza totale prima/dopo;
  3. dentro `a/0/2/7`, ogni banco NON elencato in CORREZIONI.tsv per la lingua data e' byte-identico;
  4. per ogni riga A/B in perimetro: il messaggio "dopo" e' o il testo proposto, o la sua variante
     corta pura, o (se non ancora applicata) il testo attuale originale -- qualunque altra cosa e'
     un esito INATTESO;
  5. ogni messaggio riscritto rispetta il limite di larghezza del suo banco.

Nessun testo di gioco e' scritto in questo file.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANSLATION_DIR = HERE.parents[1] / 'translation'
QUALITY_DIR = HERE.parents[1] / 'quality-audit'
sys.path.insert(0, str(TRANSLATION_DIR))
sys.path.insert(0, str(QUALITY_DIR))

from message_codec import Bank  # noqa: E402 -- unico modulo condiviso con l'applicatore
import misura_larghezza as mw  # noqa: E402
import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402

MSG_ARCHIVE = 'a/0/2/7'
FONT_ARCHIVE = 'a/0/1/6'

DEFAULT_LIMIT_PX = 216
_WIDE_BANKS = {b: 224 for b in range(411, 421)}
_WIDE_BANKS.update({309: 224, 803: 222, 804: 222, 180: 256, 13: 234})


def limit_for_bank(bank_index):
    return _WIDE_BANKS.get(bank_index, DEFAULT_LIMIT_PX)


def build_charmap(pret_source: Path):
    """N.B.: alcune voci del charmap hanno per valore un carattere di spaziatura vero e proprio
    (0001='\\u3000' ideografico, 01DE=' ' normale, 01E2='\\u2009' sottile): si toglie solo
    l'indentazione a sinistra della riga, MAI gli spazi a destra del segno uguale, altrimenti
    queste tre voci diventerebbero stringhe vuote."""
    chars, commands = {}, {}
    for raw_line in (pret_source / 'charmap.txt').read_text().splitlines():
        body = raw_line.split('//', 1)[0].lstrip()
        if not body or '=' not in body:
            continue
        hexcode, token = body.split('=', 1)
        n = int(hexcode, 16)
        if token[:1] == '{' and token[-1:] == '}':
            commands[n] = token[1:-1]
        else:
            chars[n] = token
    return chars, commands


def words_to_text(words, chars, commands):
    """Riscritta da zero (non importata da applica_testi.decode_text): stesso obiettivo, cammino
    diverso -- qui si costruisce prima la lista dei token e si unisce alla fine, e il controllo
    di malformazione e' un contatore invece di un flag booleano."""
    tokens = []
    problems = 0
    pos = 0
    end = len(words)
    while pos < end:
        code = words[pos]
        pos += 1
        if code == 0xFFFF:
            break
        if code == 0xFFFE:
            if pos + 2 > end:
                problems += 1
                break
            cmd, argc = words[pos], words[pos + 1]
            arglist = words[pos + 2: pos + 2 + argc]
            if len(arglist) != argc:
                problems += 1
                break
            pos += 2 + argc
            label = commands.get(cmd)
            if not label and (cmd & 0xFF00) in (0x100, 0x300, 0x400, 0x3400):
                label = f'STRVAR_{cmd >> 8:X}:{cmd & 0xFF}'
            if not label:
                label = f'CMD_{cmd:04X}'
            tokens.append('{' + label + ((':' + ','.join(str(a) for a in arglist)) if arglist else '') + '}')
            continue
        glyph = chars.get(code)
        if glyph is None:
            tokens.append(f'<{code:04X}>')
            problems += 1
        else:
            tokens.append(glyph)
    return ''.join(tokens), problems == 0


# Stessa tabella di applica_testi.py, riscritta qui indipendentemente (dato, non logica) perche'
# il rilettore deve poter riconoscere una variante corta gia' applicata senza fidarsi
# dell'applicatore.
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


def load_rows(path: Path, lang: str):
    out = []
    with path.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['lingua'] != lang or row['priorita'] == 'C':
                continue
            out.append({
                'banco': int(row['banco']),
                'messaggio': int(row['id_messaggio']),
                'testo_attuale': row['testo_attuale'],
                'testo_proposto': row['testo_proposto'],
                'nome_simbolico': row['nome_simbolico'],
                'priorita': row['priorita'],
            })
    return out


def compare_roms(before_bytes, after_bytes, lang, rows, chars, commands):
    problems = []
    before_rom = ndspy.rom.NintendoDSRom(before_bytes)
    after_rom = ndspy.rom.NintendoDSRom(after_bytes)

    report = {
        'rom_len_before': len(before_bytes),
        'rom_len_after': len(after_bytes),
        'file_count_before': len(before_rom.files),
        'file_count_after': len(after_rom.files),
    }

    if repr(before_rom.filenames) != repr(after_rom.filenames):
        problems.append('ALBERO_NITROFS_CAMBIATO')
    if len(before_rom.files) != len(after_rom.files):
        problems.append('NUMERO_FILE_CAMBIATO')

    msg_index_before = before_rom.filenames.idOf(MSG_ARCHIVE)
    other_file_diffs = []
    for i in range(min(len(before_rom.files), len(after_rom.files))):
        if i == msg_index_before:
            continue
        if before_rom.files[i] != after_rom.files[i]:
            other_file_diffs.append(i)
    report['altri_file_diversi'] = other_file_diffs
    if other_file_diffs:
        problems.append('FILE_NON_a027_MODIFICATO')

    msg_before = before_rom.getFileByName(MSG_ARCHIVE)
    msg_after = after_rom.getFileByName(MSG_ARCHIVE)
    report['a027_len_before'] = len(msg_before)
    report['a027_len_after'] = len(msg_after)
    if len(msg_before) != len(msg_after):
        problems.append('a027_LUNGHEZZA_CAMBIATA')

    narc_before = ndspy.narc.NARC(msg_before)
    narc_after = ndspy.narc.NARC(msg_after)
    if len(narc_before.files) != len(narc_after.files):
        problems.append('NUMERO_BANCHI_CAMBIATO')

    touched_banks = {r['banco'] for r in rows}
    other_bank_diffs = []
    for i in range(min(len(narc_before.files), len(narc_after.files))):
        if i in touched_banks:
            continue
        if narc_before.files[i] != narc_after.files[i]:
            other_bank_diffs.append(i)
    report['banchi_non_in_perimetro_diversi'] = other_bank_diffs
    if other_bank_diffs:
        problems.append('BANCO_NON_TOCCATO_MODIFICATO')

    row_reports = []
    for r in rows:
        b, m = r['banco'], r['messaggio']
        entry = {'banco': b, 'messaggio': m, 'nome_simbolico': r['nome_simbolico'], 'priorita': r['priorita']}
        if not (0 <= b < len(narc_after.files)):
            entry['esito'] = 'BANCO_ASSENTE'
            row_reports.append(entry)
            problems.append(f'BANCO_ASSENTE_{b}')
            continue
        try:
            bank_after = Bank(narc_after.files[b])
        except ValueError as exc:
            entry['esito'] = 'BANCO_NON_DECODIFICABILE'
            entry['dettaglio'] = str(exc)
            row_reports.append(entry)
            problems.append(f'BANCO_NON_DECODIFICABILE_{b}')
            continue
        if not (0 <= m < len(bank_after.words)):
            entry['esito'] = 'MESSAGGIO_ASSENTE'
            row_reports.append(entry)
            problems.append(f'MESSAGGIO_ASSENTE_{b}#{m}')
            continue
        words_after = bank_after.words[m]
        text_after, ok = words_to_text(words_after, chars, commands)
        entry['ok_decodifica'] = ok
        pure_variant = VARIANT_PURE_TEXT.get((b, m))
        if text_after == r['testo_proposto']:
            entry['esito'] = 'CORRETTO_APPLICATO'
        elif pure_variant is not None and text_after == pure_variant:
            entry['esito'] = 'CORRETTO_APPLICATO_VARIANTE_CORTA'
        elif text_after == r['testo_attuale']:
            entry['esito'] = 'NON_ANCORA_APPLICATA'
        else:
            entry['esito'] = 'INATTESO'
            entry['testo_trovato'] = text_after
            problems.append(f'POSTIMMAGINE_INATTESA_{b}#{m}')
        if not ok:
            problems.append(f'DECODIFICA_MALFORMATA_{b}#{m}')
        row_reports.append(entry)

    return report, row_reports, problems


def check_widths(before_bytes, after_bytes, rows):
    """Il limite di un banco (`limit_for_bank`) e' un'ipotesi prudente quando non e' stato
    verificato da una costante del sorgente decompilato (vedi SGP-1.2-LINGUA-03/RAPPORTO.md
    paragrafo 4). Una riga che la ROM "prima" gia' spediva a una data larghezza dimostra da sola
    che quella finestra regge almeno quella larghezza (stessa prova b del paragrafo citato): il
    limite effettivo usato qui e' quindi il piu' alto fra l'ipotesi di contesto e la larghezza
    gia' spedita per quello stesso messaggio, cosi' il rilettore non segnala come problema una
    correzione che lascia la riga larga quanto era gia'."""
    after_rom = ndspy.rom.NintendoDSRom(after_bytes)
    before_rom = ndspy.rom.NintendoDSRom(before_bytes)
    font_narc = ndspy.narc.NARC(after_rom.getFileByName(FONT_ARCHIVE))
    table = mw.extract_width_table(font_narc.files[0])
    check = mw.self_check(table)
    narc_after = ndspy.narc.NARC(after_rom.getFileByName(MSG_ARCHIVE))
    narc_before = ndspy.narc.NARC(before_rom.getFileByName(MSG_ARCHIVE))
    width_reports = []
    problems = []
    for r in rows:
        b, m = r['banco'], r['messaggio']
        if not (0 <= b < len(narc_after.files)):
            continue
        try:
            bank_after = Bank(narc_after.files[b])
            bank_before = Bank(narc_before.files[b]) if b < len(narc_before.files) else None
        except ValueError:
            continue
        if not (0 <= m < len(bank_after.words)):
            continue
        context_limit = limit_for_bank(b)
        shipped_before_px = 0
        if bank_before is not None and 0 <= m < len(bank_before.words):
            shipped_before_px = mw.measure(table, bank_before.words[m], None)['max_width_px']
        effective_limit = max(context_limit, shipped_before_px)
        measured = mw.measure(table, bank_after.words[m], effective_limit)
        width_reports.append({'banco': b, 'messaggio': m, 'max_width_px': measured['max_width_px'],
                              'limite_contesto_px': context_limit, 'gia_spedito_px': shipped_before_px,
                              'limite_effettivo_px': effective_limit, 'oltre_limite': measured['any_over_limit']})
        if measured['any_over_limit']:
            problems.append(f'LARGHEZZA_OLTRE_LIMITE_{b}#{m}')
    return {'font_self_check_ok': check['ok'], 'righe': width_reports}, problems


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before', type=Path, required=True)
    p.add_argument('--after', type=Path, required=True)
    p.add_argument('--lang', choices=('EN', 'IT'), required=True)
    p.add_argument('--correzioni', type=Path, required=True)
    p.add_argument('--pret-source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args(argv)

    chars, commands = build_charmap(args.pret_source)
    rows = load_rows(args.correzioni, args.lang)
    before_bytes = args.before.read_bytes()
    after_bytes = args.after.read_bytes()

    report, row_reports, problems = compare_roms(before_bytes, after_bytes, args.lang, rows, chars, commands)
    width_report, width_problems = check_widths(before_bytes, after_bytes, rows)
    problems.extend(width_problems)

    outcome_counts = {}
    for r in row_reports:
        outcome_counts[r['esito']] = outcome_counts.get(r['esito'], 0) + 1

    full = {
        'lingua': args.lang,
        'righe_in_perimetro': len(rows),
        'esiti': outcome_counts,
        'confronto_rom': report,
        'righe': row_reports,
        'larghezza': width_report,
        'problemi': problems,
        'ok': not problems,
    }
    args.report.write_text(json.dumps(full, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in full.items() if k != 'righe'}, indent=2, ensure_ascii=False))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
