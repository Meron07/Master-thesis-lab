# IEC-104 and GOOSE Replay Detection Lab

This repository contains the lab implementation, scripts, experiment results, and setup notes for replay attack detection in smart-grid communication protocols.

## Protocols

- IEC 60870-5-104
- IEC 61850 GOOSE

## Lab environment

The experiments were performed in an isolated virtual lab using Kali Linux and Ubuntu.

- Kali Linux: packet capture, replay testing, feature extraction, and evaluation
- Ubuntu: protocol-side environment using lib60870 and libiec61850

## Repository structure

- `scripts/` - detection, feature extraction, and evaluation scripts
- `results/` - CSV files, summaries, and experiment outputs
- `figures/` - generated graphs and plots
- `data/processed/` - processed feature data
- `data/sample_pcaps/` - small sample packet captures only
- `docs/` - setup and experiment documentation

## Note

The thesis document itself is not included in this repository.

## Ethical use

This repository is for academic and defensive cybersecurity research only. All experiments were performed in an isolated lab environment.
