# Sketchy <a href='https://github.com/esteinig'><img src='img/logo.png' align="right" height="250" /></a>

Real-time lineage matching and genotyping from uncorrected nanopore reads

![](https://img.shields.io/badge/version-alpha-red.svg)
![](https://img.shields.io/badge/lifecycle-experimental-orange.svg)
![](https://img.shields.io/badge/docs-latest-green.svg)
![](https://img.shields.io/badge/BioRxiv-prep-green.svg)

## Overview

**`v0.1-alpha: internal pre-release, no tests`**

`Sketchy` is an online lineage matching algorithm for real-time genotyping and susceptibility prediction in bacterial pathogens using nanopore sequencing platforms. In a nutshell, it is a variant of inexact lineage calling as implemented by [Brinda et al. (2019)](https://www.biorxiv.org/content/early/2018/08/29/403204). `Sketchy` uses MinHash distances to match reads to a representative population genomic sketch of the target organism. Because it relies on well characterized, high-quality genomes from the public domain, it is currently restricted to common pathogens for which we have sufficient data that can be processed with the [`pf-core/pf-survey`](https://github.com/pf-core) Nextflow pipeline, which currently supports *Staphylococcus aureus*, *Klebsiella pneumoniae* and *Mycobacterium tuberculosis* specific typing. *Burkholderia pseudomallei* with antibiotic resistance genotype using `ArDAP` annd other candidates are planned for beta release.

Preprint coming soon



