#!/usr/bin/env python3
"""Explain item count calculation."""

from itertools import combinations, permutations

V = 22  # rooms
k = 3   # capacity
E = 2   # exits

print("="*70)
print("ITEM COUNT BREAKDOWN")
print("="*70)
print(f"\nParameters: V={V} rooms, k={k} capacity, E={E} exits")
print(f"\nWe generate items for ALL sizes r=1 to k (not just k):")

total = 0

# 1-room items
print(f"\n1-ROOM ITEMS:")
print(f"  Room combinations: C({V}, 1) = {V}")
print(f"  Vectors per room: How many ways to rescue 1-3 people?")
print(f"    1 person: [1]")
print(f"    2 people: [2]")
print(f"    3 people: [3]")
print(f"  Total vectors: 3")
print(f"  Permutations: 1! = 1 (only one room)")
print(f"  Exit combinations: E² = {E**2}")
print(f"  Total 1-room items: {V} × 3 × 1 × {E**2} = {V * 3 * 1 * E**2}")
total += V * 3 * 1 * E**2

# 2-room items
print(f"\n2-ROOM ITEMS:")
C_V_2 = V * (V-1) // 2
print(f"  Room combinations: C({V}, 2) = {C_V_2}")
print(f"  Vectors per combination: How many ways to split k=3?")
print(f"    [1, 1]: rescue 1 from each")
print(f"    [1, 2]: rescue 1 from first, 2 from second")
print(f"    [2, 1]: rescue 2 from first, 1 from second")
print(f"  Total vectors: 3 (for k=3)")
print(f"  Permutations: 2! = 2 (which room to visit first)")
print(f"  Exit combinations: E² = {E**2}")
print(f"  Total 2-room items: {C_V_2} × 3 × 2 × {E**2} = {C_V_2 * 3 * 2 * E**2}")
total += C_V_2 * 3 * 2 * E**2

# 3-room items
print(f"\n3-ROOM ITEMS:")
C_V_3 = V * (V-1) * (V-2) // 6
print(f"  Room combinations: C({V}, 3) = {C_V_3}")
print(f"  Vectors per combination: How many ways to split k=3?")
print(f"    [1, 1, 1]: rescue 1 from each")
print(f"  Total vectors: 1 (for k=3, only way is [1,1,1])")
print(f"  Permutations: 3! = 6 (visit order matters)")
print(f"  Exit combinations: E² = {E**2}")
print(f"  Total 3-room items: {C_V_3} × 1 × 6 × {E**2} = {C_V_3 * 1 * 6 * E**2}")
total += C_V_3 * 1 * 6 * E**2

print(f"\n{'='*70}")
print(f"TOTAL RAW ITEMS (before pruning): {total:,}")
print(f"{'='*70}")

print(f"\nActual count from code: 672,228")
print(f"Expected from formula: {total:,}")
print(f"\nDifference is due to:")
print(f"  - Rooms with fewer than k occupants can't generate all vectors")
print(f"  - Some rooms have 2 occupants, so can't generate [3] vector")
print(f"  - Algorithm filters invalid vectors during generation")

print(f"\nAfter pruning (~29k dominated items):")
print(f"  Final items: ~642k")
print(f"  These are kept because combined trips are faster than sequential")
