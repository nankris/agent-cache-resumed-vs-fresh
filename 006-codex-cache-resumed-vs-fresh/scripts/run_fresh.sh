#!/bin/bash
# Fresh arm: one new `codex exec` per package, same working dir, sequential. 2 reps in parallel.
E6=/workspace/work/tig/006-codex-cache-resumed-vs-fresh
H=/workspace/work/tig/_harness
FRESH=1 $H/chain.sh $E6 fresh 1 >> $E6/results/chain.log 2>&1 &
FRESH=1 $H/chain.sh $E6 fresh 2 >> $E6/results/chain.log 2>&1 &
wait
echo "ALL_DONE $(date -u +%s)" >> $E6/results/chain.log
