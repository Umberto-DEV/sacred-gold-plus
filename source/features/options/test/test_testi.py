#!/usr/bin/env python3
"""SGP-1.2-OPZIONI-03 — cancello G5: testi, enum e ancore.

Sono i controlli che nessuno esegue a runtime e che per questo si rompono in
silenzio: l'ordine degli id fra C e costruttore, la larghezza in pixel, le
preimmagini dei due ganci. Se l'enum di `sgp_ui.h` e la lista di
`costruisci_testi.py` divergono, la pagina stampa la riga sbagliata e nessun
fotogramma lo rivela subito.
"""
import json
import re
import sys
import unittest
from pathlib import Path

PAC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PAC / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import BUILD                                              # noqa: E402
import costruisci_testi as ct                                        # noqa: E402
from codifica_testo import carica_charmap, codifica                  # noqa: E402

# Le maiuscole NON sono una preferenza: si copiano dall'app Opzioni della stessa
# ROM, lingua per lingua (REVISIONE-QUALITA A3). Prova dentro il pacchetto:
# `fotogrammi/vanilla-{EN,IT}-opzioni.png`, ritagliati dai fotogrammi vanilla.
#   IT  OPZIONI · VELOC. TESTO · SCENA LOTTA · SUONO · PULSANTI · CORNICE
#       valori SI / NO / SCEGLI / FISSO / STEREO / MONO / NORM. / L=A / TIPO 1
#   EN  Options · Text Speed · Battle Scene · Sound · Button Mode · Frame
#       valori Slow / Mid / Fast · On / Off · Shift / Set · Normal / Type 1
# Le chiavi della PAGINA seguono quello schema; la prosa della schermata al
# Continua (`c_riga*`, `c_nota`) resta in tondo in tutte e due le lingue, perche'
# in HGSS le frasi sono in tondo e solo le voci di menu sono maiuscole in IT.
CHIAVI_MENU_IT_MAIUSCOLO = ("p_titolo", "p_aiuto_a", "p_aiuto_b", "p_bloccato",
                            "p_rifiutato", "p_suggerimento",
                            "v0_nome", "v1_nome", "v2_nome", "v3_nome", "v4_nome",
                            "x_off", "x_on", "x_normale", "x_plus",
                            "n_norm", "n_fluido", "w_0", "w_1", "w_2",
                            # v3: anche la riga dei comandi della schermata al
                            # Continua, che nella v2 era in minuscolo e dava due
                            # vocabolari alle due schermate.
                            "c_aiuto")
# `é` di POKéMON e' l'unico minuscolo ammesso in una riga IT maiuscola: e' il
# glifo dedicato che il gioco stesso usa (POKéWALKER nel menu principale).
ECCEZIONI_MINUSCOLE = "é"
# v3: `v3_nome` non e' piu' «FLUIDITA' NPC» ma «PERSONAGGI» (via il gergo «NPC»,
# che in un menu di HGSS non e' mai comparso), quindi non porta piu' l'accento;
# `c_riga2` lo porta al posto suo come riga di prosa accentata da sorvegliare.
ACCENTI_ATTESI = {"IT": {"v0_nome": "À", "x_on": "Ì", "v2_nome": "é"},
                  "EN": {"v2_nome": "é"}}

# v3: parole che in un menu di HGSS non sono mai comparse. Il difetto che questo
# cancello sorveglia e' reale: la v2 spediva «FLUIDITA' NPC» e «NPC Smoothness».
GERGO_VIETATO = ("NPC", "SLOT", "FLAG", "DEBUG", "BETA", "CHUNK", "OVERLAY")


def enum_c():
    s = (PAC / "sorgenti" / "sgp_ui.h").read_text()
    corpo = s[s.index("enum {\n    T_TITOLO"):]
    corpo = corpo[:corpo.index("};")]
    nomi = re.findall(r"\bT_[A-Z0-9_]+\b", corpo)
    return [n for n in nomi if n not in ("T_COUNT",)]


def testi():
    return json.loads((PAC / "testi" / "testi.json").read_text(encoding="utf-8"))["testi"]


def prove():
    return json.loads((PAC / "prove" / "testi.json").read_text(encoding="utf-8"))


class G5Testi(unittest.TestCase):
    def test_enum_C_e_costruttore_hanno_la_stessa_lunghezza(self):
        self.assertEqual(len(enum_c()), len(ct.ORDINE),
                         "l'enum di sgp_ui.h e ORDINE di costruisci_testi.py "
                         "devono avere lo stesso numero di voci")

    def test_nomi_delle_voci_contigui(self):
        e = enum_c()
        i = e.index("T_NOME0")
        self.assertEqual(e[i:i + 5], [f"T_NOME{k}" for k in range(5)])

    def test_i_valori_di_ogni_voce_sono_contigui(self):
        """La pagina stampa `val0 + valore`: se gli id non sono contigui mostra
        l'etichetta di un'altra voce, e nessun test a runtime se ne accorge."""
        idx = {c: i for i, c in enumerate(ct.ORDINE)}
        for nome, primo, nval, _q, _n in ct.VOCI:
            base = idx[primo]
            self.assertLessEqual(base + nval, len(ct.ORDINE), nome)
            attesi = ct.ORDINE[base:base + nval]
            self.assertTrue(all(a.startswith(("x_", "w_", "n_")) for a in attesi),
                            f"{nome}: {attesi} non sono tutte etichette di valore")

    def test_niente_testo_morto(self):
        """A5: la v1 portava nel blob `p_salvato`, `p_aiuto2`, `p_pagina1`,
        `p_pagina2` e sei indicatori `n/6` che nessuna riga disegnava. Qui ogni
        id deve essere usato: o dal C, o dalla tabella delle voci."""
        c = "".join((PAC / "sorgenti" / f).read_text(encoding="utf-8")
                    for f in ("opzioni_pagina.c", "continua_domanda.c", "ui_comune.c"))
        e = enum_c()
        usati_tab = set()
        for _n, primo, nval, _q, _h in ct.VOCI:
            b = ct.ORDINE.index(primo)
            usati_tab.update(e[b:b + nval])
        usati_tab.update(e[ct.ORDINE.index(n)] for n, *_ in ct.VOCI)
        morti = [n for n in e if n not in usati_tab and n not in c]
        self.assertEqual(morti, [], f"id nel blob che nessuno disegna: {morti}")

    def test_ogni_riga_entra_nel_suo_limite(self):
        """Tre limiti diversi, perche' il layout e' diverso: etichetta 114 px,
        valore 44 px, riga piena 166 px, schermata al Continua 224 px."""
        p = prove()
        self.assertEqual(p["fuori_limite"], [])
        for lingua, blocco in p["voci"].items():
            self.assertEqual(set(blocco), set(testi()[lingua]))
            for chiave, v in blocco.items():
                self.assertTrue(v["entro_limite"], f"{lingua}/{chiave}")
                self.assertEqual(v["ignoti"], 0, f"glifo ignoto in {lingua}/{chiave}")

    def test_maiuscole_per_lingua(self):
        """A3. L'italiano del menu Opzioni di HGSS e' tutto maiuscolo; l'inglese
        e' Title Case anche nei valori. La v1 aveva uno schema solo, giusto per
        nessuna delle due."""
        t = testi()
        for chiave in CHIAVI_MENU_IT_MAIUSCOLO:
            v = t["IT"][chiave]
            ripulita = "".join(c for c in v if c not in ECCEZIONI_MINUSCOLE)
            self.assertEqual(ripulita, ripulita.upper(),
                             f"IT/{chiave} = {v!r}: il menu OPZIONI e' maiuscolo")
        for chiave in ("v0_nome", "v1_nome", "v2_nome", "v3_nome", "v4_nome"):
            v = t["EN"][chiave]
            self.assertNotEqual(v, v.upper(),
                                f"EN/{chiave} = {v!r}: il menu Options e' Title Case")
            for parola in v.split():
                self.assertTrue(parola[0].isupper(), f"EN/{chiave}: {parola!r}")
        for chiave in ("x_off", "x_on", "x_normale", "x_plus", "n_norm",
                       "n_fluido", "w_0", "w_1", "w_2"):
            v = t["EN"][chiave]
            self.assertEqual(v, v[0].upper() + v[1:],
                             f"EN/{chiave}: anche i valori sono Title Case")
            self.assertNotEqual(v, v.upper(), f"EN/{chiave} = {v!r}: non maiuscolo")

    def test_accenti_veri(self):
        """A4. La v1 scriveva `Difficolta`, `SI`, `Giu`, `Pokemon`. La charmap del
        gioco ha gli accenti: si aggiungono righe alla charmap, non si rinuncia."""
        t = testi()
        for lingua, attesi in ACCENTI_ATTESI.items():
            for chiave, glifo in attesi.items():
                self.assertIn(glifo, t[lingua][chiave],
                              f"{lingua}/{chiave} deve contenere {glifo!r}")
        self.assertNotIn("SI", t["IT"]["x_on"].replace("SÌ", ""),
                         "il vanilla IT scrive SI' con l'accento")

    def test_niente_gergo_da_sviluppatore(self):
        """v3. «NPC» e «SLOT» sono parole nostre, non del gioco: in nessun menu
        di HGSS compaiono. La v2 le spediva entrambe (FLUIDITA' NPC, SLOT 2)."""
        t = testi()
        for lingua, blocco in t.items():
            for chiave, v in blocco.items():
                for parola in GERGO_VIETATO:
                    self.assertNotIn(parola, v.upper(),
                                     f"{lingua}/{chiave} = {v!r}: {parola!r} e' "
                                     "gergo da sviluppatore, non lessico di HGSS")

    def test_i_due_comandi_della_pagina_sono_due_testi(self):
        """v3. La riga dei comandi e' divisa in due meta' perche' sono i due
        BERSAGLI del tocco (sinistra = A, destra = B): se tornassero una stringa
        sola, la meta' toccabile non sarebbe piu' definita."""
        t = testi()
        for lingua in ("EN", "IT"):
            self.assertIn("p_aiuto_a", t[lingua])
            self.assertIn("p_aiuto_b", t[lingua])
            self.assertTrue(t[lingua]["p_aiuto_a"].upper().startswith("A"))
            self.assertTrue(t[lingua]["p_aiuto_b"].upper().startswith("B"))
        e = enum_c()
        self.assertEqual(e[e.index("T_AIUTO_A") + 1], "T_AIUTO_B")

    def test_niente_numeri_di_versione_nei_valori(self):
        """A6. `(1.2b)` e `(1.3)` in una colonna di valori sono changelog, non
        interfaccia: nessuno sviluppatore ufficiale spedisce un menu cosi'."""
        t = testi()
        for lingua, blocco in t.items():
            for chiave, v in blocco.items():
                if chiave.startswith(("x_", "w_", "n_")):
                    self.assertNotRegex(v, r"\d+\.\d", f"{lingua}/{chiave} = {v!r}")

    def test_la_nota_al_continua_dice_SELECT(self):
        """A7 + §6: e' l'unico punto del gioco in cui la funzione si puo'
        annunciare a costo zero. Senza questa riga SELECT non si scopre."""
        t = testi()
        for lingua in ("EN", "IT"):
            self.assertIn("SELECT", t[lingua]["c_nota"])
            self.assertIn("OP", t[lingua]["c_nota"].upper())

    def test_l_aiuto_dice_che_A_salva_e_B_annulla(self):
        """A2. Su/giu' e sinistra/destra sono ovvi; «B scarta» no, ed era proprio
        la riga che la v1 non disegnava mai."""
        t = testi()
        for lingua in ("EN", "IT"):
            v = (t[lingua]["p_aiuto_a"] + " " + t[lingua]["p_aiuto_b"]).upper()
            self.assertIn("A:", v)
            self.assertIn("B:", v)

    def test_carattere_non_mappato_e_un_errore(self):
        tab, _ = carica_charmap()
        with self.assertRaises(ValueError):
            codifica("ciao§", tab)      # § non e' nella charmap del gioco

    def test_la_charmap_viene_da_pret(self):
        """La tabella ridotta e' un estratto di pret/pokeheartgold e NON e'
        ridistribuita qui (CREDITS.md): si passa `--charmap <pret>/charmap.txt`.
        Quando qualcuno la mette comunque in `testi/`, dev'essere quella."""
        f = PAC / "testi" / "charmap-sgp.tsv"
        if not f.is_file():
            self.skipTest("charmap ridotta assente: e' un ingresso esterno, vedi CREDITS.md")
        riga = f.read_text(encoding="utf-8")
        self.assertIn("pret/pokeheartgold", riga)
        self.assertIn("d010fe01f7a83d29", riga, "sha256 della copia usata")

    def test_blob_coerente_col_manifesto(self):
        for lingua in ("EN", "IT"):
            m = json.loads((BUILD / f"testi-{lingua}.json").read_text(encoding="utf-8"))
            b = (BUILD / f"testi-{lingua}.bin").read_bytes()
            self.assertEqual(len(b), m["testi_byte"])
            self.assertEqual(m["id"], ct.ORDINE)
            n = len(ct.ORDINE)
            offs = [int.from_bytes(b[2 * i:2 * i + 2], "little") for i in range(n)]
            self.assertTrue(all(2 * n <= o < len(b) for o in offs),
                            "ogni offset deve puntare dentro il blob, dopo la testa")
            for o in offs:
                self.assertEqual(len(b[o:]) and b[o:].find(b"\xff\xff") % 2, 0,
                                 "ogni stringa deve terminare su un confine u16")

    def test_il_blob_entra_nel_suo_scomparto(self):
        """Il blob dei testi ha un BLOCCO proprio (`sgp.opzioni.testi`): nei 4096 B
        di `sgp.opzioni` non ci sta insieme al codice, e `sgp.wifi` comincia a
        0x023DA000 con un indirizzo che CONTRATTO-W1 §1b.4 dichiara fermo."""
        import compila
        scomparto = dict(compila.PIANTA_TESTI)["testi"]
        for lingua in ("EN", "IT"):
            b = (BUILD / f"testi-{lingua}.bin").read_bytes()
            self.assertLessEqual(len(b), scomparto,
                                 f"{lingua}: {len(b)} B su {scomparto}")
        self.assertLessEqual(scomparto + 16, compila.BLOCCO_TESTI_BYTE,
                             "il canarino sta in coda al blocco dei testi")

    def test_tabella_voci_coerente(self):
        b = (BUILD / "voci-IT.bin").read_bytes()
        self.assertEqual(len(b), 24, "6 voci da 4 byte (una di scorta)")
        quali = [b[4 * i + 3] & 0x0F for i in range(len(ct.VOCI))]
        self.assertEqual(quali, [q for _n, _v, _nv, q, _h in ct.VOCI])
        nascondi = [(b[4 * i + 3] >> 4) & 1 for i in range(len(ct.VOCI))]
        self.assertEqual(nascondi, [0, 0, 1, 0, 0],
                         "solo la voce di A1-B si nasconde se il cantiere non c'e'")
        nval = [b[4 * i + 2] for i in range(len(ct.VOCI))]
        self.assertEqual(nval, [2, 2, 2, 2, 3],
                         "la voce del Wi-Fi ha tre valori: Originale, slot 2, slot 3 "
                         "(CONTRATTO-W1 §1b.5: lo slot 1 e' del Dono Segreto)")
        for i in range(len(ct.VOCI)):
            self.assertLess(b[4 * i], len(ct.ORDINE))
            self.assertLess(b[4 * i + 1] + b[4 * i + 2] - 1, len(ct.ORDINE))


class G1Ancore(unittest.TestCase):
    def carica(self, nome):
        p = PAC / "prove" / nome
        if not p.is_file():
            self.skipTest(f"{nome} non prodotto: eseguire RIPRODUCI.sh")
        return json.loads(p.read_text())

    def test_preimmagini_e_identita_EN_IT(self):
        a = self.carica("ancore.json")
        self.assertTrue(a["tutte_le_preimmagini_ok"])
        self.assertTrue(a["tutte_identiche"], a["differenze_EN_IT"])

    def test_gancio_opzioni(self):
        a = self.carica("ancore.json")["EN"]
        self.assertEqual(a["A_sito"]["modulo"], "ov054")
        self.assertEqual(a["A_sito"]["ram"], "0x21e6820")
        self.assertEqual(a["A_sito"]["pre"], "041c898c")

    def test_ganci_continua_sono_dati_non_codice(self):
        a = self.carica("ancore.json")["EN"]
        self.assertEqual(a["B_parole"]["literal_gApplication_ContinueFieldsys"]["valore"],
                         "0x20fa16c")
        self.assertEqual(a["B_parole"]["literal_gApplication_NewGameFieldsys"]["valore"],
                         "0x20fa15c")
        self.assertTrue(a["C_dispatch"]["casi"]["CONTINUE"]["ok"],
                        "il template 0x021E5C04 e' davvero il caso CONTINUE")

    def test_simboli_arm9_identici_fra_EN_e_IT(self):
        s = self.carica("simboli-arm9.json")["simboli"]
        non_certi = [k for k, v in s.items() if v["fiducia"] != "certa"]
        self.assertEqual(non_certi, [], "nessun simbolo indovinato")
        diversi = [k for k, v in s.items() if not v["identico"]]
        self.assertEqual(diversi, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
