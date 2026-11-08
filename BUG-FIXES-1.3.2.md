# 1.3.2 source correction (unreleased)

The source fixes a repeatable **New Game reset after Mom's first conversation**
in English and Italian. A story variable was accessed before its new event bank
had been initialized; the 1.3.1 safety path reset the game. The corrected
source initializes that bank at the first valid access without changing the
save format. See the [measurement and limits](source/docs/validation/new-game-reset-1.3.2.md).

This is a source checkpoint, not a downloadable 1.3.2 update. The published
1.3.1 bug list remains [here](BUG-FIXES-1.3.1.md). The intermittent Latios
report has not been reproduced or declared fixed.
