"""Pinned production UI compiler; all generated code stays in tiny scratch.

The configuration is an explicit test-candidate calibration, not a production
latency claim. No test harness or linker can provide product implementations.
"""
import hashlib
import importlib
import importlib.util
import json
import os
import signal
import time
from pathlib import Path
import shutil
import struct
import subprocess
from sgp13.compiler import compiler_path, compiler_environment
import sys
import tempfile

from . import baseline, guide_content, ui_copy, ui_resource, ui_resource_verify

SOURCE = Path(__file__).resolve().parents[1]
FLAGS = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
         '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fomit-frame-pointer',
         '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
         '-Werror', '-fno-jump-tables', '-fstack-usage', '-std=c11', '-Xclang', '-fno-temp-file']
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
PYTHON_EXECUTABLE_SHA256 = '87d4df53fd91304be5bac391fb204643c36b7df2023c04a0953bcbc7d4fdf634'
PYTHON_VERSION = '3.14.7'
LIBRARY_PINS = {
    "ndspy._common": "85a6422ae23edc38f9a6016d9c8746adee5a76735f2d518abde139b748a5e08c",
    "ndspy._lzCommon": "0cf8c6f186a8fc44f0e657a5b4ca6c8f25c6ca9301b698fd7181f0782bd4b255",
    "ndspy.code": "f9867fcca6a9c738b946ee4a57019dc80f3b1275c23c44e037dc16bfaba543e3",
    "ndspy.codeCompression": "977513a94e20bee7d61b522764182c8e680dc48b3b4588d2fcbf5f4804d178a3",
    "ndspy.fnt": "4ee2ab71ba0ea3ca52f33b6785c59071461019b3bf1168d35a57ad00480cbdde",
    "ndspy.lz10": "322fba9f1ccc6daef9f7526a9bdb96fe35d2afd2a16997f6851c9e4b262efc91",
    "ndspy.narc": "b805b9bbee9c05cc6244a2a010eba8efdc31cfff55a7bde24d268c2b90468255",
    "ndspy.rom": "cbcf8a4607db9af00f4e97ed519e476c5f8e771614e0a1f29c6e67aef1afd78f"
}
COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'
SCENE_UNITS = ['ui-native/heap.c', 'ui-native/resource.c', 'ui-native/guide_resource.c',
               'ui-native/font.c', 'ui-native/bg.c', 'settings-ui/state.c',
               'settings-ui/owners.c', 'settings-ui/render.c', 'settings-ui/painter.c',
               'guide-ui/controller.c', 'guide-ui/render.c', 'guide-ui/painter.c',
               'ui-native/scene_admission.c', 'settings-ui/scene.c', 'ui-native/scene.c']
# Reviewed source identities, generated once for this implementation, not learned
# from input, receipts, environment, or candidate configuration.
SOURCE_PINS = {
    "sgp13/compiler.py": "eb1a45aa39df25ebb342e4a447dbf569e22feb90ed126d364f7db6326d0085c6",
    "sgp131/guide_incoming.py": "b55535de0452edd128e781ffae41cd727446ceabd4224a4d4c4cab0bdbecf32c",
    "sgp131/guide_retirement.py": "a2e5abd850f1835f3418a34e2b4bd3653ed11c365f49870f67f107cebdb58abc",
    "features/field-guide/sorgenti/controller.h": "06bf671098465c9c83bdbca7e5b5e88102225bef23039ac5755c41c7911d4d6c",
    "features/field-guide/sorgenti/controller_core.h": "86c21eb508499243283ad59f61fdcf291025f97fd6473533aa30712fb60347c2",
    "features/field-guide/sorgenti/guide.c": "382e5fc13f3264026f2d40deeec332ef1462bf69062d9005635aa7fadf51a198",
    "features/guide-ui/controller.c": "23b8904f9776d7e387a8e8c718da27fdc5d41ed5e7fdbd8edea20dab63e900a9",
    "features/guide-ui/controller.h": "63906be7b2e0868f31c16ec02f0b9ca8aee2607cf3379ee006b1a7dc4aaafaed",
    "features/guide-ui/painter.c": "eea15117597445a1dd61a4f60bc54bda196c40f66dd6936c022b6865e968b59f",
    "features/guide-ui/painter.h": "52eebd7e82a3af9fa197340d53afe25161e62df4a90332683083d4a3121f7129",
    "features/guide-ui/render.c": "8f75023b1334fe41540eb8b6f966456eb83ed3b6aa3ee14e79cde5f4b4dce2fe",
    "features/guide-ui/render.h": "4db3648e750bbf107a7a0bc1852ae2312fa5b9dd28cee3ce274ab3be91894b2a",
    "features/options/sorgenti/continua_domanda.c": "068ab4121111cc427ff375c9a872561171210b89adbc2bc13eab0157b335530a",
    "features/options/sorgenti/opzioni_pagina.c": "d9861b79aa6fad0a66585879730e61b2195567368567bc38cdb38f17dca12116",
    "features/options/sorgenti/sgp_ui.h": "e585c1f39a6a340db9bff04ce9866b69317e63bd1e44ded712d3012056a34cc4",
    "features/options/sorgenti/ui_blob.c": "4501298aa26e8b66751f404b10f77db2efc779cf3784ee8cddfc95da161c41e7",
    "features/options/sorgenti/ui_comune.c": "13cdcbe2fb7e5f6eed732c47f507d111b9c0cdeaff7f08a9725a218cbe4d0e68",
    "features/options/tools/carica_text.py": "45f8850662d9f748c306b15bb12d0e8d0f9598722e87debb70ee3efe6fdd32ee",
    "features/options/tools/codifica_testo.py": "ebacefd83bcf6e9b1ff9ef11bf4ccf143e9238fe35a492066129f3b1d6911a0a",
    "features/plus-ui/context.c": "9be4b196fee0db709f3bd685f6409a19904e90f42dc7fa88332fdbfc92f2a9be",
    "features/plus-ui/extended.c": "7fa96e4d122600b036acf99cf33c323b26ecde618d6cdcd675b4cdeb35e5a452",
    "features/plus-ui/extended.h": "12e66ffc4fcb9a057c4f2b6ca38b39f9a4681938c0645cab461467bb2819afdd",
    "features/plus-ui/hunt_panel.c": "efe0bff786578db716351694fed06f43bbf1ded186082953aeace92d2f11ccaa",
    "features/plus-ui/navigation.c": "7ea31bcea8d22ca60b350bbe91125e6f5461989db3b4ccd45cc1beb523f9e7e2",
    "features/plus-ui/ui_blob.c": "5af3ff60e0511ffd4b44f16e742ca2418d3ee5f209950881b0bb813867a83a5b",
    "features/plus-ui/ui_common.c": "c3f3c28643afb4ea9b22bb0b3744df6476eea71effd6b37006adc29db3331a6f",
    "features/settings-ui/catalog.h": "716ad2eca0d45f86affd6d0d1d34af821451ceb72022149576db8a8a8edd6f8e",
    "features/settings-ui/controller.h": "26ea9fabcc759dfaaab059ca5cc27b0c42ccf7bf09032b66d505d288e731bc8f",
    "features/settings-ui/owners.c": "7e0916a34912114db5e1fde40a8fa0de2e5f5ffb5d89d48c48ba5c77f16bb456",
    "features/settings-ui/owners.h": "713fc10402763f45f71e6461327f6a4487b0c63298084895e81b239d9928366a",
    "features/settings-ui/painter.c": "6c5f0944106aa87111a60d262c913d79eb33d14e1bd21072b88c7fd2d0ca24bc",
    "features/settings-ui/painter.h": "9f92a69d524f78b358561c650dce194ed8907f8787a9e6787dcd3ef0b2a4b368",
    "features/settings-ui/render.c": "68021ca7a847fae11967401db3aef98a127e22711832f05f2fc2f3a71ebca84a",
    "features/settings-ui/render.h": "55b7f00274376de65dbcd97c33f91e10df9357c52832c5b52dd842db3f6c5744",
    "features/settings-ui/scene.c": "e90ee1f3276c97182fa4a96926e6444f562b96ead3f6a46064e9b3139ccae3e2",
    "features/settings-ui/state.c": "9f9c5cc0dd7b243c4ffa7b9a724ccfa90e567282d874f0c65cfd6388fd9d4181",
    "features/shiny/api.h": "95b6c125737b0cd261bb14431603f5f4aed377749762790863eada4feb831e91",
    "features/shiny/core.c": "2daf1df894fb1b0c58883024142fe9c6e8e8dc52cb0f0971324cb8bc93389ea3",
    "features/shiny/core.h": "20feae1635b6b4b334bd6a095ab4ebc900dacedc9c0870ffe6a90f066fa31a05",
    "features/shiny/internal.h": "ff1055559264c74fd66419995f55c0145f63b69d338b4d34ef95c95979d8f7d2",
    "features/shiny/native.c": "f24482feae49c48c69caecb0968f266efeec7f928c257ae2b087de5cf745311a",
    "features/shiny/search.c": "06828a9c1419199043a7fe403f7ce01eb1e4b6d9c528e214359acd3f9b5a8e23",
    "features/shiny/ui_api.h": "f2de99606bac2821e80a1334d9b208d3f6c3782fb255d519199d4679d6f72cb7",
    "features/shiny/ui_transaction.c": "edd5bb456d00ea51d73bc4a3e82a64627bae3eab891fc79e40d7b276d4762cfa",
    "features/training-native/ownership.c": "97d5f7673bdf124cb80fbeedf0322709a4142909badf6fa097dd924c21362a74",
    "features/training-native/ownership.h": "28b05f4fb1a74a74383968096f49a089b24eba209424a0be82c2e716415c822d",
    "features/training-native/runtime.c": "72a3ac6a83e810ea0c4bdcd070f5ed1f5d660ea4a9347a8ef05c1e044ae521d5",
    "features/training-native/state.h": "623fa62159ac3beba844c3aa71d3f3ba67de9298d6981a136f187c8de9ef606b",
    "features/training-native/transaction.c": "c04a9e0f71b80c8ebab92644d2d4772f6deeba45284d5f64ede1b0a32d8d030b",
    "features/training-native/transaction.h": "f10a41d1b340a9877faa494da7ee13f807676a2ede7b4c2fea6e49d33e39eb59",
    "features/training-native/ui_transaction.c": "ff3c32f9250c78363e12f392736eb1774daa2608cca60068021cfb8161cbf0ec",
    "features/training/sorgenti/training.h": "ab631233e3237c1ba4c0b94427a5fe4363a3036d97c0f6c6650c5e143c43f47f",
    "features/ui-native/bg.c": "ed6da7f2f71bd2896e6f6d778a34d2e60631213c9d4739725cebe5bb83d923f6",
    "features/ui-native/bg.h": "bd425abfa7e3c71aa6029286e5d470f94e816896362ff64a77975e54117fcd98",
    "features/ui-native/bridge.c": "ec8c40148c22e7da5412628ecb4fb1a816755cf4723214997a0feb427d233d76",
    "features/ui-native/bridge.h": "eb21404bc7b0ee552a1f66acf2ec2850ce7b8604cfedd6f714a534962a397722",
    "features/ui-native/fieldbook.c": "628f55216143d4fed915f52e083a29a860ea6fe9ddaf6f95dc431425ee3f8df5",
    "features/ui-native/fieldbook.h": "7097f9629839654de31d94821fd2362b36323bd462fa7527030ac80f2ead2cbb",
    "features/ui-native/font.c": "96f7d33ad1923586ed8f6234a42ffa3acd86c99993618b3ba9a62a66dcc69646",
    "features/ui-native/font.h": "b7669616d7e074dff9cc568275bc4d1e7ac276258859f1a45d707181e610032d",
    "features/ui-native/guide_resource.c": "c3eaa856162b24ab7813f01b62874f4b917aea9dfa0a83339073de1750ac7be9",
    "features/ui-native/guide_resource.h": "08c818a5fddfcfc96c6205ffc97c56e7133b164266253d6f5b85a926ee150957",
    "features/ui-native/heap.c": "0462b443978b5db1dba759bc33389eff98f0ede189e39463259f4e82aaf1f219",
    "features/ui-native/heap.h": "36258d9da70e43a534b126338ae0dcc4bd11180063d79f246355175c7085ee07",
    "features/ui-native/heap_internal.h": "f97406f97c1baea94b11821f7da79348e6050f1f8bcb5ea7b33bee093952048e",
    "features/ui-native/module.c": "dc79a791ca06c78336cdcbcd11a4643cc8c278a5da042f5ba5f98c6b4db60e14",
    "features/ui-native/module.h": "10153ad5b60ffe4ae47acace2320213c65c740509ba6d887b064c69a65618642",
    "features/ui-native/native_abi.h": "c2c9ddb99a5cb44e21d227cf2fd3895d04cbf9aa92d176e2dfc5dc232353c977",
    "features/ui-native/persistent.c": "f47d4d8f08e741bad164d857e4e884d9db26abe0e8d85c119769add9f62b81e3",
    "features/ui-native/persistent.h": "de3f432b5b7fafffb05d3bfa428d9b9242942834d7afed72a76fa100e82233f9",
    "features/ui-native/physical.c": "3d8a31166d48ecbee392d05180a63a0ad15109bcbfbbcf86e7f5cb12d095b2ae",
    "features/ui-native/physical.h": "9c609c01e6dd01f185ff68aad3a828b0d239e43b353c8168f084d80282b0c16a",
    "features/ui-native/resource.c": "4358ce9227b253c94f9b0b3d9b5e59f54c7e35376d83e9dcb3c8b4ea0d03c9c6",
    "features/ui-native/resource.h": "1ca2edf7a8f2d5e2f4cc4778ec79ad7a0f8741b52c97eea8754e7bf52ec34f18",
    "features/ui-native/scene.c": "2559f576012335564fb8ac18f4496d12228160de7ef4030791394dbd8f542b8d",
    "features/ui-native/scene.h": "fcfc70053708bab23089e493f67788f8d2a119e2eade2ec22a240c4b04fe870b",
    "features/ui-native/scene_admission.c": "8db4b2de013bda096eb4177b672774c81a1c25bdef487a8fbfed03175fd2601b",
    "features/ui-native/scene_admission.h": "189d90f7bad738edfc630f5fa131199b9d151cda672b4c8470475bb7b88d4f18",
    "quality-audit/hgss_text.py": "35af2fda543bd9495c9b1ca5514478dc821684d78e158f67f72908b0570c34db",
    "quality-audit/misura_larghezza.py": "52894176d14d6c320011b54d70ec56034e83a17649a9c857074af178568389be",
    "sgp13/content.py": "fddda216f3f1596fae433c2b75cf8151095e5feeb65b4b3468c458f806bde3fb",
    "sgp13/guide.py": "7180d9af822729b6b3f4b417c6d83066226bacf3d3e6463ec339d4adba1c9b75",
    "sgp13/plus_ui.py": "5f5f3d61bd83bb820119be9dd0151c255e2d66999e7cf8ea985ec792b1159f6c",
    "sgp131/baseline.py": "a5d00444cbce85b79170202505be37292d35e9fade3449db4eb0d0dbbdb82327",
    "sgp131/data/guide-subjects.json": "3cdb55ba7fb73071e2ccdac852d5786f063f7287432c927dcde9fe80af6ac91e",
    "sgp131/data/guide.json": "8c59d185bb65cecf87cbdca1d037799b271a9c5c4edf2fecc7b09fa1aef2afc3",
    "sgp131/data/reserve-map.json": "7b201a7ea5abe3b611ac12dd1391496817d134874af87360935c97db8cfa4f6a",
    "sgp131/data/ui-copy.json": "6fe891c7252ffffdfb3fa10f25f25251e961b869b728a86ece33e516c49cad30",
    "sgp131/guide_content.py": "b61119db09bc149081128a24c8e89be8e9e62526c904a7db84542a3fabfe9647",
    "sgp131/reserve.py": "d677827f7dbbfa422a56257860f6bcdad360e01da4b83803af243b74b033fb2a",
    "sgp131/ui_copy.py": "0f7f27da938bda8df2c89712155df23abc935f0b2eb2ce3d6a19f574afde7cb9",
    "sgp131/ui_resource.py": "1d5b372dc88259a2b40ed5cd25cbc31af1ca6a757b1c184e686b30217771445c",
    "sgp131/ui_resource_verify.py": "2ef7aacb48d6f349b4612cc6ed2ac4175f5ec54954bfd2ba8710ece4306489d9",
    "translation/message_codec.py": "61de1dd4a7995ee5b6c1e20b45556c414c2fbdb55c9acd56707783cc6863891f",
    "localization/__init__.py": "e2a09065507debf68d6f85c471c7cf86ad7243a6620728416f093018e5f2c621",
    "localization/catalogue.py": "1eeba353949e14809a45f68efcd4952338d91603c4d20408f429416ce51e5704",
    "localization/locales/FR/ui.json": "19f8d01459f1e4a5c6cb3b979768e5551240e97d42efbd111c81e439ed98f842",
    "localization/locales/ES/ui.json": "f4ff39a8ed720f83961e582756a27e74d8720ce9ffbb7504259062843c2c8906",
    "localization/locales/DE/ui.json": "f5e22900ae2b1e89e5e3a884da1f1514cc312b2f976b17d926fd8c8b287d7c1d",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def validate_config(config):
    fields = {'schema', 'kind', 'scene_work_calls', 'scene_glyph_budget', 'scene_last_start_line'}
    require(type(config) is dict and set(config) == fields, 'candidate configuration exact fields')
    require(type(config['schema']) is int and config['schema'] == 1 and config['kind'] == 'test-candidate',
            'explicit test-candidate configuration required')
    for key, lo, hi in [('scene_work_calls', 1, 4096), ('scene_glyph_budget', 1, 8),
                        ('scene_last_start_line', 192, 261)]:
        require(type(config[key]) is int and lo <= config[key] <= hi, 'candidate configuration ' + key)
    return dict(config)


def read_config(work_dir):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate candidate field')
            result[key] = value
        return result
    try:
        config = json.loads((Path(work_dir) / 'ui-candidate.json').read_text(), object_pairs_hook=pairs)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError('explicit ui-candidate.json required') from error
    return validate_config(config)


def check_sources():
    require(sys.version.split()[0] == PYTHON_VERSION, 'Python toolchain drift')
    require(sha(Path(sys.executable).resolve().read_bytes()) == PYTHON_EXECUTABLE_SHA256, 'Python executable drift')
    for name, digest in LIBRARY_PINS.items():
        library = importlib.import_module(name)
        require(sha(Path(library.__file__).read_bytes()) == digest, 'library source drift: ' + name)
    for path, digest in SOURCE_PINS.items():
        try:
            actual = sha((SOURCE / path).read_bytes())
        except OSError as error:
            raise ValueError('missing pinned source: ' + path) from error
        require(actual == digest, 'pinned source changed: ' + path)
    require(bool(SOURCE_PINS), 'empty source freeze')
    return dict(SOURCE_PINS)



# Exact child-side limits; no preexec_fn or shell-unit assumptions. Isolated
# standard-library bootstrap runs before execv and cannot load project modules.
CHILD_BOOTSTRAP = ("import os,resource,sys; "
                   "resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304)); "
                   "resource.setrlimit(resource.RLIMIT_CORE,(0,0)); "
                   "os.execv(sys.argv[1],sys.argv[1:])")
MAX_FILE = 4 * 1024 * 1024
MAX_SCRATCH = 16 * 1024 * 1024  # sampled acceptance, not a disk quota
FREE_SPACE_FLOOR = 10 * 1024**3
MAX_ACTIVE_FILES = 25  # six .c/.o/.d/.su sets plus one diagnostic
TRANSIENT_RESERVE = MAX_ACTIVE_FILES * MAX_FILE
MAX_DIAGNOSTIC = 65536
COMPILER_TIMEOUT = 60


def _run(command, directory, allowed, timeout=COMPILER_TIMEOUT):
    """One bounded compiler child; temporary diagnostics never escape scratch.

    RLIMIT_FSIZE is a hard per-child-file limit. The directory total/inventory
    are checked while running and after exit, not a filesystem quota. A trusted
    pinned compiler has six fixed units and at most24 outputs plus diagnostics;
    25*4MiB is a conservative transient upper bound for that fixed inventory.
    """
    directory = Path(directory)
    diagnostic = directory / 'diagnostics.txt'
    require(not diagnostic.exists(), 'compiler diagnostic path occupied')
    process = None
    def inspect():
        total = 0
        entries = list(directory.iterdir())
        require(len(entries) <= MAX_ACTIVE_FILES, 'compiler output count')
        for path in entries:
            require(path.is_file() and not path.is_symlink() and
                    (path.name in allowed or path == diagnostic), 'compiler output inventory: ' + path.name)
            size = path.stat().st_size
            require(size <= MAX_FILE, 'compiler file size limit')
            total += size
        require(total <= MAX_SCRATCH, 'compiler scratch aggregate limit')
        require(diagnostic.stat().st_size <= MAX_DIAGNOSTIC, 'compiler diagnostic overflow')
    try:
        with diagnostic.open('xb') as output:
            start = time.monotonic()
            process = subprocess.Popen([sys.executable, '-I', '-S', '-c', CHILD_BOOTSTRAP, *command],
                                       cwd=directory, stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True, env=compiler_environment())
            while True:
                inspect()
                remaining = timeout - (time.monotonic() - start)
                require(remaining > 0, 'compiler timeout')
                try:
                    code = process.wait(timeout=min(0.05, remaining))
                    break
                except subprocess.TimeoutExpired:
                    pass
            inspect()
        diagnostic_text = diagnostic.read_bytes().decode('utf-8', 'replace')
        require(code == 0, 'compiler failure: ' + diagnostic_text)
        return diagnostic_text
    except BaseException:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                # macOS may refuse a group signal after the child exits.
                if process.poll() is None:
                    raise
            process.wait(timeout=5)
        raise
    finally:
        diagnostic.unlink(missing_ok=True)


def _toolchain(directory):
    compiler = compiler_path(COMPILER_SHA256)
    require(compiler is not None, 'clang unavailable')
    version = _run([compiler, '--version'], directory, {p.name for p in Path(directory).iterdir()})
    require(version.splitlines()[0] == COMPILER_VERSION, 'compiler version drift')
    executable = sha(Path(compiler).resolve().read_bytes())
    require(executable == COMPILER_SHA256, 'compiler binary drift')
    return compiler, {'version': version, 'executable_sha256': executable, 'flags': FLAGS,
                      'python_executable_sha256': PYTHON_EXECUTABLE_SHA256,
                      'bootstrap_sha256': sha(CHILD_BOOTSTRAP.encode()), 'timeout_seconds': COMPILER_TIMEOUT,
                      'file_limit_bytes': MAX_FILE, 'diagnostic_limit_bytes': MAX_DIAGNOSTIC,
                      'post_run_scratch_limit_bytes': MAX_SCRATCH,
                      'transient_reserve_bytes': TRANSIENT_RESERVE, 'free_space_floor_bytes': FREE_SPACE_FLOOR,
                      'max_active_files': MAX_ACTIVE_FILES, 'dependency_output': 'bounded stdout; parent writes .d'}


def _compile(directory, name, units, base, cap, defines):
    compiler, toolchain = _toolchain(directory)
    source = directory / (name + '.c')
    body = ''.join('#include "' + str(SOURCE / 'features' / p) + '"\n' for p in units)
    source.write_text(body)
    obj, dep = directory / (name + '.o'), directory / (name + '.d')
    command = [compiler, *FLAGS, *['-D' + k + '=' + str(v) for k, v in sorted(defines.items())],
               '-MMD', '-MF', '-', '-MT', name+'.o', '-c', str(source), '-o', str(obj)]
    # Clang's dependency-file path uses a separate atomic .d.tmp even with
    # -fno-temp-file. Stdout avoids that producer entirely; do not admit tmp
    # names, or a child-written .d, into the active inventory.
    allowed = {p.name for p in directory.iterdir()} | {name+suffix for suffix in ('.c','.o','.su')}
    allowed.discard(name+'.d')
    dependency_text = _run(command, directory, allowed)
    lines = dependency_text.replace('\\\n', '').splitlines()
    target = name+'.o:'
    require(len(lines) == 1 and lines[0].split()[:1] == [target], 'compiler dependency output grammar')
    dependencies = lines[0].split()[1:]
    require(bool(dependencies) and dependencies[0] == str(source), 'compiler dependency source identity')
    # The child must succeed under -Werror and output exactly one dependency
    # rule. Extra diagnostics are refused, never silently parsed as source pins.
    dep.write_text(dependency_text)
    require(sum(p.stat().st_size for p in directory.iterdir()) <= MAX_SCRATCH,
            'compiler scratch aggregate limit after dependency write')
    consumed = {}
    for p in dependencies:
        path = Path(p)
        if path == source:
            continue
        relative = str(path.resolve().relative_to(SOURCE))
        require(relative in SOURCE_PINS, 'unfrozen compilation dependency ' + relative)
        consumed[relative] = sha(path.read_bytes())
        require(consumed[relative] == SOURCE_PINS[relative], 'source changed during compile ' + relative)
    raw = obj.read_bytes()
    loader = module(SOURCE / 'features/options/tools/carica_text.py', 'ui_strict_loader')
    data, symbols = loader.load_text(raw, base)
    require(0 < len(data) <= cap, name + ' payload capacity overflow: ' + str(len(data)))
    return dict(data=data, symbols=symbols, base=base, capacity=cap, defines=dict(defines),
                receipt=dict(base=base, bytes=len(data), capacity=cap, sha256=sha(data),
                             object_sha256=sha(raw), translation_unit_sha256=sha(body.encode()),
                             sources=consumed, defines=dict(defines), symbols=symbols,
                             toolchain=toolchain,
                             stack_usage=(directory / (name + '.su')).read_text().replace(str(directory), 'TEMP')))


def compile_payloads(config, work_dir):
    config = validate_config(config)
    check_sources()
    require(shutil.disk_usage(work_dir).free >= FREE_SPACE_FLOOR + TRANSIENT_RESERVE, 'compiler scratch disk budget')
    with tempfile.TemporaryDirectory(prefix='ui-compile-', dir=work_dir) as scratch:
        directory = Path(scratch)
        p = _compile(directory, 'physical', ['ui-native/physical.c'], 0x023D6E10, 1024,
                     {'SGP_PHYSICAL_SLOT_ADDR': 0x023D7210, 'SGP_PHYSICAL_SYSTEM_ADDR': 0x021D110C,
                      'SGP_PHYSICAL_KEYINPUT_ADDR': 0x04000130, 'SGP_PHYSICAL_SHARED_ADDR': 0x027FFFA8,
                      'SGP_PHYSICAL_MAPPING_ADDR': 0x0201A5E9, 'SGP_PHYSICAL_LID_ADDR': 0x0200110D})
        scene = _compile(directory, 'scene', SCENE_UNITS, 0x021E5900, 65536,
                         {'UI_SCENE_WORK_CALLS': config['scene_work_calls'],
                          'UI_SCENE_GLYPH_BUDGET': config['scene_glyph_budget'],
                          'UI_SCENE_LAST_START_LINE': config['scene_last_start_line'],
                          'SGP_UI_SCENE_PHYSICAL_CONSUME': p['symbols']['physical_consume'],
                          'SGP_UI_SCENE_PHYSICAL_ACK': p['symbols']['physical_ack_suspend']})
        tail = (len(scene['data']) + 3) & ~3
        shiny = _compile(directory, 'shiny', ['shiny/ui_transaction.c'], 0x021E5900 + tail, 65536 - tail,
                         {'SGP_SETTINGS_UI_SUCCESSOR': 1,
                          'SGP_SETTINGS_UI_FINAL_CHECK': scene['symbols']['settings_final_check']})
        dynamic = scene['data'] + bytes(tail - len(scene['data'])) + shiny['data']
        dynamic += bytes((-len(dynamic)) % 4)
        require(len(dynamic) <= 65536, 'combined dynamic54 capacity')
        bridge = _compile(directory, 'bridge', ['ui-native/persistent.c', 'ui-native/module.c', 'ui-native/bridge.c'],
                          0x023CB800, 12272, {'UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS': 0x023D7B20,
                          'UI_BRIDGE_PHYSICAL_ACTIVATE': p['symbols']['physical_activate'],
                          'UI_BRIDGE_PHYSICAL_DEACTIVATE': p['symbols']['physical_deactivate']})
        training = _compile(directory, 'training', ['training-native/ui_transaction.c'], 0x023D6800, 1536,
                            {'SGP_SETTINGS_UI_SUCCESSOR': 1})
        fieldbook = _compile(directory, 'fieldbook', ['ui-native/fieldbook.c'], 0x023D4000, 3072, {})
        result = dict(physical=p, scene=scene, shiny=shiny, bridge=bridge, training=training,
                      fieldbook=fieldbook, dynamic54=dict(base=0x021E5900, data=dynamic, capacity=65536))
        check_sources()
        _toolchain(directory)
        return result


def evolution_records(rom, archive_deltas=()):
    """Return evolution members after the exact declared archive delta, if present."""
    from ndspy.narc import NARC
    from . import archives
    raw = bytes(rom.getFileByName('a/0/3/4'))
    matching = [delta for delta in archives.normalize(archive_deltas)
                if delta.archive == 'a/0/3/4']
    require(len(matching) <= 1, 'one evolution archive delta')
    if matching:
        raw = archives.apply_members(raw, matching[0].replacements())
    return NARC(raw).files


def resources(data, language, charmap, archive_deltas=()):
    """Byte-only adapter for the existing path-based Guide source contract.

    Existing semantic packer, verifier, codecs, font widths and coverage remain
    authoritative. No monkeypatch of filesystem APIs or temporary ROM is used.
    """
    from ndspy.rom import NintendoDSRom
    from ndspy.narc import NARC
    from ndspy.code import MainCodeFile
    require(baseline.identify(data) == language, 'input language mismatch')
    require(sha(Path(charmap).read_bytes()) == guide_content.CHARMAP_SHA256, 'charmap identity')
    rom = NintendoDSRom(data)
    scripts = NARC(rom.getFileByName('a/0/1/2')).files
    for member, digest in guide_content.SCRIPT_PINS.items():
        require(sha(scripts[member]) == digest, 'Guide script preimage')
    arm = MainCodeFile(rom.arm9, rom.arm9RamAddress)
    def read(address, length):
        spans = [s.data[address-s.ramAddress:address-s.ramAddress+length] for s in arm.sections
                 if s.ramAddress <= address and address+length <= s.ramAddress+len(s.data)]
        require(len(spans) == 1, 'Guide native span')
        return bytes(spans[0])
    for address, length, digest in guide_content.NATIVE_PINS:
        require(sha(read(address, length)) == digest, 'Guide native preimage')
    pointer = struct.unpack('<I', read(0x02029D70, 4))[0]
    require(struct.unpack('<9H', read(pointer, 18)) == guide_content.EXCLUSIONS, 'Guide exclusions')
    text = module(SOURCE/'quality-audit/hgss_text.py', 'ui_native_text')
    font = module(SOURCE/'quality-audit/misura_larghezza.py', 'ui_native_widths')
    codec = module(SOURCE/'features/options/tools/codifica_testo.py', 'ui_native_codec')
    chars, commands = text.load_charmap(charmap)
    table, _ = codec.carica_charmap(charmap)
    font_member = bytes(NARC(rom.getFileByName('a/0/1/6')).files[0])
    widths = font.extract_width_table(font_member)
    ui_widths = font_member[struct.unpack_from('<I', font_member, 4)[0]:]
    archive = NARC(rom.getFileByName('a/0/2/7'))
    banks = {kind: text.read_bank(archive.files[index], chars, commands)
             for kind, index in [('item', 222), ('pokemon', 237), ('move', 750), ('map', 279)]}
    def names(kind, index):
        row = banks[kind][index]
        require(not (row['controls'] or row['unknown_codes'] or row['malformed_controls']), 'native name controls')
        return row['text']
    def encode(value):
        return codec.codifica(value.replace("'", '’'), table)
    def measure(value):
        measured = font.measure(widths, encode(value), limit_px=224)
        require(not any(line['unknown_codes'] for line in measured['lines']), 'unknown native glyph')
        return max(line['width_px'] for line in measured['lines'])
    records = evolution_records(rom, archive_deltas)
    prose = json.loads(guide_content.PROSE.read_text())
    categories = guide_content.make_categories(records, names, language, measure, prose)
    require([len(c['entries']) for c in categories] == [6, 229, 76, 156], 'Guide coverage')
    expected_special = {2000+s for s in guide_content.SINGLE_SUBJECTS} | set(guide_content.GROUPS) | {5000+s for s in guide_content.ALIASES}
    require({e['id'] for e in categories[2]['entries']} == expected_special, 'Guide subjects')
    guide = guide_content.build_content(categories, encode, measure)
    graph = guide_content.encoded_graph(categories, encode)
    guide_content.verify_content(guide, graph)
    from localization.catalogue import ui_catalogue
    catalog = ui_catalogue()
    # UIR copy contract uses the native codec verbatim (Guide normalizes apostrophes).
    authored, geometry = ui_copy.encode_catalogue(catalog, language, lambda t: codec.codifica(t, table), ui_widths)
    require(ui_copy.c_header(catalog) == (SOURCE/'features/settings-ui/catalog.h').read_text(), 'catalog C identity')
    resource, receipt = ui_resource.compile_resource(data, authored)
    require(ui_resource_verify.verify_resource(data, resource, authored) == receipt, 'UIR independent readback')
    return dict(guide=guide, guide_graph=graph, uir=resource, uir_receipt=receipt,
                authored=authored, geometry=geometry)
