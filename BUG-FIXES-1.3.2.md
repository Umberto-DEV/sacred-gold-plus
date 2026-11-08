# 1.3.2 changes and validation

The New Game correction initializes an empty event bank before the first
redirected story-variable access, preventing the reset after Mom's first
conversation. Save layouts and identifiers remain stable. The
[original diagnosis](source/docs/validation/new-game-reset-1.3.2.md) retains its
predecessor/probe hashes; the [current validation report](source/docs/validation/localization-1.3.2.md)
records the five-language candidate identities, bounded acceptance checks and limits.

French, Spanish and German presentation uses matching retail resources and
explicit Sacred Gold/Plus translations. Localized menus, onboarding, EV/IV
help, Fairy labels and accent keys share the current gameplay implementation.
Player PDFs are generated from each candidate's actual rules and names.

The French Options entry was traced to a footer that fit an ordinary text line
but exceeded the native button-cap layout. The audit also exposed Spanish
selector/confirmation footers and French/German exit action bars. Copy was
shortened, and composition now checks cap/gap and combined action-bar geometry
before emitting resources. Native glyph and width bounds remain enforced.
Ordinary field dialogue receives context-specific native line/scroll layout;
this does not claim a generic reflow of every game menu.

The package has five current targets and 150 direct routes from 30 recognized
original/historical inputs. Byte-reconstruction checks are separate from
representative raw-save Continue/SAVE/cold-restart testing and UI captures.
The acceptance report owns exact results; host checks do not imply a physical
device run or a full playthrough.

The published [1.3.1 bug list](BUG-FIXES-1.3.1.md) remains historical evidence.
The intermittent Latios report has not been reproduced or declared fixed.
