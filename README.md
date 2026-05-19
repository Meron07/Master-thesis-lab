# IEC-104 and GOOSE Replay Detection Lab

This repository contains the lab implementation, experiment scripts, processed data, figures, and results for replay attack detection in smart-grid communication protocols.

The work focuses on two protocols:

- IEC 60870-5-104
- IEC 61850 GOOSE

The thesis document itself is not included in this repository.

## Lab environment

The experiments were performed in an isolated virtual lab using Kali Linux and Ubuntu.

- Kali Linux: packet capture, replay testing, feature extraction, detection, and evaluation
- Ubuntu: protocol-side environment using lib60870 and libiec61850

No real industrial system or production network was used.

## Repository structure

```text
.
├── docs/                  Setup notes and experiment documentation
├── scripts/
│   ├── iec104/             IEC-104 detection scripts
│   ├── goose/              GOOSE detection scripts
│   └── evaluation/         Evaluation and metric scripts
├── data/
│   ├── processed/          Processed feature data
│   └── sample_pcaps/       Optional small sample packet captures
├── results/
│   ├── iec104/             IEC-104 result files
│   ├── goose/              GOOSE result files
│   └── summary/            Summary outputs
└── figures/
    ├── iec104/             IEC-104 plots
    └── goose/              GOOSE plots
