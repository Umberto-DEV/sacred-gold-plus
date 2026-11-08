"""Localized package explanations, with an unchanged English GPL license.

The explanations are not license translations and grant no third-party rights.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import PurePosixPath


LOCALES = ('EN', 'IT', 'FR', 'ES', 'DE')
LICENSE_BYTES = 35147
LICENSE_SHA256 = '8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903'
PROJECT_URL = 'https://github.com/Umberto-DEV/sacred-gold-plus'
ORIGINAL_PLUS_URL = ('https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/'
                     'sacred_gold_plus_fairy_type_full_implementation/')

_NOTICES = {
    'EN': """CREDITS AND LICENSE

Sacred Gold / Storm Silver: Drayano and the original contributors.
Fairy-type foundation: mikelan / Mikelan98.
Original Sacred Gold Plus: NefariousnessNo3436, including its Fairy moves and wider camera.
Historical trainer reference: @JD48096761; its author credits u/ittapubas as inspiration.
This continuation: @Umberto-DEV and the community contributors.

The original Plus author's public reuse permission asks for credit to the original authors; see the announcement below. This is an independent fan continuation, with no claim of an official handover.

This project's own tools and source code use GPL-3.0-or-later. LICENSE.txt contains the complete, unmodified English GNU GPL version 3. This explanatory notice does not replace or change its terms. Pokemon, the original game and third-party contributions remain under their owners' rights; this notice grants no license to those materials.

In the main download, Originals/ contains the seven current English gameplay PDFs for this release, shared once for all languages, with the relevant author credits. The installation and news PDFs are in each language folder of that download.

Project and source code: {project}
Original Plus announcement and reuse permission: {original}
""",
    'IT': """CREDITI E LICENZA

Sacred Gold / Storm Silver: Drayano e i collaboratori originali.
Base del tipo Folletto: mikelan / Mikelan98.
Sacred Gold Plus originale: NefariousnessNo3436, comprese le mosse Folletto e la visuale più ampia.
Riferimento storico degli Allenatori: @JD48096761; il suo autore cita u/ittapubas come fonte di ispirazione.
Questa continuazione: @Umberto-DEV e i collaboratori della comunità.

Il permesso pubblico di riutilizzo dell'autore originale di Plus richiede il riconoscimento degli autori originali; vedi l'annuncio qui sotto. Questa è una continuazione indipendente di appassionati, senza rivendicare un passaggio ufficiale del progetto.

Gli strumenti e il codice sorgente propri di questo progetto usano GPL-3.0-or-later. LICENSE.txt contiene il testo inglese completo e invariato della GNU GPL versione 3. Solo il testo inglese della licenza ne stabilisce i termini. Questo avviso è una spiegazione, non una traduzione della licenza, e non ne sostituisce o modifica i termini. Pokémon, il gioco originale e i contributi di terze parti restano soggetti ai diritti dei rispettivi titolari; questo avviso non concede licenze su tali materiali.

Nel download principale, Originals/ contiene i sette PDF di gioco attuali in inglese per questa versione, condivisi una sola volta fra tutte le lingue, con i riconoscimenti pertinenti. I PDF di installazione e novità sono in ogni cartella linguistica di quel download.

Progetto e codice sorgente: {project}
Annuncio originale di Plus e permesso di riutilizzo: {original}
""",
    'FR': """CRÉDITS ET LICENCE

Sacred Gold / Storm Silver : Drayano et les contributeurs d'origine.
Base du type Fée : mikelan / Mikelan98.
Sacred Gold Plus d'origine : NefariousnessNo3436, notamment les capacités Fée et la vue élargie.
Référence historique des Dresseurs : @JD48096761 ; son auteur cite u/ittapubas comme source d'inspiration.
Cette continuation : @Umberto-DEV et les contributeurs de la communauté.

L'autorisation publique de réutilisation de l'auteur d'origine de Plus demande de citer les auteurs d'origine ; voir l'annonce ci-dessous. Il s'agit d'une continuation indépendante de passionnés, sans revendication d'une reprise officielle du projet.

Les outils et le code source propres à ce projet sont sous GPL-3.0-or-later. LICENSE.txt contient le texte anglais complet et inchangé de la GNU GPL version 3. Seul le texte anglais de la licence en définit les conditions. Cet avis est une explication, pas une traduction de la licence ; il ne remplace ni ne modifie ses conditions. Pokémon, le jeu d'origine et les contributions de tiers restent soumis aux droits de leurs titulaires respectifs ; cet avis n'accorde aucune licence sur ces éléments.

Dans le téléchargement principal, Originals/ contient les sept PDF de jeu actuels en anglais pour cette version, partagés une seule fois entre toutes les langues, avec les crédits pertinents. Les PDF d'installation et de nouveautés se trouvent dans chaque dossier de langue de ce téléchargement.

Projet et code source : {project}
Annonce originale de Plus et autorisation de réutilisation : {original}
""",
    'ES': """CRÉDITOS Y LICENCIA

Sacred Gold / Storm Silver: Drayano y los colaboradores originales.
Base del tipo Hada: mikelan / Mikelan98.
Sacred Gold Plus original: NefariousnessNo3436, incluidos sus movimientos de tipo Hada y la vista ampliada.
Referencia histórica de Entrenadores: @JD48096761; su autor cita a u/ittapubas como fuente de inspiración.
Esta continuación: @Umberto-DEV y los colaboradores de la comunidad.

El permiso público de reutilización del autor original de Plus pide dar crédito a los autores originales; consulta el anuncio enlazado más abajo. Esta es una continuación independiente de aficionados, sin afirmar un traspaso oficial del proyecto.

Las herramientas y el código fuente propios de este proyecto usan GPL-3.0-or-later. LICENSE.txt contiene el texto completo e inalterado en inglés de la GNU GPL versión 3. Solo el texto inglés de la licencia establece sus condiciones. Este aviso es una explicación, no una traducción de la licencia, y no sustituye ni modifica sus condiciones. Pokémon, el juego original y las contribuciones de terceros siguen sujetos a los derechos de sus titulares; este aviso no concede licencias sobre esos materiales.

En el paquete principal, Originals/ contiene los siete PDF de juego actuales en inglés para esta versión, compartidos una sola vez entre todos los idiomas, con los créditos pertinentes. Los PDF de instalación y novedades están en cada carpeta de idioma de ese paquete.

Proyecto y código fuente: {project}
Anuncio original de Plus y permiso de reutilización: {original}
""",
    'DE': """DANKSAGUNG UND LIZENZ

Sacred Gold / Storm Silver: Drayano und die ursprünglichen Mitwirkenden.
Grundlage für den Feen-Typ: mikelan / Mikelan98.
Ursprüngliches Sacred Gold Plus: NefariousnessNo3436, einschließlich der Feen-Attacken und der erweiterten Kameraansicht.
Historische Trainerübersicht: @JD48096761; ihr Autor nennt u/ittapubas als Inspiration.
Diese Fortsetzung: @Umberto-DEV und die Mitwirkenden aus der Community.

Die öffentliche Erlaubnis des ursprünglichen Plus-Autors zur Weiterverwendung verlangt die Nennung der ursprünglichen Autoren; siehe die unten verlinkte Ankündigung. Dies ist eine unabhängige Fortsetzung von Fans, die keine offizielle Projektübergabe beansprucht.

Die eigenen Werkzeuge und der Quellcode dieses Projekts stehen unter GPL-3.0-or-later. LICENSE.txt enthält den vollständigen, unveränderten englischen Text der GNU GPL Version 3. Nur der englische Lizenztext legt die Lizenzbedingungen fest. Dieser Hinweis ist eine Erläuterung und keine Übersetzung der Lizenz; er ersetzt oder ändert ihre Bedingungen nicht. Pokémon, das ursprüngliche Spiel und Beiträge Dritter unterliegen weiterhin den Rechten ihrer jeweiligen Rechteinhaber; dieser Hinweis erteilt keine Lizenz für diese Materialien.

Im Hauptdownload enthält Originals/ die sieben aktuellen englischen Spielanleitungs-PDFs für diese Version einmal gemeinsam für alle Sprachen, mit den jeweiligen Autorenangaben. Die Installations- und Neuigkeiten-PDFs stehen in jedem Sprachordner dieses Downloads.

Projekt und Quellcode: {project}
Ursprüngliche Plus-Ankündigung und Erlaubnis zur Weiterverwendung: {original}
""",
}

_START_TEXT = {
    'EN': ("English", "Open {guide} first. The single patch in this folder is for an unmodified US English HeartGold ROM. For an earlier Plus ROM or a different starting language, use the optional {updater} from the official release. When updating, keep your current game language, ROM filename and location, raw .sav and Plus settings. Current English gameplay guides: Originals/. Credits and license: {folder}/Credits-and-Licenses/."),
    'IT': ("Italiano", "Apri prima {guide}. L'unica patch in questa cartella è per una ROM italiana di HeartGold non modificata. Per una ROM Plus precedente o una lingua iniziale diversa, usa il pacchetto facoltativo {updater} della release ufficiale. Per aggiornare, conserva lingua del gioco, nome e percorso della ROM, file .sav originale e impostazioni Plus. Guide attuali in inglese: Originals/. Crediti e licenza: {folder}/Credits-and-Licenses/."),
    'FR': ("Français", "Ouvrez d'abord {guide}. Le seul correctif de ce dossier est destiné à une ROM française de HeartGold non modifiée. Pour une ancienne ROM Plus ou une autre langue de départ, utilisez le paquet facultatif {updater} de la version officielle. Pour une mise à jour, conservez la langue du jeu, le nom et l'emplacement de la ROM, le fichier .sav d'origine et les réglages Plus. Guides actuels en anglais : Originals/. Crédits et licence : {folder}/Credits-and-Licenses/."),
    'ES': ("Español", "Abre primero {guide}. El único parche de esta carpeta es para una ROM española de HeartGold sin modificar. Para una ROM Plus anterior u otro idioma de origen, usa el paquete opcional {updater} de la versión oficial. Al actualizar, conserva el idioma del juego, el nombre y la ubicación de la ROM, el archivo .sav original y los ajustes Plus. Guías actuales en inglés: Originals/. Créditos y licencia: {folder}/Credits-and-Licenses/."),
    'DE': ("Deutsch", "Öffne zuerst {guide}. Der einzige Patch in diesem Ordner ist für eine unveränderte deutsche HeartGold-ROM bestimmt. Für eine frühere Plus-ROM oder eine andere Ausgangssprache nutze das optionale Paket {updater} aus der offiziellen Veröffentlichung. Behalte beim Aktualisieren die Spielsprache, den ROM-Dateinamen und Speicherort, die ursprüngliche .sav-Datei und die Plus-Einstellungen bei. Aktuelle englische Spielanleitungen: Originals/. Danksagung und Lizenz: {folder}/Credits-and-Licenses/."),
}

_SOURCE_SIZE_LABELS = {'EN': 'Size (bytes)', 'IT': 'Dimensione (byte)',
                       'FR': 'Taille (octets)', 'ES': 'Tamaño (bytes)',
                       'DE': 'Größe (Bytes)'}


def localized_notice(locale: str) -> bytes:
    """Return the explicitly authored notice without a fallback language."""
    try:
        text = _NOTICES[locale]
    except KeyError as exc:
        raise ValueError('Unsupported player-notice locale: ' + str(locale)) from exc
    return text.format(project=PROJECT_URL, original=ORIGINAL_PLUS_URL).encode('utf-8')


def license_members(locale: str, license_bytes: bytes) -> dict[str, bytes]:
    """Return locale-relative notices after authenticating the English license."""
    notice = localized_notice(locale)
    if (not isinstance(license_bytes, bytes) or len(license_bytes) != LICENSE_BYTES
            or hashlib.sha256(license_bytes).hexdigest() != LICENSE_SHA256):
        raise ValueError('Player package requires the unchanged English GNU GPLv3 text')
    return {'Credits-and-Licenses/ABOUT.txt': notice,
            'Credits-and-Licenses/LICENSE.txt': license_bytes}


def _basename(value: str, label: str) -> str:
    if (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', value)
            or value.endswith('.') or value in ('.', '..')):
        raise ValueError('Invalid player-notice ' + label)
    return value


def start_here(version: str, package_revision: str, locale_folders: Mapping[str, str],
               updater_asset_name: str) -> bytes:
    """Name each installation PDF and the separate historical updater download."""
    version = _basename(version, 'version')
    package_revision = _basename(package_revision, 'package revision')
    updater_asset_name = _basename(updater_asset_name, 'updater asset name')
    if not updater_asset_name.lower().endswith('.zip'):
        raise ValueError('Player-notice updater asset must be a ZIP')
    if set(locale_folders) != set(LOCALES):
        raise ValueError('Player notices require exactly five locale folders')
    folders = {locale: _basename(locale_folders[locale], 'locale folder') for locale in LOCALES}
    if len({folder.casefold() for folder in folders.values()}) != len(LOCALES):
        raise ValueError('Player-notice locale folders must be distinct')
    lines = ['Sacred Gold Plus ' + version + ' — ' + package_revision, '', PROJECT_URL, '']
    for locale in LOCALES:
        folder = folders[locale]
        name, text = _START_TEXT[locale]
        guide = folder + '/Installation-' + version + '-' + locale + '.pdf'
        lines.extend([name + ' — ' + folder + '/',
                      text.format(guide=guide, updater=updater_asset_name, folder=folder), ''])
    return ('\n'.join(lines) + '\n').encode('utf-8')


def updater_readme(locale: str, version: str, target: Mapping, sources,
                   patch_names: Mapping[str, str]) -> bytes:
    """Render authored native instructions and a complete exact-source table."""
    from reference_docs import load_player_documents

    localized_notice(locale)  # Reject unsupported locales before loading documents.
    version = _basename(version, 'version')
    docs = load_player_documents(locale)
    sha, size = target.get('sha256', ''), target.get('bytes')
    if not re.fullmatch('[0-9a-f]{64}', sha) or not isinstance(size, int) or size <= 0:
        raise ValueError('Invalid updater target identity')
    rows, seen = [], set()
    for source in sources:
        source_id = _basename(source['id'], 'source ID')
        source_sha, patch = source.get('sha256', ''), patch_names.get(source_id)
        source_size = source.get('bytes')
        if (source_id in seen or not re.fullmatch('[0-9a-f]{64}', source_sha)
                or type(source_size) is not int or source_size <= 0
                or not isinstance(patch, str) or '\\' in patch
                or any(ord(c) < 32 or c == '|' for c in patch)):
            raise ValueError('Invalid updater source or patch')
        path = PurePosixPath(patch)
        if (path.is_absolute() or '..' in path.parts or path.as_posix() != patch
                or path.suffix != '.xdelta'):
            raise ValueError('Invalid updater patch path')
        rows.append(source_id + ' | ' + source_sha + ' | ' + str(source_size) + ' | ' + patch)
        seen.add(source_id)
    if not rows or set(patch_names) != seen:
        raise ValueError('Updater patch table must match its source IDs')
    lines = ['Sacred Gold Plus ' + version + ' — ' + locale, '',
             docs['d:label:updater_intro'], '', docs['d:install:4'], '',
             docs['d:install:12'], locale + ' / ' + version,
             'SHA-256: ' + sha, 'Bytes: ' + str(size), '',
             docs['d:label:source'] + ' ID | SHA-256 | ' + _SOURCE_SIZE_LABELS[locale]
             + ' | Patch', *rows, '', PROJECT_URL, '']
    return ('\n'.join(lines) + '\n').encode('utf-8')
