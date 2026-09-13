#!/usr/bin/env python3
"""Reuse the accepted Summary oracles on the combined build identity/layout."""
import argparse
import json
from pathlib import Path
import verify_summary_guide
import verify_summary_save
from run_newgame_guide import current_build, loaded_code
from run_probe import sha


def probe(rom, fixture, observer, out, kind, baseline, save=False):
    suite = verify_summary_save if save else verify_summary_guide
    # Only provenance/text-offset adapters change. Input and all assertions in
    # the reviewed native Summary suite are executed without modification.
    suite.current_build = current_build
    suite.loaded_code = loaded_code
    result = suite.probe(rom, fixture, observer, out, kind, baseline)
    result['composition'] = 'combined-summary-newgame'
    result['composition_adapter_sha256'] = sha(Path(__file__))
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['rom', 'fixture', 'observer', 'out', 'baseline']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--kind', choices=['party', 'box'], required=True)
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    result = probe(args.rom, args.fixture, args.observer, args.out,
                   args.kind, args.baseline, args.save)
    print(json.dumps({name: result[name] for name in ['passed', 'kind', 'language', 'composition']}))
