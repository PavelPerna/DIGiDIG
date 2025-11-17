# Delegation Flow Diagram

## Basic Delegation Flow / Základní Tok Delegace

```
┌─────────────────────────────────────────────────────────────────┐
│                         UŽIVATEL / USER                          │
│                  "Refactoruj identity service"                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HLAVNÍ AGENT / MAIN AGENT                      │
│                    (Coding Agent)                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Analyzuje požadavek / Analyzes request                       │
│ 2. Identifikuje typ úkolu: Python refactoring                   │
│ 3. Kontroluje dostupné nástroje / Checks available tools        │
│ 4. Nalezne: python_expert custom agent                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │   DELEGACE?   │
                     │   DELEGATE?   │
                     └───────┬───────┘
                             │
                ┌────────────┴────────────┐
                │                         │
               ANO                       NE
               YES                       NO
                │                         │
                ▼                         ▼
┌───────────────────────────┐   ┌─────────────────────┐
│    CUSTOM AGENT           │   │  Hlavní agent dělá  │
│    (python_expert)        │   │  Main agent does it │
├───────────────────────────┤   └─────────────────────┘
│ • Vlastní kontext         │
│ • Specializované nástroje │
│ • Best practices          │
│                           │
│ PROVEDE:                  │
│ 1. Načte identity.py      │
│ 2. Refactoruje kód        │
│ 3. Spustí testy           │
│ 4. Ověří výsledek         │
└───────────┬───────────────┘
            │
            ▼
    ┌───────────────┐
    │   VÝSLEDEK    │
    │   RESULT      │
    └───────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HLAVNÍ AGENT / MAIN AGENT                      │
├─────────────────────────────────────────────────────────────────┤
│ ✅ Přijme výsledek BEZ review                                   │
│    Accepts result WITHOUT review                                │
│                                                                  │
│ ❌ NEDĚLÁ validaci                                              │
│    Does NOT validate                                            │
│                                                                  │
│ ✅ Pokračuje na další úkol                                      │
│    Continues to next task                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOKONČENO / DONE                            │
│              Reportuje pokrok uživateli                          │
│              Reports progress to user                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decision Tree / Rozhodovací Strom

```
                         ┌─────────────┐
                         │  NOVÝ ÚKOL  │
                         │  NEW TASK   │
                         └──────┬──────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Je úkol dostatečně    │
                    │ složitý?              │
                    │ Is task complex?      │
                    └──────┬────────────────┘
                           │
                  ┌────────┴────────┐
                  │                 │
                 ANO               NE
                 YES               NO
                  │                 │
                  ▼                 ▼
      ┌────────────────────┐   ┌──────────────┐
      │ Existuje custom    │   │ Dělej sám    │
      │ agent pro oblast?  │   │ Do yourself  │
      │ Custom agent       │   └──────────────┘
      │ exists?            │
      └──────┬─────────────┘
             │
    ┌────────┴────────┐
    │                 │
   ANO               NE
   YES               NO
    │                 │
    ▼                 ▼
┌───────────────┐  ┌──────────────┐
│   DELEGUJ     │  │  Dělej sám   │
│   DELEGATE    │  │  Do yourself │
└───────────────┘  └──────────────┘
```

---

## Success Flow / Tok Úspěchu

```
┌─────────────┐
│  Hlavní     │
│  Agent      │
│  Main Agent │
└──────┬──────┘
       │
       │ Delegace / Delegation
       ▼
┌─────────────┐      ┌────────────────────────┐
│   Custom    │─────▶│ Pracuje nezávisle      │
│   Agent     │      │ Works independently    │
└──────┬──────┘      └────────────────────────┘
       │
       │ Vrací výsledek / Returns result
       ▼
┌─────────────┐      ┌────────────────────────┐
│  Hlavní     │─────▶│ ✅ Přijímá bez review │
│  Agent      │      │    Accepts w/o review  │
└──────┬──────┘      └────────────────────────┘
       │
       │ Pokračuje / Continues
       ▼
┌─────────────┐
│  Další úkol │
│  Next task  │
└─────────────┘
```

---

## Failure Flow / Tok Selhání

```
┌─────────────┐
│  Hlavní     │
│  Agent      │
│  Main Agent │
└──────┬──────┘
       │
       │ Delegace / Delegation
       ▼
┌─────────────┐      ┌────────────────────────┐
│   Custom    │─────▶│ Pracuje na úkolu       │
│   Agent     │      │ Works on task          │
└──────┬──────┘      └────────────────────────┘
       │
       │ Hlásí problém / Reports problem
       ▼
┌─────────────┐      ┌────────────────────────┐
│  Hlavní     │─────▶│ Zkusí znovu s lepšími  │
│  Agent      │      │ instrukcemi            │
└──────┬──────┘      │ Retries with better    │
       │             │ instructions           │
       │             └────────────────────────┘
       │
       │ Opakované selhání / Repeated failure
       ▼
┌─────────────┐      ┌────────────────────────┐
│  Hlavní     │─────▶│ Dělá úkol sám          │
│  Agent      │      │ Does task itself       │
└─────────────┘      └────────────────────────┘
```

---

## Multi-Agent Scenario / Scénář s Více Agenty

```
┌──────────────────────────────────────────────────────┐
│            KOMPLEXNÍ ÚKOL / COMPLEX TASK             │
│  "Implementuj nový API endpoint s testy a dokumentací│
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   HLAVNÍ AGENT        │
         │   MAIN AGENT          │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │ Rozdělí na 3 pod-úkoly│
         │ Splits into 3 subtasks│
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────┐    ┌──────────┐    ┌──────────┐
│ Python  │    │ Testing  │    │   Docs   │
│ Expert  │    │ Expert   │    │  Expert  │
└────┬────┘    └────┬─────┘    └────┬─────┘
     │              │               │
     │ Implementace │ Unit testy    │ API docs
     │              │               │
     └──────────────┼───────────────┘
                    │
                    ▼
         ┌───────────────────────┐
         │   HLAVNÍ AGENT        │
         │ Spojí výsledky        │
         │ MAIN AGENT            │
         │ Combines results      │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  HOTOVO / DONE        │
         └───────────────────────┘
```

---

## Context Flow / Tok Kontextu

```
┌───────────────────────────────────────────┐
│         HLAVNÍ AGENT                      │
│         MAIN AGENT                        │
│                                           │
│  Kontext:                                 │
│  • Celý repository                        │
│  • Historie konverzace                    │
│  • Předchozí kroky                        │
│  • Uživatelské instrukce                  │
└────────────────┬──────────────────────────┘
                 │
                 │ Předává kontext
                 │ Passes context
                 ▼
┌───────────────────────────────────────────┐
│   DELEGACE S KONTEXTEM                    │
│   DELEGATION WITH CONTEXT                 │
│                                           │
│   {                                       │
│     "task": "Refactor identity.py",       │
│     "pattern": "ServiceServer",           │
│     "file": "services/identity/...",      │
│     "context": "DIGiDIG uses class-based" │
│   }                                       │
└────────────────┬──────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────┐
│         CUSTOM AGENT                      │
│                                           │
│  Vlastní kontext:                         │
│  • Pouze předaný kontext                  │
│  • Specializované znalosti                │
│  • Best practices                         │
│  • Přístup k repository                   │
└────────────────┬──────────────────────────┘
                 │
                 │ Vrací výsledek
                 │ Returns result
                 ▼
┌───────────────────────────────────────────┐
│         HLAVNÍ AGENT                      │
│         MAIN AGENT                        │
│                                           │
│  Obnovený kontext:                        │
│  • Původní kontext +                      │
│  • Výsledek od custom agenta              │
└───────────────────────────────────────────┘
```

---

## Comparison: With vs Without Delegation

### BEZ DELEGACE / WITHOUT DELEGATION
```
┌─────────────┐
│ Hlavní      │  1. Načti soubor
│ Agent       │  2. Analyzuj kód
│             │  3. Refactoruj
│             │  4. Testuj
│             │  5. Oprav chyby
│             │  6. Znovu testuj
└─────────────┘
      │
      │ Čas: 20+ minut / Time: 20+ minutes
      │ Riziko: Střední-Vysoké / Risk: Medium-High
      ▼
┌─────────────┐
│  Výsledek   │
└─────────────┘
```

### S DELEGACÍ / WITH DELEGATION
```
┌─────────────┐
│ Hlavní      │  1. Deleguj na python_expert
│ Agent       │  2. Přijmi výsledek
└─────────────┘  3. Pokračuj
      │
      │ Čas: 5 minut / Time: 5 minutes
      │ Riziko: Nízké / Risk: Low
      ▼
┌─────────────┐
│  Výsledek   │  (Expert provedl všechny kroky)
└─────────────┘  (Expert did all steps)
```

---

## Agent Hierarchy / Hierarchie Agentů

```
                    ┌────────────────┐
                    │  UŽIVATEL      │
                    │  USER          │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ HLAVNÍ AGENT   │
                    │ MAIN AGENT     │
                    │ (Orchestrator) │
                    └────────┬───────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌──────────┐      ┌──────────┐       ┌──────────┐
   │ Python   │      │ Docker   │       │   Docs   │
   │ Expert   │      │ Expert   │       │  Expert  │
   └──────────┘      └──────────┘       └──────────┘
   
   (Specialized)     (Specialized)      (Specialized)
```

---

*Diagram vytvořen: 2025-11-10*
*Pro více informací viz: DELEGATION-GUIDE.md*
