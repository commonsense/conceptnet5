from assoc_space import AssocSpace
import argparse
import os
import numpy as np


def merge_8_vector_spaces(subspace_dir):
    # For now, we'll hardcode a balanced way to merge 8 vector spaces.
    # Supporting an arbitrary number of spaces would be trickier.
    mergers = [
        ('part_00', 'part_01', 'merged_a0'),
        ('part_02', 'part_03', 'merged_a1'),
        ('part_04', 'part_05', 'merged_a2'),
        ('part_06', 'part_07', 'merged_a3'),
        ('merged_a0', 'merged_a1', 'merged_b0'),
        ('merged_a2', 'merged_a3', 'merged_b1'),
        ('merged_b0', 'merged_b1', 'merged_complete')
    ]
    merge_vector_spaces(subspace_dir, mergers)


def merge_vector_spaces(subspace_dir, mergers):
    merged = None
    for sourceA, sourceB, target in mergers:
        print('Merging: %s + %s -> %s' % (sourceA, sourceB, target))
        spaceA = AssocSpace.load_dir(os.path.join(subspace_dir, sourceA))
        spaceB = AssocSpace.load_dir(os.path.join(subspace_dir, sourceB))

        # On the first step, we want to keep all the axes from merging subparts.
        # Through most of the merging, we want to maintain that number of axes.
        # At the end, we want to go back to the original number of axes.

        # For example, when we are merging 300-dimensional spaces, the
        # intermediate merge results will have 600 dimensions, and the final
        # result will have 300 dimensions again.

        # We don't refer to the number of axes in spaceB in this code, because
        # we're assuming all the sub-parts have equal numbers of axes.

        if sourceA.startswith('part'):
            k = spaceA.k * 2
        elif target == 'merged_complete':
            k = spaceA.k // 2
        else:
            k = spaceA.k

        merged = spaceA.merged_with(spaceB, k=k)
        del spaceA
        del spaceB
        merged.save_dir(os.path.join(subspace_dir, target))
    
    magnitudes = (merged.u ** 2).sum(1)
    good_indices = np.flatnonzero(magnitudes >= 1e-5)
    filtered = merged[good_indices]
    filtered.save_dir(os.path.join(subspace_dir, 'merged_filtered'))
    return filtered


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')

    args = parser.parse_args()
    merge_8_vector_spaces(args.input_dir)
