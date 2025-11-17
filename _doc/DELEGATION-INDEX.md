# Delegation Documentation - Start Here / Začněte Zde

## 🎯 Pro koho je tato dokumentace? / Who is this for?

Tato dokumentace je pro každého, kdo pracuje s **GitHub Copilot** v DIGiDIG projektu a chce porozumět konceptu **delegace** (delegation) úkolů na specializované agenty.

This documentation is for anyone working with **GitHub Copilot** in the DIGiDIG project and wants to understand the concept of **delegation** of tasks to specialized agents.

---

## 📚 Dokumentační Soubory / Documentation Files

### 1. 🚀 Quick Start - DELEGATION-QUICK-REFERENCE.md
**Začněte zde! / Start here!**

- ⏱️ Čtení: 5 minut / Reading time: 5 minutes
- 📋 Formát: Quick reference card / Rychlá referenční karta
- ✅ Ideální pro: Rychlé pochopení základů
- 🎯 Obsahuje:
  - Kdy delegovat / When to delegate
  - Workflow diagram
  - Klíčová pravidla / Key rules
  - Nejčastější chyby / Common mistakes
  - Kontrolní seznam / Checklist

**[→ Přejít na Quick Reference](DELEGATION-QUICK-REFERENCE.md)**

---

### 2. 📖 Complete Guide - DELEGATION-GUIDE.md
**Kompletní průvodce**

- ⏱️ Čtení: 15-20 minut / Reading time: 15-20 minutes
- 📋 Formát: Comprehensive guide / Komplexní průvodce
- ✅ Ideální pro: Hluboké porozumění konceptu
- 🎯 Obsahuje:
  - Co je delegace / What is delegation
  - Jak delegace funguje / How delegation works
  - Výhody a nevýhody / Pros and cons
  - Praktické příklady / Practical examples
  - Best practices pro DIGiDIG
  - FAQ sekce
  - Reference na další zdroje

**[→ Přejít na Complete Guide](DELEGATION-GUIDE.md)**

---

### 3. 📊 Visual Diagrams - DELEGATION-DIAGRAMS.md
**Vizuální diagramy**

- ⏱️ Čtení: 10 minut / Reading time: 10 minutes
- 📋 Formát: ASCII flow diagrams / Vývojové diagramy
- ✅ Ideální pro: Vizuální učení
- 🎯 Obsahuje:
  - Basic delegation flow
  - Decision trees / Rozhodovací stromy
  - Success/failure flows
  - Multi-agent scenarios
  - Context flow / Tok kontextu
  - Comparison diagrams / Srovnání

**[→ Přejít na Diagrams](DELEGATION-DIAGRAMS.md)**

---

## 🎓 Doporučené Pořadí Studia / Recommended Study Order

### Pro Začátečníky / For Beginners

1. **Quick Reference** (5 min) - Získej základní přehled
2. **Diagrams** (10 min) - Vizualizuj si koncept
3. **Complete Guide** (20 min) - Ponořte se do detailů

### Pro Pokročilé / For Advanced Users

1. **Quick Reference** - Rychlá rekapitulace
2. **Complete Guide** - Specific sections as needed
3. **Diagrams** - Reference při řešení konkrétních problémů

### Pro Týmové Lead / For Team Leads

1. **Complete Guide** - Celá dokumentace
2. **Quick Reference** - Pro týmovou distribuci
3. **Diagrams** - Pro prezentace a školení

---

## 🔍 Rychlé Odpovědi / Quick Answers

### Co je delegace?
Delegace je proces předání úkolu z hlavního GitHub Copilot agenta na specializovaného custom agenta.

**→ Více info:** [DELEGATION-GUIDE.md](DELEGATION-GUIDE.md#co-je-to-delegace--what-is-delegation)

### Kdy mám delegovat?
Deleguj složité úkoly, kdy existuje vhodný custom agent (Python, Docker, docs, atd.).

**→ Více info:** [DELEGATION-QUICK-REFERENCE.md](DELEGATION-QUICK-REFERENCE.md#-kdy-delegovat--when-to-delegate)

### Jak funguje workflow delegace?
Hlavní agent → deleguje → custom agent → vrátí výsledek → hlavní agent pokračuje (bez review!).

**→ Více info:** [DELEGATION-DIAGRAMS.md](DELEGATION-DIAGRAMS.md#basic-delegation-flow--základní-tok-delegace)

### Co dělat po delegaci?
NIČEHO! Důvěřuj výsledku custom agenta a pokračuj na další úkol.

**→ Více info:** [DELEGATION-GUIDE.md](DELEGATION-GUIDE.md#pravidla-pro-hlavního-agenta--rules-for-main-agent)

### Jaké custom agenty jsou k dispozici?
Python expert, Docker expert, Documentation expert, Testing expert, Merge conflict resolver...

**→ Více info:** [DELEGATION-GUIDE.md](DELEGATION-GUIDE.md#příklady-custom-agentů-v-digidig--custom-agent-examples-in-digidig)

---

## 🛠️ Praktické Příklady / Practical Examples

### Scénář: Refactoring Python Servisu

```markdown
Úkol: "Refactoruj identity service podle ServiceServer patternu"

1. Hlavní agent zkontroluje dostupnost python_expert agenta
2. Deleguje s kontextem: "DIGiDIG používá ServiceServer base class"
3. Python expert provede refactoring a testy
4. Hlavní agent přijme výsledek BEZ review
5. Pokračuje na další úkol
```

**→ Podrobný příklad:** [DELEGATION-GUIDE.md - Workflow](DELEGATION-GUIDE.md#workflow-delegace-v-digidig-projektu--delegation-workflow-in-digidig-project)

### Scénář: Aktualizace Dokumentace

```markdown
Úkol: "Aktualizuj API dokumentaci pro nové endpointy"

1. Hlavní agent identifikuje změny v API
2. Deleguje na documentation_expert s detaily
3. Documentation expert aktualizuje docs s konzistentním stylem
4. Hlavní agent přijme výsledek
5. Reportuje pokrok uživateli
```

**→ Podrobný příklad:** [DELEGATION-GUIDE.md - Scénář 2](DELEGATION-GUIDE.md#scénář-2-aktualizace-dokumentace)

---

## ❓ FAQ - Nejčastější Otázky

| Otázka | Odpověď | Link |
|--------|---------|------|
| Musím konfigurovat custom agenty? | Ne, jsou automaticky dostupné | [FAQ](DELEGATION-GUIDE.md#q-musím-custom-agenty-konfigurovat) |
| Může custom agent udělat chybu? | Ano, ale hlavní agent by měl důvěřovat výsledku | [FAQ](DELEGATION-GUIDE.md#q-co-když-custom-agent-udělá-chybu) |
| Je delegace rychlejší? | Ano, díky specializaci a absenci review | [FAQ](DELEGATION-GUIDE.md#q-je-delegace-rychlejší) |
| Co když agent neexistuje? | Hlavní agent dělá úkol sám | [Decision Tree](DELEGATION-DIAGRAMS.md#decision-tree--rozhodovací-strom) |

---

## 🎯 Klíčové Principy / Key Principles

### ⚠️ 4 ZLATÁ PRAVIDLA / 4 GOLDEN RULES

1. **VŽDY NEJPRVE DELEGUJ**
   Pokud existuje custom agent, zkus delegovat před tím, než začneš sám.

2. **POSKYTNI KOMPLETNÍ KONTEXT**
   Custom agent nemá tvůj kontext, předej mu všechny potřebné informace.

3. **DŮVĚŘUJ VÝSLEDKU**
   Po úspěšné delegaci NEPROVÁDÍŠ review, validaci, nebo testy.

4. **POUZE PŘI SELHÁNÍ INTERVENUJ**
   Custom agent hlásí problém? Zkus znovu s lepšími instrukcemi.

**→ Detailní pravidla:** [DELEGATION-GUIDE.md - Pravidla](DELEGATION-GUIDE.md#⚠️-kritická-pravidla-při-delegaci--critical-delegation-rules)

---

## 📊 Srovnání: S vs Bez Delegace

| Aspekt | BEZ Delegace | S Delegací |
|--------|--------------|------------|
| ⏱️ Čas | 20+ minut | 5 minut |
| 🎯 Kvalita | Střední | Vysoká (expert) |
| ⚠️ Riziko chyb | Střední-Vysoké | Nízké |
| 🔄 Iterace | Mnoho | Minimum |
| ✅ Testování | Manuální | Automatické (agent) |

**→ Vizuální srovnání:** [DELEGATION-DIAGRAMS.md - Comparison](DELEGATION-DIAGRAMS.md#comparison-with-vs-without-delegation)

---

## 🔗 Související Dokumentace / Related Documentation

### DIGiDIG Projekt
- [README.md](../README.md) - Hlavní dokumentace projektu
- [.github/instructions.md](../.github/instructions.md) - Copilot instrukce
- [API-ENDPOINTS.md](API-ENDPOINTS.md) - API reference

### GitHub Copilot
- [GitHub Copilot Official Docs](https://docs.github.com/en/copilot)
- [GitHub Copilot Workspace](https://githubnext.com/projects/copilot-workspace)

---

## 💡 Tipy a Triky / Tips & Tricks

### ✅ DO - Dělej
- Deleguj složité úkoly
- Poskytni kontext
- Důvěřuj expertům
- Používej Quick Reference

### ❌ DON'T - Nedělej
- Review po úspěšné delegaci
- Deleguj triviální úkoly
- Zapomínej na kontext
- Ignoruj selhání agenta

**→ Více tipů:** [DELEGATION-GUIDE.md - Best Practices](DELEGATION-GUIDE.md#best-practices-pro-digidig-projekt)

---

## 📝 Kontrolní Seznam / Checklist

### Před Delegací
- [ ] Existuje custom agent pro tuto oblast?
- [ ] Je úkol dostatečně složitý?
- [ ] Mám všechny informace pro kontext?
- [ ] Je úkol jasně definovaný?

### Po Delegaci
- [ ] Custom agent hlásí úspěch?
  - **ANO** → Přijmi výsledek bez změn
  - **NE** → Zkus znovu s lepšími instrukcemi

**→ Kompletní checklist:** [DELEGATION-GUIDE.md - Checklist](DELEGATION-GUIDE.md#kontrolní-seznam--checklist)

---

## 🎓 Další Kroky / Next Steps

1. **Přečti Quick Reference** (5 min)
   - Získej základní přehled konceptu

2. **Projdi Complete Guide** (20 min)
   - Ponořte se do detailů

3. **Prohlédni si Diagrams** (10 min)
   - Vizualizuj workflow

4. **Vyzkoušej v praxi!**
   - Aplikuj znalosti na reálných úkolech v DIGiDIG

---

## 📞 Podpora / Support

Máš otázky nebo návrhy na vylepšení dokumentace?

1. Otevři issue v GitHub repository
2. Kontaktuj týmové lead
3. Přidej komentář do JIRA ticketu DIGIDIG-10

---

## 📜 Historie Změn / Changelog

| Datum | Verze | Změny |
|-------|-------|-------|
| 2025-11-10 | 1.0 | Iniciální vytvoření všech dokumentů |

---

## 📄 Licence / License

Tato dokumentace je součástí DIGiDIG projektu a podléhá stejné licenci jako projekt.

---

**Happy Delegating! / Šťastné Delegování!** 🚀

*Pro aktualizace sleduj: [DIGiDIG Repository](https://github.com/PavelPerna/DIGiDIG)*
