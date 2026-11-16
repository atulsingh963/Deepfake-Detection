# MINO System Architecture

```mermaid
graph TD
    Client["Client Browser (React / TypeScript SPA)"]
    API["FastAPI REST Backend (V1)"]
    DB[("Relational Database")]
    Store["Private Media Storage"]
    Worker["Asynchronous Processing Engine"]
    ML["PyTorch Baseline Forensic Engine"]
    
    Client -->|HTTPS / JWT Auth| API
    API -->|Read / Write Metadata| DB
    API -->|Store Encrypted Assets| Store
    API -->|Submit Forensic Job| Worker
    Worker -->|Execute Preprocessing & Crops| Worker
    Worker -->|Inference Query| ML
    ML -->|Confidence & Frame Risk| Worker
    Worker -->|Write Analysis Results| DB
```

## Service Boundaries
1. **Frontend (`apps/web`)**: Single-page application rendering real-time job status, video risk timelines, and forensic reports.
2. **API (`apps/api`)**: High-performance asynchronous REST API handling auth, upload guards, and queries.
3. **Forensics Engine (`ml/src/mino_ml`)**: Neural network backbones, face detection cascades, and temporal risk aggregators.
