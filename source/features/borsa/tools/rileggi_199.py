#!/usr/bin/env python3
"""Rilettore INDIPENDENTE di `applica_199.py` (BORSA-GEN-08, Classe B).

Non importa nulla da `applica_199.py`: condivide solo il codec byte-esatto
`message_codec.Bank` (dato, non logica editoriale), esattamente come
`source/features/texts/rileggi_testi.py` fa con `applica_testi.py`. Il testo
atteso di 199#10 e la lista dei 6 morti sono riscritti qui una seconda volta,
cosi' un bug logico nell'applicatore non si nasconderebbe dietro lo stesso
codice riusato dal suo stesso rilettore.

Verifica, dati una ROM "prima" e una "dopo":
  1. ogni file della ROM diverso da `a/0/2/7` e' byte-identico;
  2. `a/0/2/7` ha la stessa lunghezza totale prima/dopo;
  3. dentro `a/0/2/7`, ogni banco DIVERSO da 199 e' byte-identico;
  4. il banco 199 decodificato "dopo" ha ESATTAMENTE 11 messaggi:
     - i 6 morti (0,1,2,5,7,8) sono vuoti/troncati (`[0xFFFF]`);
     - il nuovo 199#10 e' esattamente il testo atteso;
     - i 4 vivi originali (3,4,6,9) sono byte-identici prima/dopo (nessuno
       li ha toccati);
  5. il membro 199 "dopo" ha la stessa lunghezza (in byte) del membro 199
     "prima" (il riempimento di zeri della regola «mai crescere»).

SOLA LETTURA. Nessun testo di gioco RETAIL e' scritto qui; il testo di 199#10
e' testo ORIGINALE Sacred Gold Plus (non e' testo del gioco base), riscritto
qui indipendentemente da `applica_199.py`.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'source' / 'translation'))
sys.path.insert(0, str(REPO / 'source' / 'quality-audit'))
sys.path.insert(0, str(REPO / 'source' / 'features' / 'texts'))

from message_codec import Bank  # noqa: E402 -- unico modulo condiviso con l'applicatore
import misura_larghezza as mw  # noqa: E402
import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402

MSG_ARCHIVE = 'a/0/2/7'
FONT_ARCHIVE = 'a/0/1/6'
BANK_199 = 199
MORTI = (0, 1, 2, 5, 7, 8)
VIVI_ORIGINALI = (3, 4, 6, 9)
LIMITE_PX_DEFAULT = 216
PLACEHOLDER = '{STRVAR_1:8:1,0}'

# Riscritto qui, non importato: stessa idea di VARIANT_PURE_TEXT in
# rileggi_testi.py, per indipendenza dal file che lo applica.
TESTO_199_10_ATTESO = {
    'EN': 'The Bag is full!\\nNo room for the ' + PLACEHOLDER + '.\\rIt was picked up,\\nbut had to be left behind.',
    'IT': 'La Borsa è piena!\\nNon c’è posto per ' + PLACEHOLDER + '.\\rL’oggetto è stato raccolto, ma non\\nè stato possibile conservarlo.',
}


def build_charmap(pret_source: Path):
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
    tokens, problems, pos, end = [], 0, 0, len(words)
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


def rileggi_bytes(before_bytes: bytes, after_bytes: bytes, lang: str,
                   pret_source: Path) -> dict:
    if lang not in TESTO_199_10_ATTESO:
        raise ValueError('lingua non supportata: %r' % lang)
    chars, commands = build_charmap(Path(pret_source))
    before_rom = ndspy.rom.NintendoDSRom(before_bytes)
    after_rom = ndspy.rom.NintendoDSRom(after_bytes)

    problemi = []
    rapporto = {'lingua': lang, 'rom_len_before': len(before_bytes), 'rom_len_after': len(after_bytes)}

    if repr(before_rom.filenames) != repr(after_rom.filenames):
        problemi.append('ALBERO_NITROFS_CAMBIATO')
    if len(before_rom.files) != len(after_rom.files):
        problemi.append('NUMERO_FILE_CAMBIATO')

    msg_index = before_rom.filenames.idOf(MSG_ARCHIVE)
    altri_diversi = [i for i in range(min(len(before_rom.files), len(after_rom.files)))
                      if i != msg_index and before_rom.files[i] != after_rom.files[i]]
    rapporto['altri_file_diversi'] = altri_diversi
    if altri_diversi:
        problemi.append('FILE_NON_a027_MODIFICATO')

    msg_before = before_rom.getFileByName(MSG_ARCHIVE)
    msg_after = after_rom.getFileByName(MSG_ARCHIVE)
    rapporto['a027_len_before'] = len(msg_before)
    rapporto['a027_len_after'] = len(msg_after)
    if len(msg_before) != len(msg_after):
        problemi.append('a027_LUNGHEZZA_CAMBIATA')

    narc_before = ndspy.narc.NARC(msg_before)
    narc_after = ndspy.narc.NARC(msg_after)
    if len(narc_before.files) != len(narc_after.files):
        problemi.append('NUMERO_BANCHI_CAMBIATO')

    banchi_diversi = [i for i in range(min(len(narc_before.files), len(narc_after.files)))
                       if i != BANK_199 and narc_before.files[i] != narc_after.files[i]]
    rapporto['banchi_non_199_diversi'] = banchi_diversi
    if banchi_diversi:
        problemi.append('BANCO_NON_199_MODIFICATO')

    rapporto['banco199_len_before'] = len(narc_before.files[BANK_199])
    rapporto['banco199_len_after'] = len(narc_after.files[BANK_199])
    if len(narc_before.files[BANK_199]) != len(narc_after.files[BANK_199]):
        problemi.append('BANCO199_LUNGHEZZA_CAMBIATA')

    try:
        bank_before = Bank(narc_before.files[BANK_199])
        bank_after = Bank(narc_after.files[BANK_199])
    except ValueError as exc:
        problemi.append(f'BANCO199_NON_DECODIFICABILE: {exc}')
        rapporto['problemi'] = problemi
        rapporto['ok'] = False
        return rapporto

    rapporto['numero_messaggi_before'] = len(bank_before.words)
    rapporto['numero_messaggi_after'] = len(bank_after.words)
    if len(bank_before.words) != 10:
        problemi.append(f'BANCO199_PRIMA_NON_10_MESSAGGI_{len(bank_before.words)}')
    if len(bank_after.words) != 11:
        problemi.append(f'BANCO199_DOPO_NON_11_MESSAGGI_{len(bank_after.words)}')

    # --- i 6 morti: vuoti/troncati dopo
    dettaglio_morti = []
    for idx in MORTI:
        if idx >= len(bank_after.words):
            problemi.append(f'MORTO_{idx}_ASSENTE')
            continue
        parole = bank_after.words[idx]
        vuoto = parole == [0xFFFF]
        dettaglio_morti.append({'messaggio': idx, 'vuoto': vuoto, 'n_parole': len(parole)})
        if not vuoto:
            problemi.append(f'MORTO_{idx}_NON_VUOTO')
    rapporto['morti'] = dettaglio_morti

    # --- i 4 vivi originali: identici prima/dopo
    dettaglio_vivi = []
    for idx in VIVI_ORIGINALI:
        identico = (idx < len(bank_before.words) and idx < len(bank_after.words)
                    and bank_before.words[idx] == bank_after.words[idx])
        dettaglio_vivi.append({'messaggio': idx, 'identico': identico})
        if not identico:
            problemi.append(f'VIVO_{idx}_MODIFICATO')
    rapporto['vivi_originali'] = dettaglio_vivi

    # --- 199#10: testo esatto atteso
    if len(bank_after.words) > 10:
        testo10, ok10 = words_to_text(bank_after.words[10], chars, commands)
        atteso = TESTO_199_10_ATTESO[lang]
        rapporto['messaggio_10'] = {'ok_decodifica': ok10, 'testo_combacia': ok10 and testo10 == atteso}
        if not (ok10 and testo10 == atteso):
            problemi.append('MESSAGGIO_10_INATTESO')
            rapporto['messaggio_10']['testo_trovato'] = testo10
    else:
        problemi.append('MESSAGGIO_10_ASSENTE')

    # --- larghezza di 199#10 (segnaposto vuoto; col nome piu' lungo e'
    # verificato a parte da testo_finale.py, che e' la prova indipendente
    # sul font/larghezza reale con un oggetto vero)
    font_narc = ndspy.narc.NARC(after_rom.getFileByName(FONT_ARCHIVE))
    table = mw.extract_width_table(font_narc.files[0])
    check = mw.self_check(table)
    rapporto['font_self_check_ok'] = check['ok']
    if len(bank_after.words) > 10:
        misura = mw.measure(table, bank_after.words[10], LIMITE_PX_DEFAULT)
        rapporto['larghezza_199_10'] = misura
        if misura['any_over_limit']:
            problemi.append('MESSAGGIO_10_OLTRE_LIMITE_LARGHEZZA')

    rapporto['problemi'] = problemi
    rapporto['ok'] = not problemi
    return rapporto


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--before', required=True, type=Path)
    ap.add_argument('--after', required=True, type=Path)
    ap.add_argument('--lang', required=True, choices=('EN', 'IT'))
    ap.add_argument('--pret-source', type=Path,
                    default=Path(__import__('os').environ['SGP_PRET_SOURCE'])
                    if __import__('os').environ.get('SGP_PRET_SOURCE') else None)
    ap.add_argument('--report', required=True, type=Path)
    a = ap.parse_args(argv)
    if a.pret_source is None:
        ap.error('--pret-source oppure SGP_PRET_SOURCE e\' obbligatorio')
    rapporto = rileggi_bytes(a.before.read_bytes(), a.after.read_bytes(),
                             a.lang, a.pret_source)
    a.report.write_text(json.dumps(rapporto, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(rapporto, indent=2, ensure_ascii=False))
    return 0 if rapporto['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
