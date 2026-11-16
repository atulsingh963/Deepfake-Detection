# MINO Scope & Governance Specification

## 1. Primary Objectives
MINO is built to provide reliable, explainable, and privacy-conscious media forensics. It specifically addresses:
1. Facial manipulation detection across standard image formats (JPEG, PNG, WebP) and video formats (MP4, MOV, WebM).
2. Frame-level forensic breakdowns with interactive timeline scoring.
3. Cryptographic integrity logging and provenance tracking via SHA-256 and C2PA inspection.
4. Role-based operational access: User and Service Provider (Admin).

## 2. Non-Goals & Forensic Boundaries
- MINO **never** claims 100% certainty or acts as a definitive legal judge.
- MINO does not perform biometric facial recognition or identify private citizens.
- Detection of whole-scene synthetic generation (e.g. general diffusion art) is treated as a separate domain and not conflated with face-manipulation classifiers.
