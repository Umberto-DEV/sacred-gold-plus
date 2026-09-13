# ANIM2 — moto continuo in lotta

`sgp.anim2` estende il moto procedurale v4 a tutti i lottatori e lo mantiene
nei menu di lotta. Tre cancelli sospendono ogni scrittura durante animazioni di
mossa, ingresso della specie e animazioni native del Pokepic. La politica dei
nove siti di fermata sopprime soltanto `IO-BARRA`, `BORSA` e `SQUADRA`; gli
altri siti fermano e puliscono tutti i lottatori.

Il blocco occupa 2048 byte a `0x023DB500`. Codice, canarino, tabelle, parametri,
nove valori `lr`, stato e quattro slot hanno regioni separate. L'opzione usa il
campo `anim` del chunk condiviso e resta spenta per difetto.

Ricostruzione autonoma:

```sh
python3 source/features/anim2/tools/compila_anim2.py \
  --uscita /tmp/anim2-build --livello 5b
```

Suite A, senza ROM: `test_metadata.py`. Suite B, con ARM9/ov012 estratti:
`test_blob5.py` con `SGP_MODULI`; applicatore, rilettore e mutanti usano
`SGP_ROM_BASE` e `SGP_ROM_ANIM2`. I test Unicorn/headless JIT possono richiedere
esecuzione fuori sandbox su macOS.
