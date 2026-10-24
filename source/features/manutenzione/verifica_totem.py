#!/usr/bin/env python3
"""Due controlli del totem di Aranciopoli, senza eseguire il gioco.

Uso: .venv/bin/python3 -B source/features/manutenzione/verifica_totem.py
     [--rom ROM.nds ...] [--pret directory]

Legge a streaming i soli membri 776/51/483; non scrive file e non stampa
testi, bytecode o byte della ROM. Riusa il disassemblatore del progetto.
Test 1: struttura e percorsi A -> rinuncia/assenza oggetto/inizio lotta.
Test 2: parametri WildBattle e continuazione dello script per sei esiti.

Le attese asincrone vengono assunte completate nel cammino dello script.
Non esegue codice ARM né verifica scheduler, GPU, audio, heap, salvataggio, cheat o motore
di battaglia: un PASS non riproduce e non esclude il freeze reale.
I flag vengono seguiti come effetti del bytecode, non dichiarati sicuri:
quelli fuori SaveVarsFlags producono un WARNING. L'alias PalPad riportato
deriva dall'ispezione separata dei binari 1.2.3 EN/IT, non da questa corsa.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'source/features/borsa/tools'),
                str(ROOT / 'source/translation'),
                str(ROOT / 'source/quality-audit')]
import ndspy.fnt
import scr_disasm as SD
from message_codec import Bank
from hgss_text import load_charmap, render


class CheckError(ValueError):
    """Messaggio diagnostico senza contenuto estratto."""


def require(condition, message):
    if not condition:
        raise CheckError(message)


def flag_warnings(flag_ids):
    outside = sorted(flag for flag in set(flag_ids) if 2912 <= flag < 0x4000)
    if not outside:
        return []
    aliases = {0x3FAF: 'SavePalPad+0xD9, bit7', 0x3FCA: 'SavePalPad+0xDD, bit2'}
    return [dict(
        livello='WARNING', codice='FLAG_FUORI_SAVEVARSFLAGS',
        flag=[hex(flag) for flag in outside],
        alias_osservati={hex(flag): aliases[flag] for flag in outside if flag in aliases},
        evidenza='Ispezione statica separata di ARM9 1.2.3 EN/IT: GetFlagAddr 0x0205045C, '
                 'limite2912 e sizeof SaveVarsFlags0x44C invariati; tabella save0x020F64C4. '
                 'Nessuna rimappatura nella catena SetFlag esaminata.',
        limite='Questo comando non ricontrolla ARM9. Alias validi per i binari esaminati; '
               'riuso legacy intenzionale del PalPad possibile ma non dimostrato. '
               'La simulazione verifica i rami che emettono i flag, non la sicurezza '
               'della scrittura; nessun nesso causale con il freeze dimostrato.')]


class NitroReader:
    """FNT/FAT piccoli; nessuna lettura integrale di ROM o NARC."""
    def __init__(self, stream):
        self.stream = stream
        stream.seek(0, 2)
        self.size = stream.tell()
        self.largest_read = 0
        header = self.read(0, 0x200)
        fnt, fnt_size, fat, fat_size = struct.unpack_from('<4I', header, 0x40)
        self.names = ndspy.fnt.load(self.read(fnt, fnt_size))
        self.fat = self.read(fat, fat_size)

    def read(self, offset, size):
        require(0 <= offset <= self.size and 0 <= size <= 8 * 1024 * 1024
                and offset + size <= self.size, 'lettura fuori limiti')
        self.largest_read = max(self.largest_read, size)
        self.stream.seek(offset)
        result = self.stream.read(size)
        require(len(result) == size, 'lettura troncata')
        return result

    def member(self, name, index):
        file_id = self.names.idOf(name)
        require(file_id is not None and 8 * file_id + 8 <= len(self.fat),
                'file NitroFS assente')
        start, end = struct.unpack_from('<II', self.fat, file_id * 8)
        require(start < end <= self.size, 'FAT fuori limiti')
        head = self.read(start, 16)
        require(head[:4] == b'NARC', 'NARC assente')
        declared, header_size, chunks = struct.unpack_from('<IHH', head, 8)
        require(header_size >= 16 and declared <= end - start, 'header NARC invalido')
        pos = start + header_size
        member_range = None
        for _ in range(chunks):
            tag, size = struct.unpack('<4sI', self.read(pos, 8))
            require(size >= 8 and pos + size <= start + declared, 'blocco NARC invalido')
            if tag == b'BTAF':
                count = struct.unpack('<H', self.read(pos + 8, 2))[0]
                require(0 <= index < count and 12 + count * 8 <= size,
                        'membro NARC fuori tabella')
                member_range = struct.unpack('<II', self.read(pos + 12 + index * 8, 8))
            elif tag == b'GMIF':
                require(member_range is not None, 'GMIF prima della tabella')
                lo, hi = member_range
                require(0 <= lo <= hi <= size - 8, 'membro NARC fuori dati')
                return self.read(pos + 8 + lo, hi - lo)
            pos += size
        raise CheckError('blocco dati NARC assente')


@dataclass
class Fixture:
    script: bytes
    objects: dict
    messages: list
    cmds: object
    chars: dict
    controls: dict
    largest_read: int


def load_fixture(rom, pret):
    with Path(rom).open('rb') as stream:
        reader = NitroReader(stream)
        script = reader.member('a/0/1/2', 776)
        events = reader.member('a/0/3/2', 51)
        messages = Bank(reader.member('a/0/2/7', 483)).words
    require(len(events) <= 0x800, 'eventi oltre buffer nativo')
    bg_count = struct.unpack_from('<I', events)[0]
    offset = 4 + bg_count * 20
    require(offset + 4 <= len(events), 'eventi troncati')
    count = struct.unpack_from('<I', events, offset)[0]
    offset += 4
    require(offset + count * 32 <= len(events), 'oggetti troncati')
    objects = {}
    for i in range(count):
        v = struct.unpack_from('<6Hh3HhhHHi', events, offset + 32 * i)
        require(v[0] not in objects, 'id oggetto duplicato')
        objects[v[0]] = dict(sprite=v[1], movement=v[2], type=v[3], flag=v[4],
                             script=v[5], facing=v[6], x=v[12], z=v[13], y=v[14])
    chars, controls = load_charmap(Path(pret) / 'charmap.txt')
    return Fixture(script, objects, messages,
                   SD.Comandi(Path(pret) / 'tools/py_scripts/scrcmd.json'),
                   chars, controls, reader.largest_read)


def decode(fixture):
    member = SD.Membro(776, fixture.script, fixture.cmds).cammina()
    require(member.header_valido and len(member.entry) >= 16, 'entry16 assente')
    require(not member.errori, 'bytecode o destinazione non decodificabile')
    require(member.riassembla()[0], 'round-trip decoder fallito')
    occupied = set()
    for ins in member.istruzioni.values():
        region = set(range(ins.off, ins.fine))
        require(not occupied.intersection(region), 'salto dentro istruzione')
        occupied.update(region)
    return member


def reachable(member):
    pending, seen = [member.entry[15]], set()
    while pending:
        pc = pending.pop()
        if pc in seen:
            continue
        require(pc in member.istruzioni, 'percorso senza istruzione valida')
        seen.add(pc)
        ins = member.istruzioni[pc]
        pending.extend(dest for _, dest, kind in ins.rami if kind != 'movement')
        if ins.nome not in ('End', 'Return', 'GoTo'):
            pending.append(ins.fine)
    return seen


PASSIVE = {'Nop', 'PlaySE', 'StopBGM', 'PlayBGM', 'WaitSE', 'FacePlayer',
           'WaitButton', 'CloseMsg', 'TouchscreenMenuHide', 'TouchscreenMenuShow',
           'FadeScreen', 'WaitFade', 'PlayCry', 'WaitCry'}


def simulate(fixture, member, *, item, choice, version, outcome=1, stop_at_battle=False):
    """Interpreta SOLO controllo di flusso; nessun effetto nativo e' eseguito."""
    pc, variables, stack, seen = member.entry[15], {}, [], []
    locked, comparison, battle, whiteout = False, None, None, False
    flags, hidden, messages = set(), set(), []
    for _ in range(1024):
        require(pc in member.istruzioni, 'PC non valido nella simulazione')
        ins = member.istruzioni[pc]
        seen.append(pc)
        name, args, next_pc = ins.nome, ins.args, ins.fine
        target = ins.rami[0][1] if ins.rami else None
        if name == 'LockAll':
            locked = True
        elif name == 'ReleaseAll':
            locked = False
        elif name == 'HasItem':
            require(args[:2] == [225, 1], 'requisito oggetto inatteso')
            variables[args[-1]] = int(item)
        elif name == 'GetMenuChoice':
            variables[args[0]] = choice
        elif name == 'GetGameVersion':
            variables[args[0]] = version
        elif name == 'CompareVarToValue':
            require(args[0] in variables, 'variabile letta senza origine modellata')
            left, right = variables[args[0]], args[1]
            comparison = (left > right) - (left < right)
        elif name in ('GoToIf', 'CallIf'):
            require(comparison is not None and 0 <= args[0] <= 5, 'confronto non valido')
            truth = (comparison < 0, comparison == 0, comparison > 0,
                     comparison <= 0, comparison >= 0, comparison != 0)[args[0]]
            if truth:
                if name == 'CallIf':
                    stack.append(next_pc)
                next_pc = target
        elif name == 'GoTo':
            next_pc = target
        elif name == 'Return':
            require(bool(stack), 'Return senza Call')
            next_pc = stack.pop()
        elif name == 'NPCMsg':
            require(args[0] < len(fixture.messages), 'indice messaggio fuori banco')
            messages.append(args[0])
        elif name in ('HidePerson', 'MovePersonFacing', 'ApplyMovement'):
            require(args[0] in fixture.objects, 'oggetto riferito assente dagli eventi')
            if name == 'HidePerson':
                hidden.add(args[0])
            else:
                require(args[0] not in hidden, 'operazione su oggetto gia rimosso')
        elif name == 'WildBattle':
            require(battle is None, 'due battaglie sullo stesso percorso')
            require(1 <= args[0] <= 493 and 1 <= args[1] <= 100 and args[2] in (0, 1),
                    'specie/livello/shiny WildBattle non validi')
            battle = dict(specie=args[0], livello=args[1], forza_shiny=bool(args[2]))
            if stop_at_battle:
                return dict(battle=battle, locked=locked, seen=seen, messages=messages)
        elif name == 'CheckBattleWon':
            require(battle is not None, 'esito richiesto prima della battaglia')
            variables[args[0]] = int(outcome not in (2, 3))
        elif name == 'GetStaticEncounterOutcome':
            require(battle is not None, 'esito richiesto prima della battaglia')
            variables[args[0]] = outcome
        elif name == 'SetFlag':
            flags.add(args[0])
        elif name == 'WhiteOut':
            whiteout = True
        elif name == 'End':
            require(not stack, 'End con chiamata aperta')
            require(not locked, 'uscita senza ReleaseAll')
            return dict(battle=battle, locked=locked, seen=seen, messages=messages,
                        flags=flags, hidden=hidden, whiteout=whiteout)
        elif name not in PASSIVE:
            raise CheckError('comando non modellato: ' + name)
        pc = next_pc
    raise CheckError('ciclo o percorso oltre budget1024')


def verify_start(fixture):
    report = dict(test='1_A_fino_avvio', errori=[], avvisi=[], scenari_controllati=0)
    try:
        member = decode(fixture)
        nodes = reachable(member)
        require(20 in fixture.objects and fixture.objects[20]['script'] == 16,
                'totem non associato a entry16')
        report['avvisi'] = flag_warnings([fixture.objects[20]['flag']])
        for pc in nodes:
            ins = member.istruzioni[pc]
            if ins.nome in ('HidePerson', 'MovePersonFacing', 'ApplyMovement'):
                require(ins.args[0] in fixture.objects, 'oggetto riferito assente dagli eventi')
            if ins.nome == 'NPCMsg':
                index = ins.args[0]
                require(index < len(fixture.messages), 'indice messaggio fuori banco')
                words = fixture.messages[index]
                metadata = render(words, fixture.chars, fixture.controls)
                require(len(words) < 1024 and not metadata['unknown_codes']
                        and not metadata['malformed_controls'], 'messaggio strutturalmente invalido')
                require(not any((cmd & 0xFF00) in (0x100, 0x300, 0x400, 0x3400)
                                for cmd, _ in metadata['controls']),
                        'placeholder richiede un modello aggiuntivo')
            if ins.nome == 'ApplyMovement':
                offset = ins.rami[0][1]
                for _ in range(128):
                    require(offset + 4 <= len(fixture.script), 'movimento fuori membro')
                    action, repetitions = struct.unpack_from('<HH', fixture.script, offset)
                    if action == 0xFE:
                        break
                    require(action == 33 and repetitions > 0, 'movimento non coperto dal contratto')
                    offset += 4
                else:
                    raise CheckError('movimento senza terminatore')
        covered = set()
        for version in (7, 8):
            for item, choice in ((False, 0), (True, 1), (True, 0)):
                result = simulate(fixture, member, item=item, choice=choice,
                                  version=version, stop_at_battle=True)
                require((result['battle'] is not None) == (item and choice == 0),
                        'requisito o rinuncia non rispettato')
                require(result['messages'] and result['messages'][0] == 26,
                        'primo messaggio inatteso')
                covered.update(result['seen'])
                report['scenari_controllati'] += 1
        report.update(istruzioni_raggiungibili=len(nodes), istruzioni_pre_lotta=len(covered),
                      messaggio_iniziale=26, oggetti=sorted({20, 21, 22}),
                      attese='assunte completate; LockAll puo restare pendente senza timeout')
    except (CheckError, IndexError, struct.error) as exc:
        report['errori'].append(str(exc))
    report['esito'] = 'FAIL' if report['errori'] else 'PASS_CONTRATTO'
    return report


def verify_battle(fixture):
    report = dict(test='2_lotta_e_uscita', errori=[], avvisi=[], esiti_controllati=0)
    try:
        member = decode(fixture)
        report['avvisi'] = flag_warnings(
            member.istruzioni[pc].args[0] for pc in reachable(member)
            if member.istruzioni[pc].nome == 'SetFlag')
        covered = set()
        for version, species, object_id in ((7, 381, 22), (8, 380, 21)):
            for outcome in range(1, 7):
                result = simulate(fixture, member, item=True, choice=0,
                                  version=version, outcome=outcome)
                require(result['battle'] == dict(specie=species, livello=40, forza_shiny=False),
                        'parametri della battaglia inattesi')
                require(result['whiteout'] == (outcome in (2, 3)), 'WhiteOut sull esito errato')
                require((0x3FAF in result['flags']) == (outcome == 4),
                        'emissione flag cattura sul ramo inatteso')
                if outcome not in (2, 3):
                    require(0x3FCA in result['flags'] and object_id in result['hidden'],
                            'chiusura evento incompleta')
                covered.update(result['seen'])
                report['esiti_controllati'] += 1
        report.update(istruzioni_coperte=len(covered),
                      wild_battle=dict(specie=[381, 380], livello=40, forma=0,
                                       forza_shiny=False, battle_type=0, battle_special_bit=8),
                      esiti=['vittoria', 'sconfitta', 'pareggio', 'cattura',
                             'fuga_giocatore', 'fuga_nemico'],
                      uscita='ReleaseAll/End su tutti i sei esiti; WhiteOut su sconfitta/pareggio',
                      durante='Task_StartBattle attende ApplicationIsRunning=false; motore NON eseguito',
                      modello_attesa_lotta='app attiva: sospeso; app terminata: continuazione',
                      contratto_motore='pret: scrcmd_c.c WildBattle; encounter.c SetupAndStartWildBattle/Task_StartEncounter/Task_StartBattle; battle_setup.c IsBattleResultWin',
                      limite_motore='contratto lotta derivato dal sorgente pret; questo comando non esegue ne confronta ARM. '
                                    'La distinta ispezione nativa dei flag e descritta negli avvisi.',
                      forma='0: generatore nativo e specie Latios/Latias senza forme alternative')
    except (CheckError, IndexError, struct.error) as exc:
        report['errori'].append(str(exc))
    report['esito'] = 'FAIL' if report['errori'] else 'PASS_CONTRATTO'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, action='append')
    parser.add_argument('--pret', type=Path, default=ROOT / 'local/tools/pokeheartgold')
    args = parser.parse_args()
    paths = args.rom or [ROOT / f'local/roms/1.2.3/sgp-1.2.3-{lang}.nds' for lang in ('EN', 'IT')]
    failed = False
    for path in paths:
        try:
            fixture = load_fixture(path, args.pret)
            reports = [verify_start(fixture), verify_battle(fixture)]
            failed |= any(report['errori'] for report in reports)
            print(json.dumps(dict(rom=path.name, lettura_massima_byte=fixture.largest_read,
                                  test=reports, limite='Analisi statica e simulazione script; nessuna riproduzione runtime.'),
                             ensure_ascii=False))
        except (OSError, ValueError, struct.error) as exc:
            failed = True
            print(json.dumps(dict(rom=path.name, esito='FAIL', errore=type(exc).__name__)))
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
