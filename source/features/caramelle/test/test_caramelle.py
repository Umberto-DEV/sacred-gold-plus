#!/usr/bin/env python3
"""SGP-1.2-CARAMELLE-01 — la suite. Gira sull'ARM9 VERO di una ROM patchata.

    SGP_ROM_DIR=<dir con sgp-1.2.2-{EN,IT}.nds> \
        python3 -m unittest discover -s test -v

Ogni caso parte dal sito del gancio 0x02081E96 e legge l'esito dai byte: lo
stato reso, `args->selectedAction`, la sequenza di chiamate native. Nessun caso
consulta il sorgente C.

Gli esiti attesi vengono dal decomp, non da noi:
    PARTY_MENU_STATE_USE_ITEM_SELECT_MON = 4     (include/party_menu.h:36)
    PARTY_MENU_STATE_BEGIN_EXIT          = 0x20  (include/party_menu.h:64)
    PARTY_MENU_ACTION_RETURN_0           = 0     (include/party_menu.h:137)
    PARTY_MENU_ACTION_RETURN_EVO_RARE_CANDY = 9  (include/party_menu.h:146)

GPL-3.0-or-later.
"""
import os
import importlib.util
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import Banco, rom_dir, manifesto, rom_presenti, ROM_NOME, CALLEE  # noqa: E402
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R4,
                               UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP)  # noqa: E402

RESTA = 4
ESCI = 0x20
AZ_0 = 0
AZ_EVO = 9

LINGUE = ("EN", "IT")

ROOT = Path(__file__).resolve().parents[4]
CAPACITY_BUILD = Path(os.environ.get(
    "SGP_CAPACITY_BUILD", ROOT / "source" / "sgp12" / "build" / "capacita_borsa"))


def capacity_bench_class():
    """Load the capacity bench without colliding with this directory's banco.py."""
    path = ROOT / "source" / "features" / "capacita-borsa" / "test" / "banco.py"
    spec = importlib.util.spec_from_file_location("sgp_capacity_integration_bench", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Bench


class CapacityCandyBench:
    """Compose the shipped Candy hook with the shipped expanded-Bag ARM code.

    Bag_GetItemQuantity and Bag_TakeItem are deliberately not stubbed.  They
    execute the candidate ARM9 and reach sgp_cap_pocket through the installed
    native entry hook.  Only UI, Party metadata and item/mon readers outside
    the interaction under test are modelled.
    """
    PM = 0x02300000
    ARGS = 0x02320000
    PARTY = 0x02340000
    SPRITE = 0x02350000
    STACK = 0x023B0000
    STOP = 0x023AF000
    ITEM = 50
    POCKET = 0
    OLD_COUNT = 165
    GANCIO = 0x02081E96
    CAN_USE = 0x0208FD9C
    SUPPORT = (0x0207463C, 0x02074640, 0x0200E9BC, 0x0207DAC4,
               0x0200DD08, 0x02077CE8, 0x02077DAC, 0x0206E540, 0x0201AB0C)

    def __init__(self, path):
        self.b = capacity_bench_class()(path, CAPACITY_BUILD)
        self.b.pockets[self.ITEM] = self.POCKET
        self.level = 99
        self.support_calls = []
        for address in self.SUPPORT:
            self.b.mu.hook_add(UC_HOOK_CODE, self._support, begin=address, end=address)

    def _return(self, value):
        self.b.mu.reg_write(UC_ARM_REG_R0, value)
        self.b.mu.reg_write(UC_ARM_REG_PC, self.b.mu.reg_read(UC_ARM_REG_LR))

    def _support(self, uc, address, size, unused):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        self.support_calls.append((address, r0, r1))
        if address in (0x0207463C, 0x02074640):
            self._return(6)
        elif address == 0x02077CE8:                 # LoadItemDataOrGfx
            self._return(0x022F0000)
        elif address == 0x02077DAC:                 # GetItemAttr_PreloadedItemData
            self._return(1 if r1 in (0x0E, 0x19) else 0)  # party-use, level-up
        elif address == 0x0206E540:                 # GetMonData
            self._return(self.level if r1 == 0xA1 else 0)
        else:
            self._return(0)

    def bag_with_candy(self, index, quantity):
        bag = self.b.bag()
        slot = self.b.call('sgp_cap_slot', bag, self.POCKET, index)
        self.b.mu.mem_write(slot, struct.pack('<HH', self.ITEM, quantity))
        return bag

    def quantity(self, bag):
        return self.b.call(0x02078550, bag, self.ITEM, 12)

    def take_one(self, bag):
        return self.b.call(0x02078434, bag, self.ITEM, 1, 12)

    def candy_tail(self, bag):
        u = self.b.mu
        u.mem_write(self.PM, bytes(0xD00))
        u.mem_write(self.ARGS, bytes(0x50))
        u.mem_write(self.PM + 0x654, struct.pack('<I', self.ARGS))
        u.mem_write(self.PM + 0x678, struct.pack('<I', self.SPRITE))
        u.mem_write(self.ARGS, struct.pack('<II', self.PARTY, bag))
        u.mem_write(self.ARGS + 0x24, bytes([5]))
        u.mem_write(self.ARGS + 0x27, bytes([0xEE]))
        u.mem_write(self.ARGS + 0x28, struct.pack('<H', self.ITEM))
        u.mem_write(self.ARGS + 0x38, struct.pack('<I', 0x7777))
        sp = self.STACK - 16
        u.mem_write(sp, struct.pack('<4I', 0x33333333, 0xC4C4C4C4,
                                    0xC5C5C5C5, self.STOP | 1))
        u.reg_write(UC_ARM_REG_SP, sp)
        u.reg_write(UC_ARM_REG_R0, 0)
        u.reg_write(UC_ARM_REG_R1, self.ARGS)
        u.reg_write(UC_ARM_REG_R4, self.PM)
        u.reg_write(UC_ARM_REG_LR, 0xFFFFFFFF)
        u.emu_start(self.GANCIO | 1, self.STOP, count=20000)
        return (u.reg_read(UC_ARM_REG_R0),
                u.mem_read(self.ARGS + 0x27, 1)[0],
                struct.unpack('<I', u.mem_read(self.ARGS + 0x38, 4))[0])

    def can_use_at_level(self, level):
        self.level = level
        self.support_calls = []
        return self.b.call(self.CAN_USE, 0x022E0000, self.ITEM, 0, 12)


def rom(lingua):
    return rom_dir() / (ROM_NOME % lingua)


MOTIVO = ("classe B: serve $SGP_ROM_DIR con " + ROM_NOME % "{EN,IT}"
          + " (ROM gia' patchate: vedi source/README.md)")


@unittest.skipUnless(rom_presenti(), MOTIVO)
class ProveCaramelle(unittest.TestCase):
    """Ogni prova gira su EN e su IT: gli indirizzi ARM9 statici coincidono
    (RAPPORTO §2), e questa suite è il controllo che continuino a coincidere."""

    def banco(self, lingua):
        return Banco(rom(lingua))

    # -- (i) caso pulito: si resta nel menu ---------------------------------
    def test_i_item_valido_senza_evoluzione_resta_nel_menu(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(species=0, item=50, context=5, slot=0, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], RESTA,
                                 "atteso USE_ITEM_SELECT_MON (4), avuto %#x" % r["stato"])
                self.assertEqual(r["azione"], AZ_0)
                nomi = [c[0] for c in r["chiamate"]]
                self.assertEqual(
                    nomi,
                    ["Bag_GetItemQuantity", "Party_GetCount", "Party_GetCapacity",
                     "ClearFrameAndWindow2", "PartyMenu_PrintMessageOnWindow32",
                     "thunk_Sprite_SetPaletteOverride"],
                    "la sequenza di rientro non è quella di UX105_BAG_Tail")

    def test_i_bis_la_sequenza_di_rientro_ha_gli_argomenti_giusti(self):
        from banco import PM, PM_WIN34, PM_SPR_CURSOR, SPRITE, BAG, PARTY
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                r = b.esegui()
                c = dict((x[0], x) for x in r["chiamate"])
                self.assertEqual(c["Bag_GetItemQuantity"][1], BAG)
                self.assertEqual(c["Bag_GetItemQuantity"][2], 50, "itemId passato")
                self.assertEqual(c["Bag_GetItemQuantity"][3], 12, "heap 12")
                self.assertEqual(c["Party_GetCount"][1], PARTY)
                self.assertEqual(c["ClearFrameAndWindow2"][1], PM + PM_WIN34,
                                 "dev'essere &windows[34]")
                self.assertEqual(c["ClearFrameAndWindow2"][2], 1)
                self.assertEqual(c["PartyMenu_PrintMessageOnWindow32"][1], PM)
                self.assertEqual(c["PartyMenu_PrintMessageOnWindow32"][2], 33,
                                 "msg_0300_00033, «Su quale Pokémon usarlo?»")
                self.assertEqual(c["thunk_Sprite_SetPaletteOverride"][1], SPRITE)
                self.assertEqual(c["thunk_Sprite_SetPaletteOverride"][2], 0)
                self.assertEqual(r["search"], 0,
                                 "levelUpMoveSearchState dev'essere azzerato")

    # -- (ii) itemId == ITEM_NONE: uscita vanilla ---------------------------
    def test_ii_item_none_esce_come_il_vanilla(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(species=0, item=0, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertEqual(r["chiamate"], [],
                                 "con ITEM_NONE non si deve chiamare nulla")

    # -- (iii) evoluzione in coda: uscita vanilla, azione 9 -----------------
    def test_iii_evoluzione_in_coda_esce_con_azione_9(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(species=157, item=50, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_EVO)
                self.assertEqual(r["chiamate"], [])

    # -- (iv) registri callee-saved -----------------------------------------
    def test_iv_callee_saved_preservati(self):
        from banco import PM
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                r = b.esegui_blob()
                self.assertEqual(r["stato"], RESTA)
                self.assertEqual(r["r4"], PM, "r4 non è tornato al chiamante")
                for reg, atteso in CALLEE.items():
                    if reg == UC_ARM_REG_R4:
                        continue
                    self.assertEqual(r["callee"][reg], atteso,
                                     "registro callee-saved %d corrotto" % reg)

    def test_iv_bis_la_pila_torna_al_suo_posto(self):
        from banco import PILA
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                r = b.esegui_blob()
                self.assertEqual(r["sp"], PILA - 64, "sp sbilanciato")

    # -- gli altri cancelli --------------------------------------------------
    def test_g2_contesto_sbagliato_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(context=8)      # REPLACE_MOVE_LEVELUP
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertEqual(r["chiamate"], [])

    def test_g4_scorta_finita_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                b.quantita = 0
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertEqual([c[0] for c in r["chiamate"]],
                                 ["Bag_GetItemQuantity"])

    def test_g5_slot_fuori_squadra_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=7)          # la sentinella PARTY_MON_SELECTION_CONFIRM
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertNotIn("ClearFrameAndWindow2", [c[0] for c in r["chiamate"]])

    def test_g5_slot_oltre_il_conteggio_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=3)
                b.conteggio = 2            # squadra di due
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)

    def test_g5_slot_oltre_la_capienza_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=3)
                b.capienza = 2
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)

    def test_slot_al_limite_resta(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=5)
                b.conteggio = 6
                b.capienza = 6
                r = b.esegui()
                self.assertEqual(r["stato"], RESTA)

    def test_args_nullo_esce_senza_scrivere(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(args_nullo=True, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], 0xEE, "con args nullo non si scrive")

    def test_due_usi_di_fila_rendono_lo_stesso_esito(self):
        """R4 di M: la seconda caramella non deve comportarsi diversamente
        dalla prima. Si esegue due volte senza rifare lo stato."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                uno = b.esegui()
                due = b.esegui()
                self.assertEqual(uno["stato"], RESTA)
                self.assertEqual(due["stato"], RESTA)
                self.assertEqual([c[0] for c in uno["chiamate"]],
                                 [c[0] for c in due["chiamate"]])

    def test_il_gancio_e_una_bl_verso_il_blocco(self):
        """Il blob in ROM è quello del manifesto e il gancio ci punta."""
        m = manifesto()
        self.assertEqual(int(m["simboli"]["sgp_caramelle_gancio"], 16), 0x023DAC01)
        self.assertLessEqual(m["blob"]["byte"], 240)


@unittest.skipUnless(rom_presenti() and (CAPACITY_BUILD / 'manifesto.json').is_file(),
                         MOTIVO + " e build capacita_borsa")
class ProveCaramellaBorsaIntegrate(unittest.TestCase):
    """Real ARM composition: Rare Candy tail -> native Bag -> expanded Bag."""

    def test_ultima_e_non_ultima_da_slot_nativo_ed_extra(self):
        # Pocket 0 has 165 retail cells and 252 Plus cells.  Index 165 is the
        # first cell that cannot exist in the unchanged on-disk Bag.
        for language in LINGUE:
            for index, kind in ((0, 'native'), (CapacityCandyBench.OLD_COUNT, 'extra')):
                for initial, expected_quantity, expected_state in ((2, 1, RESTA),
                                                                   (1, 0, ESCI)):
                    with self.subTest(lingua=language, slot=kind, initial=initial):
                        x = CapacityCandyBench(rom(language))
                        bag = x.bag_with_candy(index, initial)
                        self.assertEqual(x.quantity(bag), initial)
                        self.assertEqual(x.take_one(bag), 1)
                        self.assertEqual(x.quantity(bag), expected_quantity)
                        state, action, search = x.candy_tail(bag)
                        self.assertEqual(state, expected_state)
                        self.assertEqual(action, AZ_0)
                        if expected_state == RESTA:
                            self.assertEqual(search, 0)
                        # A stubbed Bag_GetItemQuantity would invalidate this
                        # integration proof.  The support hook list must not
                        # contain either real Bag API entry.
                        addresses = [call[0] for call in x.support_calls]
                        self.assertNotIn(0x02078550, addresses)
                        self.assertNotIn(0x02078434, addresses)

    def test_predicato_nativo_rifiuta_livello_100_senza_consumare_la_borsa(self):
        # This executes CanUseItemOnPokemon itself.  The PartyMenu caller takes
        # the item only after this predicate succeeds; the reusable-tail hook
        # is downstream and is therefore correctly unreachable at level 100.
        for language in LINGUE:
            with self.subTest(lingua=language):
                x = CapacityCandyBench(rom(language))
                bag = x.bag_with_candy(CapacityCandyBench.OLD_COUNT, 1)
                self.assertEqual(x.can_use_at_level(99), 1)
                self.assertEqual(x.quantity(bag), 1)
                self.assertEqual(x.can_use_at_level(100), 0)
                self.assertEqual(x.quantity(bag), 1)
                attrs = [r1 for address, unused, r1 in x.support_calls
                         if address == 0x02077DAC]
                self.assertIn(0x19, attrs, 'the real LEVEL_UP attribute gate was not reached')
                levels = [r1 for address, unused, r1 in x.support_calls
                          if address == 0x0206E540]
                self.assertIn(0xA1, levels, 'the real MON_DATA_LEVEL read was not reached')


if __name__ == "__main__":
    unittest.main()
