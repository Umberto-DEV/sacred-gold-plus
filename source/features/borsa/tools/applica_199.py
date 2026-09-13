#!/usr/bin/env python3
"""Applicatore dedicato per il messaggio 199#10 (BORSA-GEN-08, 13 settembre 2026).

PERCHE' NON `applica_testi.py`/`REGOLE.json`
---------------------------------------------
Quella catena riscrive un messaggio GIA' ESISTENTE: `process_bank` in
`source/features/texts/applica_testi.py` rifiuta con `RIFIUTATA_MESSAGGIO_FUORI_BANCO`
qualunque indice fuori da `[0, len(bank.words))`, e non ha alcun percorso per
*aggiungere* un'undicesima voce a un banco che ne ha dieci (`Bank.words` e'
la lista decodificata dalla tabella di allocazione della ROM in ingresso, non
cresce da sola). Il banco 199 non ha oggi un messaggio 10: serve un
applicatore diverso, non una riga in piu' in CORREZIONI.tsv.

COSA FA
-------
1. Legge il banco 199 (`a/0/2/7`, membro 199) dalla ROM.
2. Verifica per hash SHA-256 che i 6 messaggi morti (0,1,2,5,7,8 -- prova di
   irraggiungibilita' in `verifica_irraggiungibilita.py`, tre prove
   indipendenti, tutte verdi) e il messaggio di riferimento vivo 199#3
   abbiano ANCORA il testo atteso: se no, la ROM non e' quella prevista e si
   rifiuta invece di scrivere alla cieca.
3. Tronca i 6 morti a stringa vuota (`[0xFFFF]`, 2 B ciascuno: libera 372 B
   EN / 302 B IT).
4. Aggiunge il messaggio 199#10 (indice nuovo, in coda): NOMINA L'OGGETTO con
   lo stesso segnaposto del riferimento 199#3, `{STRVAR_1:8:1,0}` (sottotipo 8
   = nome oggetto, indice buffer 1, come da `source/translation/message_codec.py`
   e la lettura fatta in `ricognizione.py`). Testo ORIGINALE scritto per
   Sacred Gold Plus (non e' testo retail: nessun problema di ridistribuzione),
   quindi e' scritto qui in chiaro, non tramite REGOLE.json.
5. Il membro deve restare uguale o piu' piccolo dell'originale (stessa regola
   di `applica_testi.py`): qui lo e' con largo margine (EN 170+8=178 B <= 372
   liberati; IT 194+8=202 B <= 302 liberati). Viene riempito di zeri fino alla
   lunghezza originale byte per byte, cosi' `a/0/2/7` non cambia lunghezza e
   `rom_container.append_files(..., reuse_existing=True)` lo riusa in luogo:
   **crescita ROM = 0**.

SOLA LETTURA salvo `--out`: non scrive mai sopra l'ingresso.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'source' / 'translation'))
sys.path.insert(0, str(REPO / 'source' / 'quality-audit'))
sys.path.insert(0, str(REPO / 'source' / 'features' / 'texts'))

from message_codec import Bank, encode_text  # noqa: E402 -- solo il codec, non applica_testi
from rom_container import append_files  # noqa: E402
from applica_testi import load_charmap, decode_text  # noqa: E402 -- charmap condiviso, non logica editoriale
import misura_larghezza as mw  # noqa: E402
import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402

MSG_ARCHIVE = 'a/0/2/7'
FONT_ARCHIVE = 'a/0/1/6'
BANK_199 = 199
MORTI = (0, 1, 2, 5, 7, 8)
RIFERIMENTO_VIVO = 3
PLACEHOLDER = '{STRVAR_1:8:1,0}'
LIMITE_PX_DEFAULT = 216  # stesso default di applica_testi.py/rileggi_testi.py per un banco senza costante propria

# Testo finale di 199#10, ORIGINALE (non retail): definito e misurato in
# testo_finale.py (round-trip OK, 170 B EN / 194 B IT, entro 216 px anche con
# il nome di oggetto piu' lungo di ciascuna lingua sostituito al segnaposto).
TESTO_199_10 = {
    'EN': 'The Bag is full!\\nNo room for the ' + PLACEHOLDER + '.\\rIt was picked up,\\nbut had to be left behind.',
    'IT': 'La Borsa è piena!\\nNon c’è posto per ' + PLACEHOLDER + '.\\rL’oggetto è stato raccolto, ma non\\nè stato possibile conservarlo.',
}

# Ancore SHA-256 (non e' testo di gioco: e' un'impronta) sul testo ATTUALE dei
# 6 morti + del riferimento vivo 199#3, misurate sulle preimmagini EN/IT. Stessa idea
# di REGOLE.json::sha256_attuale: se non combaciano, la ROM in ingresso non e'
# quella attesa e si rifiuta invece di scrivere alla cieca.
ANCORE_SHA256 = {
    'EN': {
        0: '7d51f6314db43b0f9df0e1f284f338eaa0935ee8f69d25f50d0f460ccda283ee',
        1: '4b262d4085e351b0a059077816a22d9f0e02bf67c163309a5f0d0fe1973f0e1c',
        2: '7ea936e500f287294329b88570cc5d118736f5fe0958edf76cff0c04db4d5581',
        5: 'cc9abfc5ea81f84ece2a71f71d8344935ca8bd26f5b4f9d88fcbe37a278965a3',
        7: '5428c4544abff1c81cb5582372420e47db2f82db51b9f245ccba8e6e6327b028',
        8: '67ff96eaf14824a529b4f14f6c8296005bc98db97379924b08fb8459f5a79d26',
        RIFERIMENTO_VIVO: 'ae554d3dd36ced4cfdc505b9e6ed410136997816215cb09b6a51c61ea19dfd9c',
    },
    'IT': {
        0: 'ac21ed1b36292393c18b6a1d549e888b6902cd7b0bcd3d5b985e1f46fc999f59',
        1: '10ef2bb8d168b10feccdedb97a3a11aec1e7e65f1dec18e5f885d8b40ad8ca7c',
        2: '8ec524eeb810521523003b73fe9cf4e9b045f8d85772fba214572ae7748b77cf',
        5: 'de862f1a6efa404fae30976ddd9d26aaeac59694bca75c977ee812d5e821c313',
        7: 'ac21ed1b36292393c18b6a1d549e888b6902cd7b0bcd3d5b985e1f46fc999f59',
        8: 'ac21ed1b36292393c18b6a1d549e888b6902cd7b0bcd3d5b985e1f46fc999f59',
        RIFERIMENTO_VIVO: 'a78e840d217362f4e4c005145aa76a8349c3befbdf3beb2733b4643cd8cbfa2d',
    },
}


class Rifiuto(Exception):
    pass


def applica_bank199_bytes(rom_bytes: bytes, lang: str, pret_source: Path):
    """Nucleo puro: bytes-in / (bytes-out-o-None, rapporto)."""
    chars, commands = load_charmap(pret_source)
    rom = ndspy.rom.NintendoDSRom(rom_bytes)
    msg_raw = rom.getFileByName(MSG_ARCHIVE)
    narc = ndspy.narc.NARC(msg_raw)
    font_narc = ndspy.narc.NARC(rom.getFileByName(FONT_ARCHIVE))
    table = mw.extract_width_table(font_narc.files[0])
    self_check = mw.self_check(table)

    original_member = narc.files[BANK_199]
    bank = Bank(original_member)
    original_len = len(original_member)

    rapporto = {'lingua': lang, 'font_self_check_ok': self_check['ok'],
                'numero_messaggi_prima': len(bank.words)}

    if len(bank.words) == 11:
        testo10, ok10 = decode_text(bank.words[10], chars, commands)
        if ok10 and testo10 == TESTO_199_10[lang]:
            rapporto['esito'] = 'GIA_APPLICATA'
            return None, rapporto
        raise Rifiuto(f'banco 199 ha gia 11 messaggi ma il #10 non e quello atteso: {testo10!r}')
    if len(bank.words) != 10:
        raise Rifiuto(f'banco 199 ha {len(bank.words)} messaggi, attesi 10 (prima) o 11 (gia applicata)')

    # --- verifica delle ancore (morti + riferimento vivo) prima di scrivere
    ancore = ANCORE_SHA256[lang]
    controlli = []
    for idx, sha_atteso in ancore.items():
        testo, ok = decode_text(bank.words[idx], chars, commands)
        sha_trovato = hashlib.sha256(testo.encode('utf-8')).hexdigest()
        combacia = ok and sha_trovato == sha_atteso
        controlli.append({'messaggio': idx, 'ok_decodifica': ok, 'sha_combacia': combacia})
        if not combacia:
            raise Rifiuto(f'199#{idx}: ancora SHA-256 non combacia (sha={sha_trovato}, atteso={sha_atteso}) '
                           '-- la ROM in ingresso non e quella prevista')
    rapporto['ancore_verificate'] = controlli

    # --- tronca i 6 morti a stringa vuota
    for idx in MORTI:
        bank.words[idx] = [0xFFFF]

    # --- codifica e appende 199#10
    nuove_parole = encode_text(TESTO_199_10[lang], chars, commands)
    # cancello di larghezza: il default (216 px, nessuna riga della finestra
    # di dialogo generica del banco 199 e' elencata in BANK_LIMIT_PX di
    # applica_testi.py). Qui, a differenza della misura "a vuoto", basta il
    # segnaposto: la prova col nome di oggetto piu' lungo di ciascuna lingua
    # e' fatta a parte in testo_finale.py (164 px EN / 176 px IT, entrambe
    # entro 216).
    misura = mw.measure(table, nuove_parole, LIMITE_PX_DEFAULT)
    if misura['any_over_limit']:
        raise Rifiuto(f'199#10 (segnaposto vuoto) supera {LIMITE_PX_DEFAULT} px: {misura}')
    bank.words.append(nuove_parole)

    final_raw = bank.save()
    if len(final_raw) > original_len:
        raise Rifiuto(f'banco 199 cresciuto: {len(final_raw)} > {original_len}')
    if len(final_raw) < original_len:
        final_raw = final_raw + b'\x00' * (original_len - len(final_raw))

    narc.files[BANK_199] = final_raw
    new_msg_raw = narc.save()
    if len(new_msg_raw) != len(msg_raw):
        raise Rifiuto(f'a/0/2/7 ha cambiato lunghezza: {len(new_msg_raw)} != {len(msg_raw)}')

    new_rom_bytes, changes = append_files(rom_bytes, {MSG_ARCHIVE: new_msg_raw}, reuse_existing=True)
    if len(new_rom_bytes) != len(rom_bytes):
        raise Rifiuto(f'ROM ha cambiato lunghezza: {len(new_rom_bytes)} != {len(rom_bytes)}')
    for change in changes:
        if not change['reused_extent']:
            raise Rifiuto(f'file rilocato invece di riusato in luogo: {change}')

    rapporto.update({
        'esito': 'APPLICATA',
        'numero_messaggi_dopo': 11,
        'banco199_len_bytes_originale': original_len,
        'byte_199_10': len(nuove_parole) * 2,
        'larghezza_199_10_px_segnaposto_vuoto': misura['max_width_px'],
        'rom_container_changes': changes,
    })
    return new_rom_bytes, rapporto


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rom', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--lang', required=True, choices=('EN', 'IT'))
    ap.add_argument('--pret-source', type=Path,
                    default=Path(__import__('os').environ['SGP_PRET_SOURCE'])
                    if __import__('os').environ.get('SGP_PRET_SOURCE') else None)
    ap.add_argument('--report', required=True, type=Path)
    a = ap.parse_args(argv)
    if a.pret_source is None:
        ap.error('--pret-source oppure SGP_PRET_SOURCE e\' obbligatorio')

    if a.out.exists():
        ap.error(f'{a.out} esiste gia: nessun file viene sovrascritto')

    rom_bytes = a.rom.read_bytes()
    try:
        new_bytes, rapporto = applica_bank199_bytes(rom_bytes, a.lang, a.pret_source)
    except Rifiuto as rej:
        rapporto = {'errore_fatale': str(rej)}
        a.report.write_text(json.dumps(rapporto, indent=2, ensure_ascii=False) + '\n')
        print(json.dumps(rapporto, indent=2, ensure_ascii=False))
        return 2

    if new_bytes is not None:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with a.out.open('xb') as f:
            f.write(new_bytes)
    a.report.write_text(json.dumps(rapporto, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(rapporto, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
