# Delegation Quick Reference Card

## 🚀 Co je Delegace? / What is Delegation?

**Delegace = Předání úkolu specializovanému agentovi / Delegation = Passing task to specialized agent**

---

## ⚡ Kdy Delegovat? / When to Delegate?

| ✅ DELEGUJ / DELEGATE | ❌ NEDELEGUJ / DON'T DELEGATE |
|----------------------|-------------------------------|
| Složité Python změny / Complex Python changes | Jednoduché opravy / Simple fixes |
| Merge konflikty / Merge conflicts | Malé změny konfigurace / Small config changes |
| Aktualizace dokumentace / Documentation updates | Explorace kódu / Code exploration |
| Psaní testů / Writing tests | Cross-domain úkoly / Cross-domain tasks |
| Refactoring / Refactoring | - |

---

## 🔄 Workflow Delegace / Delegation Workflow

```
1. Uživatel zadá úkol / User gives task
        ↓
2. Hlavní agent zkontroluje custom agenty / Main agent checks custom agents
        ↓
3. Existuje vhodný agent? / Suitable agent exists?
   ├─ ANO → DELEGUJ / YES → DELEGATE
   │         ↓
   │   Custom agent pracuje / Custom agent works
   │         ↓
   │   Hlavní agent přijme výsledek BEZ review
   │   Main agent accepts result WITHOUT review
   │         ↓
   │   Pokračuj v další práci / Continue with next task
   │
   └─ NE → Hlavní agent dělá sám / NO → Main agent does it
```

---

## 🎯 Klíčová Pravidla / Key Rules

### 1️⃣ VŽDY NEJPRVE DELEGUJ / ALWAYS DELEGATE FIRST
```
if (custom_agent_exists && task_is_suitable):
    DELEGATE()  # ✅
else:
    do_it_yourself()
```

### 2️⃣ POSKYTNI KONTEXT / PROVIDE CONTEXT
- Custom agent nemá tvůj kontext / Custom agent doesn't have your context
- Předej všechny potřebné informace / Pass all necessary info
- Jasně formuluj úkol / Clearly define task

### 3️⃣ DŮVĚŘUJ VÝSLEDKU / TRUST THE RESULT
```python
result = delegate_to_custom_agent(task)

if result.success:
    # ✅ Přijmi výsledek / Accept result
    # ❌ NEDĚLEJ review / DON'T review
    # ❌ NEDĚLEJ validaci / DON'T validate
    # ❌ NEDĚLEJ testy / DON'T test
    return result
else:
    # Pouze při selhání / Only on failure
    retry_with_better_instructions()
```

### 4️⃣ POUZE PŘI SELHÁNÍ INTERVENUJ / INTERVENE ONLY ON FAILURE
- Custom agent hlásí úspěch → Pokračuj / Agent reports success → Continue
- Custom agent hlásí problém → Zkus znovu / Agent reports problem → Retry

---

## 📋 Příklady Custom Agentů / Custom Agent Examples

| Agent | Použití / Use Case | Příklad / Example |
|-------|-------------------|-------------------|
| 🐍 `python_expert` | Python kód, FastAPI | Refactoring servisů / Service refactoring |
| 🔀 `merge_conflict_resolver` | Git merge konflikty | Složité konflikty / Complex conflicts |
| 📝 `documentation_expert` | Markdown, API docs | Aktualizace README / README updates |
| 🐳 `docker_expert` | Docker, compose | Optimalizace Dockerfile / Dockerfile optimization |
| ✅ `testing_expert` | Unit/integration testy | Psaní testů / Writing tests |

---

## 💡 Praktický Příklad / Practical Example

### Scénář: Refactoring Python Servisu

**Uživatel:** "Refactoruj identity service podle ServiceServer patternu"

**❌ Špatně (bez delegace):**
```
Hlavní agent:
1. Načte identity.py
2. Ručně upraví kód
3. Spustí testy
4. Opraví chyby
5. Znovu testuje
→ Dlouhé, riziko chyb
```

**✅ Správně (s delegací):**
```
Hlavní agent:
1. Zkontroluje python_expert agenta
2. Deleguje: "Refactor identity.py to ServiceServer"
3. Custom agent provede refactoring + testy
4. Hlavní agent přijme výsledek
5. Pokračuje na další úkol
→ Rychlé, kvalitní
```

---

## 🔍 Jak Poznat Custom Agenta? / How to Recognize Custom Agent?

V seznamu nástrojů (tools) hledej popis začínající:
In tool list, look for description starting with:

```
"Custom agent: [description]"
```

**Příklad / Example:**
```
Tool: python_code_editor
Description: "Custom agent: Expert in Python code with refactoring tools"
              ↑ Tohle značí custom agenta / This marks custom agent
```

---

## ⚠️ NEJČASTĚJŠÍ CHYBY / COMMON MISTAKES

### ❌ Chyba 1: Review po delegaci
```python
# ❌ ŠPATNĚ / WRONG
result = delegate_to_python_expert(task)
view_file(result.changed_file)  # DON'T!
validate_changes()               # DON'T!
```

```python
# ✅ SPRÁVNĚ / CORRECT
result = delegate_to_python_expert(task)
if result.success:
    continue_to_next_task()  # Trust and continue!
```

### ❌ Chyba 2: Nedelegování, když agent existuje
```python
# ❌ ŠPATNĚ / WRONG
if task == "python_refactoring":
    manually_refactor_code()  # DON'T! Delegate first!
```

```python
# ✅ SPRÁVNĚ / CORRECT
if task == "python_refactoring" and python_expert_exists():
    delegate_to_python_expert()  # Do this first!
```

### ❌ Chyba 3: Nedostatek kontextu
```python
# ❌ ŠPATNĚ / WRONG
delegate("Fix the service")  # Too vague!
```

```python
# ✅ SPRÁVNĚ / CORRECT
delegate({
    "task": "Refactor identity.py",
    "pattern": "ServiceServer base class",
    "context": "DIGiDIG uses class-based service architecture",
    "file": "services/identity/src/identity.py"
})
```

---

## 📊 Kdy Delegace Selhává / When Delegation Fails

| Důvod / Reason | Řešení / Solution |
|----------------|-------------------|
| Nejasný úkol / Unclear task | Přeformuluj s více detaily / Reformulate with more details |
| Chybí kontext / Missing context | Přidej všechny potřebné info / Add all necessary info |
| Nesprávný agent / Wrong agent | Zkus jiného agenta nebo dělej sám / Try different agent or do it yourself |
| Technický problém / Technical issue | Zkus znovu nebo escaluj / Retry or escalate |

---

## ✅ Kontrolní Seznam / Checklist

### Před Delegací / Before Delegation:
- [ ] Existuje custom agent pro tuto oblast? / Custom agent exists for this area?
- [ ] Je úkol dostatečně složitý? / Is task complex enough?
- [ ] Mám všechny informace pro kontext? / Do I have all context info?
- [ ] Je úkol jasně definovaný? / Is task clearly defined?

### Po Delegaci / After Delegation:
- [ ] Custom agent hlásí úspěch? / Custom agent reports success?
  - **ANO / YES** → Přijmi výsledek BEZ změn / Accept result WITHOUT changes
  - **NE / NO** → Zkus znovu s lepšími instrukcemi / Retry with better instructions

---

## 🎓 Zapamatuj Si / Remember

1. **Deleguj VŽDY, když můžeš** / **Delegate ALWAYS when you can**
2. **Důvěřuj expertům** / **Trust the experts**
3. **Poskytni kontext** / **Provide context**
4. **Neprovádíš review** / **Don't review**
5. **Efektivita > Kontrola** / **Efficiency > Control**

---

## 📚 Další Zdroje / More Resources

- 📖 [Kompletní Delegation Guide](DELEGATION-GUIDE.md) - Podrobný průvodce
- 📖 [DIGiDIG Instructions](.github/instructions.md) - Projekt instrukce
- 📖 [GitHub Copilot Docs](https://docs.github.com/en/copilot) - Oficiální dokumentace

---

*Quick Reference vytvořena: 2025-11-10*
*Verze: 1.0*
