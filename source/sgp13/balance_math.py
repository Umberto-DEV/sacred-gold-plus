"""Exact, conditional probability models for inspecting balance proposals.

Damage and effective accuracy must come from the target game, including abilities
and type rules. These functions do not implement Pokémon battle mechanics. They
compose independent, identical attack kernels, without enemy actions, switching,
status, PP, recoil or passive healing. A result is not a full-battle win rate or
a proof that consecutive outputs of the native PRNG are independent.
"""
from collections import defaultdict
from fractions import Fraction


def _integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f'{name} must be a nonnegative integer')
    return value


def _probability(value):
    if type(value) not in (int, Fraction) or not 0 <= value <= 1:
        raise ValueError('probabilities must be exact integers or Fractions in [0, 1]')
    return Fraction(value)


def attack_distribution(normal_rolls, critical_rolls, hit_chance, crit_chance):
    """Mix hit/critical branches; retain repeated equally likely damage rolls.

    ``crit_chance`` is conditional on a successful hit. A metadata accuracy of
    zero often represents an accuracy-check bypass: the caller must evaluate
    the native hit chance rather than treating that byte as a probability.
    """
    hit, critical = _probability(hit_chance), _probability(crit_chance)
    normal, crit = tuple(normal_rolls), tuple(critical_rolls)
    if not normal or not crit:
        raise ValueError('each damage branch needs at least one roll')
    for roll in normal + crit:
        _integer(roll, 'damage')
    result = defaultdict(Fraction)
    result[0] = 1 - hit
    for rolls, weight in ((normal, hit * (1 - critical)), (crit, hit * critical)):
        for damage in rolls:
            result[damage] += weight / len(rolls)
    return {damage: probability for damage, probability in sorted(result.items())
            if probability}


def ko_probability(distribution, hp, attempts, *, berry_heal=0, berry_threshold=None):
    """Probability of KO within ``attempts`` independent attacks.

    An optional berry heals once after a nonlethal damaging hit leaves HP at or
    below the threshold (default half initial HP). Healing is capped at initial
    HP. The target starts at full HP; no other turn effects are implied.
    """
    hp = _integer(hp, 'HP')
    attempts = _integer(attempts, 'attempts')
    berry_heal = _integer(berry_heal, 'berry healing')
    threshold = hp // 2 if berry_threshold is None else _integer(berry_threshold, 'threshold')
    if threshold > hp:
        raise ValueError('berry threshold exceeds initial HP')
    outcomes = {}
    for damage, probability in distribution.items():
        outcomes[_integer(damage, 'damage')] = _probability(probability)
    if not outcomes or sum(outcomes.values()) != 1:
        raise ValueError('damage probabilities must sum exactly to one')
    states = {(hp, bool(berry_heal)): Fraction(1)}
    for _ in range(attempts):
        next_states = defaultdict(Fraction)
        for (remaining, ready), weight in states.items():
            if remaining == 0:
                next_states[(0, False)] += weight
                continue
            for damage, probability in outcomes.items():
                if not probability:
                    continue
                after = max(0, remaining - damage)
                available = ready and after > 0
                if damage > 0 and available and after <= threshold:
                    after = min(hp, after + berry_heal)
                    available = False
                next_states[(after, available)] += weight * probability
        states = next_states
    return sum((weight for (remaining, _), weight in states.items() if remaining == 0),
               Fraction(0))


def encounter_cdf(probabilities):
    """At least one success for independent, possibly different encounter odds.

    The caller defines what counts as an eligible encounter and how chain state
    evolves. This function does not assume that a failed shiny roll advances a
    chain, nor that a chain survives encounters, escapes or a reset.
    """
    no_success = Fraction(1)
    for probability in probabilities:
        no_success *= 1 - _probability(probability)
    return 1 - no_success
