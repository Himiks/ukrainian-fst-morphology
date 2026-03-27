# Ukrainian Morphology FST — Documentation

## Files

| File | Description |
|------|-------------|
| [`ukrainian_fst.ipynb`](./ukrainian_fst.ipynb) | Jupyter notebook with full FST implementation and tests |
| [`lexicon.txt`](./lexicon.txt) | Lexicon of base forms with categories and morphological tags |
| [`main.py`](./main.py) | Standalone Python module (same FST, runnable without Jupyter) |

---

## Grammar Description

This project implements a **Finite State Transducer (FST)** for a fragment of Ukrainian morphology.
Each rule is encoded as a set of arcs over states q0…qN:

```
q0 --[σ:σ]--> q0        self-loop: copy every stem character unchanged
q0 --[s1:t1]--> q1  ┐
q1 --[s2:t2]--> q2  │   suffix arcs: consume old suffix / emit new suffix
qN  :  FINAL STATE  ┘
```

- **σ** = any input character (identity / stem copy)
- **ε** on the input side = **insertion** (output character has no corresponding input)
- **ε** on the output side = **deletion** (input character is consumed but not emitted)

---

## Case 1 — Noun Genitive Singular (Родовий відмінок однини)

Feminine nouns of the 1st declension form the Genitive Singular by replacing their ending.

| Stem type | Rule    | Examples |
|-----------|---------|----------|
| Hard      | -а → -и | держава→держави, людина→людини, хвилина→хвилини, справа→справи, садиба→садиби, влада→влади |
| Soft      | -я → -і | криниця→криниці, лікарня→лікарні, пустеля→пустелі, знаряддя→знарядді, праця→праці, пекерня→пекерні |

**FST `noun_gen_hard` (`-а → -и`):**
```
q0 --[σ:σ]--> q0   (copy stem)
q0 --[а:и]--> q1   FINAL
```

**FST `noun_gen_soft` (`-я → -і`):**
```
q0 --[σ:σ]--> q0
q0 --[я:і]--> q1   FINAL
```

---

## Case 2 — Adjective Nominative Masculine → Feminine (Чоловічий → Жіночий рід)

Ukrainian adjectives agree in gender. The Feminine form is derived from the Masculine by suffix replacement.

| Stem type | Rule      | Examples |
|-----------|-----------|----------|
| Hard      | -ий → -а  | незалежний→незалежна, відважний→відважна, загадковий→загадкова, оксамитовий→оксамитова, бурштиновий→бурштинова, зухвалий→зухвала |
| Soft      | -ій → -я  | майбутній→майбутня, сусідній→сусідня, справжній→справжня, безкрайній→безкрайня, всесвітній→всесвітня, довколишній→довколишня |

**FST `adj_fem_hard` (`-ий → -а`):**
```
q0 --[σ:σ]--> q0
q0 --[и:а]--> q1
q1 --[й:ε]--> q2   FINAL
```
*(й is deleted — it has no counterpart in the feminine form)*

**FST `adj_fem_soft` (`-ій → -я`):**
```
q0 --[σ:σ]--> q0
q0 --[і:я]--> q1
q1 --[й:ε]--> q2   FINAL
```

---

## Case 3 — Verb Infinitive → 1sg Present (Інфінітив → 1 ос. одн. теп. часу)

| Verb class | Rule       | Examples |
|-----------|-----------|----------|
| -ати / -яти | -ти → -ю | відчувати→відчуваю, перемагати→перемагаю, зупиняти→зупиняю, кохати→кохаю, мріяти→мріяю, надихати→надихаю |
| -ити        | -ити → -ю | цінити→ціню, хвалити→хвалю, молити→молю |

**FST `verb_1sg_aty` (`-ти → -ю`):**
```
q0 --[σ:σ]--> q0
q0 --[т:ю]--> q1
q1 --[и:ε]--> q2   FINAL
```

**FST `verb_1sg_yty` (`-ити → -ю`):**
```
q0 --[σ:σ]--> q0
q0 --[и:ю]--> q1
q1 --[т:ε]--> q2
q2 --[и:ε]--> q3   FINAL
```

---

## Rule S — Substitution: г → з in Dative (Давальний відмінок)

Feminine nouns ending in **-га** undergo a consonant mutation **г → з** when the Dative suffix **-і** is attached (replacing **-а**).
This is a classic Ukrainian **palatalisation alternation**.

| Nominative | Dative   |
|-----------|---------|
| перемога   | перемозі |
| наснага    | насназі  |
| звага      | звазі    |
| розвага    | розвазі  |
| вимога     | вимозі   |
| знемога    | знемозі  |

**FST `noun_dat_subst` (`-га → -зі`):**
```
q0 --[σ:σ]--> q0
q0 --[г:з]--> q1   ← SUBSTITUTION arc: г maps to з
q1 --[а:і]--> q2   FINAL
```

---

## Rule I — Insertion: ε → ся (Reflexive verbs / Зворотні дієслова)

Reflexive verbs are formed by appending the particle **-ся** after the infinitive ending **-ти**.
In FST terms, **-ся** has no corresponding input characters — it is a pure **epsilon insertion**.

| Infinitive  | Reflexive    |
|------------|-------------|
| навчати     | навчатися    |
| намагати    | намагатися   |
| піклувати   | піклуватися  |

**FST `verb_reflexive` (`-ти → -тися`):**
```
q0 --[σ:σ]--> q0
q0 --[т:т]--> q1
q1 --[и:и]--> q2
q2 --[ε:с]--> q3   ← INSERTION arc: nothing maps to с
q3 --[ε:я]--> q4   FINAL  ← INSERTION arc: nothing maps to я
```

---

## Rule D — Deletion: -ти → ε (Verb Stem Extraction)

The verb stem is obtained by stripping the infinitive suffix **-ти**.
Both **т** and **и** map to **ε** — they are consumed from the input but produce no output.

| Infinitive   | Stem      |
|-------------|----------|
| відчувати    | відчува   |
| співати      | співа     |
| обіймати     | обійма    |
| надихати     | надиха    |
| допомагати   | допомага  |
| захищати     | захища    |

**FST `verb_stem` (`-ти → ε`):**
```
q0 --[σ:σ]--> q0
q0 --[т:ε]--> q1   ← DELETION arc: т is consumed, nothing emitted
q1 --[и:ε]--> q2   FINAL  ← DELETION arc: и is consumed, nothing emitted
```

---

## Complex Case — Consonant Alternation in 1sg Present (Exceptions)

Some Ukrainian **-ити** verbs undergo **consonant mutations** before the personal ending **-ю** in 1sg Present.
The regular FST `verb_1sg_yty` (-ити → -ю) produces **incorrect** forms for these verbs:

> `голосити` → regular rule gives `*голосю` — **wrong**
> `загубити` → regular rule gives `*загубю` — **wrong**

Two dedicated exception FSTs are needed:

### Pattern с → ш  (`-сити → -шу`)

| Infinitive  | 1sg Present |
|------------|-------------|
| голосити    | голошу      |
| виносити    | виношу      |
| заносити    | заношу      |

**FST `verb_alt_s_sh`:**
```
q0 --[σ:σ]--> q0
q0 --[с:ш]--> q1   ← consonant substitution с → ш
q1 --[и:у]--> q2
q2 --[т:ε]--> q3
q3 --[и:ε]--> q4   FINAL
```

### Pattern б → бл  (`-бити → -блю`)

An **epenthetic л** is inserted between б and the ending, a well-known Ukrainian morpho-phonological rule.

| Infinitive  | 1sg Present |
|------------|-------------|
| загубити    | загублю     |
| ослабити    | ослаблю     |
| зрубити     | зрублю      |
| доробити    | дороблю     |

**FST `verb_alt_b_bl`:**
```
q0 --[σ:σ]--> q0
q0 --[б:б]--> q1
q1 --[и:л]--> q2   ← и is consumed, л is emitted (epenthesis)
q2 --[т:ю]--> q3
q3 --[и:ε]--> q4   FINAL
```

---

## Test Results

All **55 test cases** pass (✓) across all 11 FST instances.

| Section | FSTs | Tests |
|---------|------|-------|
| Case 1 — Noun Genitive (hard) | noun_gen_hard | 6 |
| Case 1 — Noun Genitive (soft) | noun_gen_soft | 6 |
| Case 2 — Adjective Feminine (hard) | adj_fem_hard | 6 |
| Case 2 — Adjective Feminine (soft) | adj_fem_soft | 6 |
| Case 3 — Verb 1sg Present (-ати/-яти) | verb_1sg_aty | 6 |
| Case 3 — Verb 1sg Present (-ити) | verb_1sg_yty | 3 |
| Rule S — Substitution | noun_dat_subst | 6 |
| Rule I — Insertion | verb_reflexive | 3 |
| Rule D — Deletion | verb_stem | 6 |
| Complex — Alternation с→ш | verb_alt_s_sh | 3 |
| Complex — Alternation б→бл | verb_alt_b_bl | 4 |
| **Total** | **11 FSTs** | **55 tests** |
