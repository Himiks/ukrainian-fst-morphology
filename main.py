"""
Ukrainian Morphology FST
========================
Finite State Transducer for Ukrainian language morphological rules.

Implemented:
  Case 1  – Noun Genitive Singular  (держава→держави, вишня→вишні)
  Case 2  – Adjective Feminine form (незалежний→незалежна, майбутній→майбутня)
  Case 3  – Verb 1sg Present tense  (відчувати→відчуваю, хвалити→хвалю)
  Rule S  – Substitution  : г→з in Dative (перемога→перемозі)
  Rule I  – Insertion     : add reflexive -ся  (навчати→навчатися)
  Rule D  – Deletion      : strip infinitive -ти → verb stem
  Complex – Consonant alternation in 1sg (голосити→голошу, загубити→загублю)
"""

# ──────────────────────────────────────────────────────────────
# Core FST data structures
# ──────────────────────────────────────────────────────────────

class Arc:
    """One arc in an FST: (from_state) --[input:output]--> (to_state)."""
    def __init__(self, from_state, to_state, inp, out):
        self.from_state = from_state
        self.to_state   = to_state
        self.inp        = inp
        self.out        = out

    def __repr__(self):
        return f"  ({self.from_state}) --[{self.inp}:{self.out}]--> ({self.to_state})"


class MorphFST:
    """
    Finite State Transducer for a single morphological rule.

    Encoding pattern (suffix rewrite):
    ─────────────────────────────────
      q0 ──[σ:σ]──> q0          self-loop: copy every stem character
      q0 ──[s1:t1]──> q1  ┐
      q1 ──[s2:t2]──> q2  │  consume old suffix / emit new suffix
      ...                  │
      qN : final state     ┘
    """

    def __init__(self, name, rule_type, description):
        self.name        = name
        self.rule_type   = rule_type
        self.description = description
        self.arcs        = []
        self.states      = {'q0'}
        self.initial     = 'q0'
        self.finals      = set()
        self._suffix_in  = None
        self._suffix_out = None
        self._condition  = None

    def encode(self, suffix_in, suffix_out, condition=None):
        """Register the suffix rewrite suffix_in → suffix_out and populate arcs."""
        self._suffix_in  = suffix_in
        self._suffix_out = suffix_out
        self._condition  = condition

        # Self-loop: copy stem characters (any symbol σ)
        self.arcs.append(Arc('q0', 'q0', 'σ', 'σ'))

        n_in  = len(suffix_in)
        n_out = len(suffix_out)
        span  = max(n_in, n_out, 1)

        prev = 'q0'
        for i in range(span):
            nxt     = f'q{i+1}'
            in_sym  = suffix_in[i]  if i < n_in  else 'ε'
            out_sym = suffix_out[i] if i < n_out else 'ε'
            self.arcs.append(Arc(prev, nxt, in_sym, out_sym))
            self.states.add(nxt)
            prev = nxt

        self.finals.add(prev)
        return self

    def apply(self, word):
        """Transduce word through this FST; return result or None."""
        if self._suffix_in is None:
            return None
        if self._condition and not self._condition(word):
            return None
        if self._suffix_in == '':                          # pure insertion
            return word + self._suffix_out
        if word.endswith(self._suffix_in):
            stem = word[: -len(self._suffix_in)]
            return stem + self._suffix_out
        return None

    def show(self):
        print(f"\n{'═'*62}")
        print(f"  FST : {self.name}")
        print(f"  Type: {self.rule_type}")
        print(f"  Rule: {self.description}")
        print(f"  States : {sorted(self.states)}")
        print(f"  Initial: {self.initial}   Finals: {self.finals}")
        print("  Arcs:")
        for arc in self.arcs:
            print(f"    {arc}")
        print(f"{'═'*62}")


def test(fst, word, expected):
    result = fst.apply(word)
    ok = "✓" if result == expected else "✗"
    print(f"    {ok}  {word:20s} →  {str(result):20s}  (expected: {expected})")


# ══════════════════════════════════════════════════════════════
# CASE 1 – Noun Genitive Singular  (Родовий відмінок однини)
# ══════════════════════════════════════════════════════════════
# hard stem (-а → -и): книга→книги, школа→школи, вода→води
# soft stem (-я → -і): земля→землі, зоря→зорі,   пісня→пісні

noun_gen_hard = MorphFST("noun_gen_hard", "inflection",
                          "Noun Genitive Sg – hard stem: -а → -и").encode('а', 'и')

noun_gen_soft = MorphFST("noun_gen_soft", "inflection",
                          "Noun Genitive Sg – soft stem: -я → -і").encode('я', 'і')

# ══════════════════════════════════════════════════════════════
# CASE 2 – Adjective Nominative Masculine → Feminine
# ══════════════════════════════════════════════════════════════
# hard stem (-ий → -а): новий→нова, старий→стара, добрий→добра
# soft stem (-ій → -я): синій→синя, осінній→осіння, безкрайній→безкрайня

adj_fem_hard = MorphFST("adj_fem_hard", "inflection",
                         "Adjective Feminine – hard stem: -ий → -а").encode('ий', 'а')

adj_fem_soft = MorphFST("adj_fem_soft", "inflection",
                         "Adjective Feminine – soft stem: -ій → -я").encode('ій', 'я')

# ══════════════════════════════════════════════════════════════
# CASE 3 – Verb Infinitive → 1sg Present
# ══════════════════════════════════════════════════════════════
# -ати/-яти verbs (-ти → -ю): читати→читаю, співати→співаю, мріяти→мріяю
# -ити verbs      (-ити → -ю): говорити→говорю, дарити→дарю, варити→варю

verb_1sg_aty = MorphFST("verb_1sg_aty", "inflection",
                         "Verb 1sg Present – -ати/-яти: -ти → -ю").encode('ти', 'ю')

verb_1sg_yty = MorphFST("verb_1sg_yty", "inflection",
                         "Verb 1sg Present – -ити: -ити → -ю").encode('ити', 'ю')

# ══════════════════════════════════════════════════════════════
# RULE S – Substitution: г → з in Dative (Давальний відмінок)
# ══════════════════════════════════════════════════════════════
# нога→нозі,  дорога→дорозі,  книга→книзі
# Arcs: q0--[σ:σ]-->q0, q0--[г:з]-->q1, q1--[а:і]-->q2(final)

noun_dat_subst = MorphFST("noun_dat_subst", "substitution",
                           "Substitution г→з in Dative: -га → -зі").encode('га', 'зі')

# ══════════════════════════════════════════════════════════════
# RULE I – Insertion: ε → ся  (reflexive verbs)
# ══════════════════════════════════════════════════════════════
# вчити→вчитися,  мити→митися,  купати→купатися
# Arcs: q0--[σ:σ]-->q0 … then ε:с, ε:я appended after input ends

verb_reflexive = MorphFST("verb_reflexive", "insertion",
                           "Insertion ε→ся: infinitive → reflexive (-ти → -тися)").encode('ти', 'тися')

# ══════════════════════════════════════════════════════════════
# RULE D – Deletion: -ти → ε  (extract verb stem)
# ══════════════════════════════════════════════════════════════
# читати→чита,  говорити→говори,  співати→співа
# Arcs: q0--[σ:σ]-->q0, q0--[т:ε]-->q1, q1--[и:ε]-->q2(final)

verb_stem = MorphFST("verb_stem", "deletion",
                     "Deletion -ти→ε: strip infinitive suffix to get stem").encode('ти', '')

# ══════════════════════════════════════════════════════════════
# COMPLEX – Consonant Alternation in 1sg Present (Exceptions)
# ══════════════════════════════════════════════════════════════
# Regular -ити→-ю FAILS for these verbs; special FSTs needed:
#
#   с → ш  : носити→ношу,  просити→прошу,  косити→кошу
#   б → бл : любити→люблю, робити→роблю,   голубити→голублю
#
# с→ш FST:  -сити → -шу
#   q0--[σ:σ]-->q0, q0--[с:ш]-->q1, q1--[и:у]-->q2,
#   q2--[т:ε]-->q3, q3--[и:ε]-->q4(final)

verb_alt_s_sh = MorphFST("verb_alt_s_sh", "inflection",
                          "Complex – consonant alternation с→ш: -сити → -шу").encode('сити', 'шу')

# б→бл FST:  -бити → -блю
#   q0--[σ:σ]-->q0, q0--[б:б]-->q1, q1--[и:л]-->q2,
#   q2--[т:ю]-->q3, q3--[и:ε]-->q4(final)

verb_alt_b_bl = MorphFST("verb_alt_b_bl", "inflection",
                          "Complex – consonant alternation б→бл: -бити → -блю").encode('бити', 'блю')


# ──────────────────────────────────────────────────────────────
# Demo / self-test
# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':

    print("\n" + "═"*62)
    print("  UKRAINIAN MORPHOLOGY FST — Demo")
    print("═"*62)

    for fst in [noun_gen_hard, noun_gen_soft,
                adj_fem_hard, adj_fem_soft,
                verb_1sg_aty, verb_1sg_yty,
                noun_dat_subst, verb_reflexive, verb_stem,
                verb_alt_s_sh, verb_alt_b_bl]:
        fst.show()

    print("\n── CASE 1: Noun Genitive Singular ──────────────────────")
    print("  Hard stem (-а → -и):")
    test(noun_gen_hard, 'держава',   'держави')
    test(noun_gen_hard, 'людина',    'людини')
    test(noun_gen_hard, 'хвилина',   'хвилини')
    test(noun_gen_hard, 'справа', 'справи')
    test(noun_gen_hard, 'садиба', 'садиби')
    test(noun_gen_hard, 'влада', 'влади')

    print("  Soft stem (-я → -і):")
    test(noun_gen_soft, 'криниця',     'криниці')
    test(noun_gen_soft, 'лікарня',     'лікарні')
    test(noun_gen_soft, 'пустеля',   'пустелі')
    test(noun_gen_soft, 'знаряддя', 'знарядді')
    test(noun_gen_soft, 'праця', 'праці')
    test(noun_gen_soft, 'пекерня', 'пекерні')


    print("\n── CASE 2: Adjective Masculine → Feminine ──────────────")
    print("  Hard stem (-ий → -а):")
    test(adj_fem_hard, 'незалежний',  'незалежна')
    test(adj_fem_hard, 'відважний',   'відважна')
    test(adj_fem_hard, 'загадковий',  'загадкова')
    test(adj_fem_hard, 'оксамитовий',  'оксамитова')
    test(adj_fem_hard, 'бурштиновий',  'бурштинова')
    test(adj_fem_hard, 'зухвалий',  'зухвала')

    print("  Soft stem (-ій → -я):")
    test(adj_fem_soft, 'майбутній',   'майбутня')
    test(adj_fem_soft, 'сусідній',    'сусідня')
    test(adj_fem_soft, 'справжній',   'справжня')
    test(adj_fem_soft, 'безкрайній',   'безкрайня')
    test(adj_fem_soft, 'всесвітній',   'всесвітня')
    test(adj_fem_soft, 'довколишній',   'довколишня')


    print("\n── CASE 3: Verb Infinitive → 1sg Present ───────────────")
    print("  -ати/-яти verbs (-ти → -ю):")
    test(verb_1sg_aty, 'відчувати',   'відчуваю')
    test(verb_1sg_aty, 'перемагати',  'перемагаю')
    test(verb_1sg_aty, 'зупиняти',    'зупиняю')
    test(verb_1sg_aty, 'кохати',    'кохаю')
    test(verb_1sg_aty, 'мріяти',    'мріяю')
    test(verb_1sg_aty, 'надихати',    'надихаю')

    print("  -ити verbs (-ити → -ю):")
    test(verb_1sg_yty, 'цінити',      'ціню')
    test(verb_1sg_yty, 'хвалити',      'хвалю')
    test(verb_1sg_yty, 'молити',      'молю')



    print("\n── RULE S: Substitution г→з (Dative -га → -зі) ─────────")
    test(noun_dat_subst, 'перемога',  'перемозі')
    test(noun_dat_subst, 'наснага',   'насназі')
    test(noun_dat_subst, 'звага',   'звазі')
    test(noun_dat_subst, 'розвага',   'розвазі')
    test(noun_dat_subst, 'вимога',   'вимозі')
    test(noun_dat_subst, 'знемога',   'знемозі')


    print("\n── RULE I: Insertion ε→ся (reflexive -ти → -тися) ──────")
    test(verb_reflexive, 'навчати',   'навчатися')
    test(verb_reflexive, 'намагати',  'намагатися')
    test(verb_reflexive, 'піклувати', 'піклуватися')

    print("\n── RULE D: Deletion -ти→ε (verb stem) ───────────────────")
    test(verb_stem, 'відчувати',   'відчува')
    test(verb_stem, 'співати',  'співа')
    test(verb_stem, 'обіймати',    'обійма')
    test(verb_stem, 'надихати',    'надиха')
    test(verb_stem, 'допомагати',    'допомага')
    test(verb_stem, 'захищати',    'захища')

    print("\n── COMPLEX: Consonant alternation (1sg Present) ─────────")
    print("  с→ш (-сити → -шу):")
    test(verb_alt_s_sh, 'голосити',   'голошу')
    test(verb_alt_s_sh, 'виносити',   'виношу')
    test(verb_alt_s_sh, 'заносити',   'заношу')
    print("  б→бл (-бити → -блю):")
    test(verb_alt_b_bl, 'загубити',   'загублю')
    test(verb_alt_b_bl, 'ослабити',   'ослаблю')
    test(verb_alt_b_bl, 'зрубити',    'зрублю')
    test(verb_alt_b_bl, 'доробити',    'дороблю')


    print("\n" + "═"*62)
    print("  All tests complete.")
    print("═"*62 + "\n")

