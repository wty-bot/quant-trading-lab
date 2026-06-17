# RiceQuant A Share Backtest Dataset

This directory contains the curated static dataset for the RiceQuant A-share final project backtests.

Use `manifest.json` as the authoritative file map. Strategy code should read files from this directory and should not call RQData dynamically during backtests.

Main coverage: 2005-01-04 to 2026-06-16 prices; 259 monthly rebalance snapshots from 2005-01-31 to 2026-06-16.
