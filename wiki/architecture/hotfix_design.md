# System Design Spec: Bug Fix Toggle
**Stato**: `In Corso`

## Modifiche Architetturali:
1. Introdurre uno stato `isUpdating` nel componente React dei task per disabilitare il click durante le modifiche asincrone.
2. Aggiungere una funzione helper `debounce` per prevenire click multipli.