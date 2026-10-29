# HGSS interface refinement contract

Scope: the maintainer's 1.3-dev follow-up, 28 October 2026. Preserve the game's
pixel-based identity and every existing save/settings identifier. This is a
refinement of native screens, not a replacement visual world.

The reference is the actual supported HGSS EN/IT cartridge and pinned
`pret/pokeheartgold` revision `0985e8718df4f25e64d6507d89c0c97c0d288981`.
The Impeccable Operate/Read, extraction, polish and craft guidance informs the
hierarchy and consistency review. Its local context launcher was not executable;
existing source and actual emulator captures provide the visual authority.

## Native rules and intended changes

- Two 256×192 screens, 8px tile grid, native font0 and localized EN/IT strings.
  No web-like typography, external font, scaling or permanent framebuffer.
- Native field icon frame: 40×26 visible pixels, 2px border with cut corners,
  at `(104,142)` for the eighth cell. Place it on BG4 below the native BG5
  labels so shared tile rows cannot clip Options. Use the actual normal/selected icon palette,
  not the font palette. Center an original book glyph in that frame. Preserve
  the native label color `0x0E0200` and centered label window.
- Native touch rectangles are 60×32. Guide remains reachable with X, D-pad and A
  and directly by stylus. A brief nine-frame page-turn acknowledgement matches
  native confirmation timing. B/X cancels pending activation; never dispatch the
  previously selected native item while Guide confirmation is pending.
- Guide is a Read surface: category, selected subject, page/entry position and
  actions have distinct roles. Keep five 24px list rows and seven 16px detail
  lines. Use native palette colors, thin beveled rows, a clear selected state,
  a subject band and visible page/reference controls. Reflow text to 208px for
  an 8px inner margin; stable entry IDs and factual content remain unchanged.
- Give the IV consultant a dedicated orange variation of the native delivery
  model, near the lower-left Mart plant on a verified walkable tile. Preserve
  original postmen, NPCs and collision routes. Build the variation from the
  user's cartridge at build time; never distribute extracted graphics in Git.
- Native Options and Plus currently have separate pending-change transactions.
  Use the explicitly permitted fallback: an always-visible, touchable Plus
  button in the native footer, retaining SELECT access and native A/B semantics.
  A fake page counter would imply shared transactions that do not exist.

## References and acceptance

The [official HGSS overview](https://www.pokemon.com/us/pokemon-video-games/pokemon-heartgold-and-soulsilver-versions)
explicitly supports both touch and buttons. The
[expansion dynamic-menu documentation](https://rh-hideout.github.io/pokeemerald-expansion/tutorials/how_to_dynmultichoice.html)
provides a useful comparison for visible row counts, selection and cleanup;
it does not establish DS compatibility. Native geometry/palettes and actual
256×192 captures remain the deciding evidence here.

Acceptance requires native EN/IT captures for normal, selected and pressed
states; touch and D-pad entry/exit; full Guide traversal and references; repeated
ownership cleanup; Options cancel/apply/preview; consultant interaction and
original NPC preservation; and native SAVE/cold Continue on copies of older
saves. Assess visual layout and behavior together. Finite tests do not certify
all adventure, hardware or wireless states.
