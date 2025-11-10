# GitHub Copilot Delegation Guide

## Co je to Delegace? / What is Delegation?

**Česky:**
Delegace (delegation) je funkce GitHub Copilot, která umožňuje hlavnímu agentovi (coding agent) předávat specifické úkoly specializovaným agentům (custom agents). Tyto custom agents mají expertní znalosti v konkrétních oblastech a vlastní sadu nástrojů.

**English:**
Delegation is a GitHub Copilot feature that allows the main agent (coding agent) to pass specific tasks to specialized agents (custom agents). These custom agents have expert knowledge in specific areas and their own set of tools.

---

## Jak Funguje Delegace? / How Does Delegation Work?

### Základní Princip / Basic Principle

1. **Hlavní Agent (Main Coding Agent)**
   - Analyzuje požadavek uživatele
   - Rozhodne, zda může úkol vyřešit sám, nebo potřebuje specialistu
   - Pokud existuje vhodný custom agent, deleguje mu úkol
   - Přijímá výsledek od custom agenta a pokračuje v práci

2. **Custom Agent (Specialized Agent)**
   - Zaměřen na konkrétní oblast (např. Python kód, dokumentace, merge konflikty)
   - Má vlastní instrukce a kontext
   - Pracuje nezávisle na hlavním agentovi
   - Vrací výsledek zpět hlavnímu agentovi

### Výhody Delegace / Benefits of Delegation

✅ **Specializace** - Custom agents mají hluboké znalosti v konkrétní oblasti
✅ **Efektivita** - Úkol je řešen tím nejlepším "expertem"
✅ **Kvalita** - Specializovaný agent často poskytne lepší výsledek
✅ **Nezávislost** - Custom agent pracuje ve vlastním kontextu
✅ **Rychlost** - Specializované nástroje a postupy

---

## Kdy Použít Delegaci? / When to Use Delegation?

### Příklady Vhodných Situací / Good Use Cases

1. **Složité Merge Konflikty**
   ```
   Uživatel: "Vyřeš merge konflikt v souboru identity.py"
   → Deleguje na "merge_conflict_resolver" custom agenta
   ```

2. **Refactoring Python Kódu**
   ```
   Uživatel: "Přepiš tento modul podle best practices"
   → Deleguje na "python_expert" custom agenta
   ```

3. **Aktualizace Dokumentace**
   ```
   Uživatel: "Aktualizuj README s novými API endpointy"
   → Deleguje na "documentation_expert" custom agenta
   ```

4. **Testování**
   ```
   Uživatel: "Napiš unit testy pro nový modul"
   → Deleguje na "testing_expert" custom agenta
   ```

### Kdy NEPOUŽÍVAT Delegaci / When NOT to Use Delegation

❌ **Jednoduché úkoly** - Malé změny zvládne hlavní agent rychleji
❌ **Neexistující custom agent** - Pokud není agent pro danou oblast
❌ **Explorace** - Při zkoumání neznámého kódu je lepší hlavní agent
❌ **Cross-domain úkoly** - Úkoly vyžadující znalosti více oblastí

---

## Jak Poznat, že je k Dispozici Custom Agent? / How to Recognize Available Custom Agents?

### V GitHub Copilot Workspace

Custom agents se objevují jako **nástroje (tools)** dostupné hlavnímu agentovi. Jejich popis začíná textem:

```
"Custom agent: [popis specializace]"
```

### Příklad
```
Tool: python_code_editor
Description: "Custom agent: Expert v Python kódu s nástroji pro refactoring a best practices"
```

---

## Workflow Delegace v DIGiDIG Projektu / Delegation Workflow in DIGiDIG Project

### Scénář 1: Oprava Služby (Service Fix)

**Uživatel říká:** "Oprav problém s autentizací v identity service"

**Hlavní Agent:**
1. ✅ Prozkoumá problém
2. ✅ Zjistí, že jde o Python kód
3. ✅ Zkontroluje, zda existuje "python_expert" custom agent
4. ✅ **Deleguje** úkol na custom agenta s kontextem
5. ✅ Přijme hotový kód od custom agenta
6. ✅ **NEDĚLÁ** review ani validaci (důvěřuje expertovi!)
7. ✅ Pokračuje na další úkol

**Custom Agent:**
1. Přijme kontext a instrukce
2. Provede analýzu kódu
3. Implementuje opravu
4. Testuje řešení
5. Vrátí výsledek

### Scénář 2: Aktualizace Dokumentace

**Uživatel říká:** "Aktualizuj API dokumentaci pro nové endpointy"

**Hlavní Agent:**
1. ✅ Identifikuje změny v API
2. ✅ Zkontroluje existenci "documentation_expert" agenta
3. ✅ **Deleguje** s informacemi o nových endpointech
4. ✅ Přijme aktualizovanou dokumentaci
5. ✅ **NEDĚLÁ** úpravy (důvěřuje expertovi!)
6. ✅ Reportuje pokrok uživateli

---

## Pravidla pro Hlavního Agenta / Rules for Main Agent

### ⚠️ KRITICKÁ PRAVIDLA PŘI DELEGACI / CRITICAL DELEGATION RULES

1. **VŽDY NEJPRVE DELEGUJ** / **ALWAYS DELEGATE FIRST**
   - Pokud existuje relevantní custom agent, **VŽDY** zkus delegovat
   - Pouze pokud delegace selže, řeš úkol sám

2. **POSKYTNI KOMPLETNÍ KONTEXT** / **PROVIDE COMPLETE CONTEXT**
   - Custom agent nemá přístup k tvému kontextu
   - Předej všechny potřebné informace
   - Jasně formuluj, co má agent udělat

3. **DŮVĚŘUJ VÝSLEDKU** / **TRUST THE RESULT**
   - Po úspěšné delegaci **NEPROVÁDÍŠ** review
   - **NEVALIDUJEŠ** změny
   - **NEUPRAVUJEŠ** kód custom agenta
   - **NEDĚLEJ** build nebo testy (pokud agent hlásí úspěch)

4. **POUZE PŘI SELHÁNÍ INTERVENUJ** / **ONLY INTERVENE ON FAILURE**
   - Pokud custom agent hlásí problém, zkus to znovu s lepšími instrukcemi
   - Po opakovaném selhání můžeš zkusit úkol sám

---

## Příklady Custom Agentů v DIGiDIG / Custom Agent Examples in DIGiDIG

### Možné Custom Agents (příklady)

1. **python_code_expert**
   - Specializace: Python kód, FastAPI, async/await
   - Použití: Refactoring, nové funkce, opravy bugů v Python souborech
   - Nástroje: Linting, testing, code analysis

2. **merge_conflict_resolver**
   - Specializace: Řešení git merge konfliktů
   - Použití: Složité konflikty při mergování větví
   - Nástroje: Git diff, conflict markers analysis

3. **documentation_expert**
   - Specializace: Markdown dokumentace, API docs
   - Použití: Aktualizace README, vytváření dokumentace
   - Nástroje: Markdown validation, link checking

4. **docker_expert**
   - Specializace: Docker, docker-compose, kontejnerizace
   - Použití: Dockerfile optimalizace, docker-compose konfigurace
   - Nástroje: Docker build, layer analysis

5. **testing_expert**
   - Specializace: Unit testy, integrační testy, pytest
   - Použití: Psaní testů pro nové funkce
   - Nástroje: pytest, coverage analysis

---

## Praktické Příklady / Practical Examples

### Příklad 1: Delegace Python Refactoringu

**Špatně (bez delegace):**
```
Hlavní agent:
1. Načte soubor identity.py
2. Ručně upraví kód
3. Spustí testy
4. Opraví chyby
5. Znovu testuje
→ Časově náročné, možné chyby
```

**Správně (s delegací):**
```
Hlavní agent:
1. Zkontroluje dostupnost python_code_expert agenta
2. Deleguje: "Refactoruj identity.py podle ServiceServer pattern"
3. Custom agent provede refactoring včetně testů
4. Hlavní agent přijme výsledek a pokračuje
→ Rychlé, kvalitní, efektivní
```

### Příklad 2: Aktualizace Dokumentace

**Špatně (bez delegace):**
```
Hlavní agent:
1. Manuálně upravuje README.md
2. Možné chyby ve formátování
3. Nekonzistentní styl
```

**Správně (s delegací):**
```
Hlavní agent:
1. Deleguje na documentation_expert
2. Agent zajistí konzistentní formát a styl
3. Hlavní agent přijme hotovou dokumentaci
```

---

## Jak Delegovat z Pohledu Kódu / How to Delegate from Code Perspective

### Delegace Není Přímé Volání Funkce

Custom agents **NEJSOU** Python funkce nebo API endpointy!

**Delegace funguje jako:**
- Nástroj (tool) dostupný hlavnímu agentovi
- Agent se "rozhodne" použít tento nástroj
- Nástroj předá úkol custom agentovi
- Custom agent pracuje nezávisle
- Výsledek se vrátí zpět

### Konceptuální Příklad

```python
# TOTO NENÍ REÁLNÝ KÓD - jen ilustrace konceptu!

class MainCodingAgent:
    def handle_task(self, user_request):
        # 1. Analyzuj požadavek
        task_type = self.analyze_request(user_request)
        
        # 2. Zkontroluj dostupné custom agenty
        if task_type == "python_refactoring" and self.has_tool("python_expert"):
            # 3. Deleguj na custom agenta
            result = self.use_tool("python_expert", {
                "task": "refactor service to use ServiceServer pattern",
                "file": "services/identity/src/identity.py",
                "context": "DIGiDIG project uses ServiceServer base class"
            })
            
            # 4. Důvěřuj výsledku - ŽÁDNÝ review!
            if result.success:
                return result
            else:
                # Pouze při selhání zkus znovu nebo dělej sám
                return self.handle_manually(user_request)
        else:
            # Žádný vhodný agent - dělej sám
            return self.handle_manually(user_request)
```

---

## Časté Otázky / FAQ

### Q: Musím custom agenty konfigurovat?
**A:** Ne, custom agenty jsou konfigurovány na úrovni GitHub repository. Jsou automaticky dostupné hlavnímu agentovi.

### Q: Můžu vytvořit vlastní custom agenty?
**A:** Ano! Custom agenty se definují v `.github/agents/` adresáři (pokud máš odpovídající oprávnění).

### Q: Co když custom agent udělá chybu?
**A:** Hlavní agent by měl přijmout výsledek. Pokud custom agent hlásí selhání, můžeš mu předat úkol znovu s lepšími instrukcemi.

### Q: Může custom agent přistupovat k mým souborům?
**A:** Ano, custom agent má přístup k repository a může používat stejné nástroje jako hlavní agent (bash, edit, create, atd.)

### Q: Jak poznám, že delegace proběhla?
**A:** Hlavní agent to obvykle zmíní v odpovědi: "Delegating to [agent_name]..." nebo "Using specialized agent for..."

### Q: Je delegace rychlejší?
**A:** Ano, protože:
  - Custom agent je specializovaný → méně chyb
  - Nepotřebuje exploraci → zná best practices
  - Hlavní agent nemusí validovat → důvěřuje výsledku

---

## Best Practices pro DIGiDIG Projekt

### 1. Vždy Deleguj Python Změny
Pokud existuje python expert agent, používej ho pro:
- ✅ Refactoring servisů
- ✅ Implementace nových API endpointů
- ✅ Opravy bugů v Python kódu
- ✅ Aktualizace podle ServiceServer/ServiceClient patternu

### 2. Deleguj Složité Merge Konflikty
- ✅ Konflikty ve více souborech
- ✅ Konflikty v kritických částech (auth, databáze)
- ✅ Konflikty vyžadující hluboké porozumění kódu

### 3. Deleguj Dokumentační Úkoly
- ✅ Aktualizace README
- ✅ Vytváření API dokumentace
- ✅ Synchronizace dokumentace s kódem

### 4. NEDELEGUJ Malé Změny
- ❌ Oprava překlepu
- ❌ Jednoduchá změna konfigurace
- ❌ Přidání jednoho řádku kódu

---

## Kontrolní Seznam / Checklist

Před delegací úkolu zkontroluj:

- [ ] Existuje custom agent pro tuto oblast?
- [ ] Je úkol dostatečně složitý na delegaci?
- [ ] Mám všechny potřebné informace pro kontext?
- [ ] Je task jasně definovaný?

Po delegaci:

- [ ] Custom agent hlásí úspěch?
  - Ano → Přijmi výsledek BEZ review
  - Ne → Zkus znovu s lepšími instrukcemi

---

## Závěr / Conclusion

**Delegace je mocný nástroj pro efektivní práci s GitHub Copilot.**

Klíčové principy:
1. ✅ Deleguj na specialisty, když jsou k dispozici
2. ✅ Poskytni kompletní kontext
3. ✅ Důvěřuj výsledkům custom agentů
4. ✅ Pouze při selhání intervenuj
5. ✅ Používej delegaci pro složité úkoly

**Nezapomeň:** Custom agenti jsou tu, aby ti pomohli pracovat efektivněji. Využívej je!

---

## Reference

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [DIGiDIG Project Instructions](.github/instructions.md)
- [DIGiDIG Architecture](README.md)

---

*Dokument vytvořen: 2025-11-10*
*Verze: 1.0*
