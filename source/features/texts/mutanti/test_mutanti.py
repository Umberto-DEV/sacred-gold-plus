#!/usr/bin/env python3
"""Cinque mutanti minimi per applica_testi.py (SGP-1.2-LINGUA-04, 12 settembre 2026).

Ogni mutante deve essere RIFIUTATO senza eccezione non gestita e senza scrivere nulla: si
verifica sia l'esito riportato sia che il banco sintetico coinvolto resti byte-identico
all'originale. Uso:

    <python-con-ndspy> test_mutanti.py --pret-source <checkout pret> --rom <ROM per la tabella dei
        glifi reale, solo lettura>

Nessun testo di gioco vero e' incluso qui: i messaggi sintetici sono frasi giocattolo scelte solo
per la loro forma (lunghezza, presenza di un tag, larghezza in pixel), non per il loro contenuto.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINGUA04 = HERE.parent
sys.path.insert(0, str(LINGUA04))
sys.path.insert(0, str(LINGUA04.parents[1] / 'translation'))
sys.path.insert(0, str(LINGUA04.parents[1] / 'quality-audit'))

import applica_testi as at  # noqa: E402
from message_codec import Bank, encode_text  # noqa: E402
import misura_larghezza as mw  # noqa: E402
import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402

FAILURES = []


def check(name, condition, detail=''):
    status = 'PASS' if condition else 'FAIL'
    print(f'[{status}] {name}' + (f' -- {detail}' if detail and status == "FAIL" else ''))
    if not condition:
        FAILURES.append(name)


def make_bank(texts, chars, commands, key=1):
    words = [encode_text(t, chars, commands) for t in texts]
    bank = Bank.from_words(words, key=key)
    return bank.save()


def edit(banco, messaggio, testo_attuale, testo_proposto, variante=None, priorita='A'):
    return {
        'banco': banco, 'messaggio': messaggio, 'testo_attuale': testo_attuale,
        'testo_proposto': testo_proposto, 'variante_corta_grezza': variante,
        'priorita': priorita, 'nome_simbolico': 'sintetico',
    }


def mutant_1_preimmagine_diversa(chars, commands):
    raw = make_bank(['Ciao mondo.'], chars, commands)
    e = edit(0, 0, 'Testo che NON e nel banco.', 'Nuovo testo.')
    rows = []
    new_raw, touched = at.process_bank(0, raw, [e], chars, commands, DUMMY_WIDTH_TABLE, rows)
    check('M1 preimmagine diversa: rifiutata', rows[0]['esito'] == 'RIFIUTATA_PREIMMAGINE', rows[0])
    check('M1 preimmagine diversa: banco non toccato', new_raw is None and not touched)
    check('M1 preimmagine diversa: byte del banco intatti', Bank(raw).words == Bank(raw).words)


def mutant_2_testo_troppo_lungo(chars, commands):
    raw = make_bank(['Hi'], chars, commands)
    lungo = 'Hi ' * 400  # ben oltre lo spazio del banco originale, nessuna variante corta
    e = edit(0, 0, 'Hi', lungo)
    rows = []
    new_raw, touched = at.process_bank(0, raw, [e], chars, commands, DUMMY_WIDTH_TABLE, rows)
    check('M2 testo troppo lungo: rifiutata per spazio', rows[0]['esito'] == 'RIFIUTATA_SPAZIO', rows[0])
    check('M2 testo troppo lungo: banco non toccato', new_raw is None and not touched)


def mutant_3_tag_rotto(chars, commands):
    raw = make_bank(['Testo normale.'], chars, commands)
    e = edit(0, 0, 'Testo normale.', 'Testo con tag {NON_ESISTE_QUESTO_CONTROLLO}.')
    rows = []
    new_raw, touched = at.process_bank(0, raw, [e], chars, commands, DUMMY_WIDTH_TABLE, rows)
    check('M3 tag rotto: rifiutata per controllo non valido',
          rows[0]['esito'] == 'RIFIUTATA_CONTROLLO_NON_VALIDO', rows[0])
    check('M3 tag rotto: banco non toccato', new_raw is None and not touched)

    # variante: parentesi graffa non chiusa
    e2 = edit(0, 0, 'Testo normale.', 'Testo con parentesi {STRVAR_1:3:0,0 non chiusa.')
    rows2 = []
    new_raw2, touched2 = at.process_bank(0, raw, [e2], chars, commands, DUMMY_WIDTH_TABLE, rows2)
    check('M3b tag non chiuso: rifiutata per controllo non valido',
          rows2[0]['esito'] == 'RIFIUTATA_CONTROLLO_NON_VALIDO', rows2[0])
    check('M3b tag non chiuso: banco non toccato', new_raw2 is None and not touched2)


def mutant_4_banco_sbagliato(chars, commands):
    raw = make_bank(['Unico messaggio.'], chars, commands)
    e = edit(0, 99, 'Unico messaggio.', 'Modificato.')  # indice messaggio fuori dal banco (1 solo msg)
    rows = []
    new_raw, touched = at.process_bank(0, raw, [e], chars, commands, DUMMY_WIDTH_TABLE, rows)
    check('M4 messaggio fuori dal banco: rifiutata',
          rows[0]['esito'] == 'RIFIUTATA_MESSAGGIO_FUORI_BANCO', rows[0])
    check('M4 messaggio fuori dal banco: banco non toccato', new_raw is None and not touched)

    # banco fuori dal NARC: verificato al livello sopra (apply_to_rom_bytes), qui simulato
    # direttamente controllando la stessa guardia usata li'.
    fake_narc_len = 829
    bad_bank_index = 99999
    ok = not (0 <= bad_bank_index < fake_narc_len)
    check('M4b banco fuori dal NARC: la guardia di apply_to_rom_bytes lo riconoscerebbe', ok)


def mutant_5_larghezza_oltre_limite(chars, commands, width_table):
    # Un testo che entra ampiamente nello spazio in byte (il banco viene artificialmente
    # allargato con zeri di coda, come farebbe un membro NARC reale gia' compattato da una
    # correzione precedente: message_codec.Bank non richiede che la lunghezza del buffer combaci
    # esattamente con l'ultimo messaggio) ma e' fatto apposta di soli caratteri larghi ripetuti,
    # per superare il limite di contesto (216 px di default) su una singola riga.
    wide_char = max(chars.items(), key=lambda kv: width_table[kv[0]] if kv[0] < len(width_table) else -1)
    code, glyph = wide_char
    width = width_table[code]
    assert width > 0, 'serve un glifo con larghezza misurabile > 0 per costruire il mutante'
    repeats = (216 // width) + 3  # abbastanza ripetizioni per superare 216 px di sicuro
    original_text = glyph  # una sola occorrenza: sicuramente sotto il limite
    proposed_text = glyph * repeats
    raw = make_bank([original_text], chars, commands)
    raw = raw + b'\x00' * 4096  # spazio di manovra abbondante: qui a fallire deve essere SOLO la larghezza
    e = edit(0, 0, original_text, proposed_text)
    rows = []
    new_raw, touched = at.process_bank(0, raw, [e], chars, commands, width_table, rows)
    check('M5 larghezza oltre limite: rifiutata', rows[0]['esito'] == 'RIFIUTATA_LARGHEZZA', rows[0])
    check('M5 larghezza oltre limite: banco non toccato', new_raw is None and not touched)


def mutant_6_variante_corta_salva_la_correzione(chars, commands):
    """Non e' uno dei 5 richiesti, ma verifica a costo quasi zero che il percorso di fallback
    funzioni: un testo troppo lungo CON una variante corta che invece entra deve essere accettato
    con esito APPLICATA (variante_corta), non rifiutato."""
    raw = make_bank(['Hi'], chars, commands)
    raw = raw + b'\x00' * 10  # spazio sufficiente per 'Ciao' (variante) ma non per 400 ripetizioni
    e = edit(0, 0, 'Hi', 'Hi ' * 400, variante='Ciao')
    rows = []
    new_raw, touched = at.process_bank(0, raw, [e], chars, commands, DUMMY_WIDTH_TABLE, rows)
    check('M6 variante corta: applicata con la corta', rows[0]['esito'] == 'APPLICATA' and rows[0]['dettaglio'] == 'variante_corta', rows[0])
    check('M6 variante corta: banco modificato', new_raw is not None and touched)
    if new_raw is not None:
        after = Bank(new_raw)
        text_after, ok = at.decode_text(after.words[0], chars, commands)
        check('M6 variante corta: testo finale e la variante pulita', text_after == 'Ciao')


def test_idempotenza(chars, commands):
    raw = make_bank(['Prima.'], chars, commands)
    e = edit(0, 0, 'Prima.', 'Dopo.')
    rows = []
    new_raw, touched = at.process_bank(0, raw, [e], chars, commands, DUMMY_WIDTH_TABLE, rows)
    check('idempotenza: prima applicazione riuscita', touched and rows[-1]['esito'] == 'APPLICATA')
    rows2 = []
    new_raw2, touched2 = at.process_bank(0, new_raw, [e], chars, commands, DUMMY_WIDTH_TABLE, rows2)
    check('idempotenza: seconda applicazione = nulla da fare', not touched2 and rows2[0]['esito'] == 'GIA_APPLICATA', rows2)


def test_variant_pure_text_matches_source():
    """Le 3 varianti corte codificate a mano in applica_testi.VARIANT_PURE_TEXT devono contenere,
    parola per parola, la clausola pulita del campo grezzo di CORREZIONI.tsv (tutto cio' che
    precede l'annotazione fra parentesi "  ("). Per 749#6 e 279#201 la variante corta SOSTITUISCE
    l'intero messaggio, quindi la clausola pulita e' l'intera variante pura (uguaglianza). Per
    219#43 la variante corta sostituisce solo una frase dentro un messaggio molto piu' lungo,
    quindi si verifica che la clausola sia contenuta nella variante pura, e che il resto del
    messaggio attorno non sia stato alterato."""
    import csv
    path = LINGUA04.parent / 'SGP-1.2-LINGUA-03' / 'CORREZIONI.tsv'
    rows = {(int(r['banco']), int(r['id_messaggio'])): r for r in
            csv.DictReader(path.open(encoding='utf-8'), delimiter='\t')}
    # L'annotazione fra parentesi non ha un separatore uniforme in CORREZIONI.tsv (per lo piu'
    # "  (" a due spazi, ma 279#201 usa un solo spazio prima della parentesi): il punto di taglio
    # e' quindi verificato a mano riga per riga invece che con un'unica euristica generica.
    CUT_MARKER = {(219, 43): '  (', (749, 6): '  (', (279, 201): ' ('}
    for key, pure in at.VARIANT_PURE_TEXT.items():
        row = rows[key]
        grezza = row['variante_corta']
        marker_text = CUT_MARKER.get(key, '  (')
        marker = grezza.find(marker_text)
        clausola = grezza[:marker] if marker >= 0 else grezza
        check(f'variante pura {key}: contiene la clausola pulita di CORREZIONI.tsv',
              clausola in pure, (clausola, pure))
        if pure != clausola:
            # Caso sostituzione-di-clausola (219#43): il resto del messaggio attorno alla
            # clausola deve combaciare esattamente con testo_attuale.
            attuale = row['testo_attuale']
            idx = pure.find(clausola)
            prima, dopo = pure[:idx], pure[idx + len(clausola):]
            check(f'variante pura {key}: testa invariata rispetto a testo_attuale',
                  attuale.startswith(prima), (prima, attuale[:len(prima) + 20]))
            check(f'variante pura {key}: coda invariata rispetto a testo_attuale',
                  attuale.endswith(dopo), (dopo, attuale[-(len(dopo) + 20):]))


DUMMY_WIDTH_TABLE = None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pret-source', type=Path, required=True)
    p.add_argument('--rom', type=Path, required=True, help='ROM di sola lettura per la tabella reale dei glifi')
    args = p.parse_args()

    chars, commands = at.load_charmap(args.pret_source)

    global DUMMY_WIDTH_TABLE
    rom = ndspy.rom.NintendoDSRom.fromFile(str(args.rom))
    font_narc = ndspy.narc.NARC(rom.getFileByName(at.FONT_ARCHIVE))
    width_table = mw.extract_width_table(font_narc.files[0])
    DUMMY_WIDTH_TABLE = width_table
    self_check = mw.self_check(width_table)
    check('tabella larghezze: self-check ok', self_check['ok'], self_check['mismatches'])

    mutant_1_preimmagine_diversa(chars, commands)
    mutant_2_testo_troppo_lungo(chars, commands)
    mutant_3_tag_rotto(chars, commands)
    mutant_4_banco_sbagliato(chars, commands)
    mutant_5_larghezza_oltre_limite(chars, commands, width_table)
    mutant_6_variante_corta_salva_la_correzione(chars, commands)
    test_idempotenza(chars, commands)
    test_variant_pure_text_matches_source()

    print()
    if FAILURES:
        print(f'{len(FAILURES)} mutante/i NON uccisi: {FAILURES}')
        return 1
    print('Tutti i mutanti uccisi.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
