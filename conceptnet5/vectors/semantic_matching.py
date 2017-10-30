import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import random

random.seed(0)
from conceptnet5.relations import (
    COMMON_RELATIONS, ALL_RELATIONS, SYMMETRIC_RELATIONS, ENTAILED_RELATIONS,
    OPPOSITE_RELATIONS
)
from conceptnet5.util import get_data_filename
from conceptnet5.vectors.formats import load_hdf

RELATION_INDEX = pd.Index(COMMON_RELATIONS)
N_RELS = len(RELATION_INDEX)
RELATION_DIM = 5
BATCH_SIZE = 10


def coin_flip():
    return random.choice([False, True])


def _make_rel_chart():
    entailed_map = {}
    unrelated_map = {}
    for rel in ALL_RELATIONS:
        entailed = [rel]
        entailed_rel = rel
        while entailed_rel in ENTAILED_RELATIONS:
            entailed_rel = ENTAILED_RELATIONS[entailed_rel]
            entailed.append(entailed_rel)
        entailed_map[rel] = [
            i for (i, rel) in enumerate(COMMON_RELATIONS)
            if rel in entailed
        ]
        unrelated_map[rel] = [
            i for (i, rel) in enumerate(COMMON_RELATIONS)
            if rel not in entailed
        ]
    return entailed_map, unrelated_map

ENTAILED_RELATIONS, UNRELATED_RELATIONS = _make_rel_chart()
print(ENTAILED_RELATIONS)
print(UNRELATED_RELATIONS)

def iter_edges_forever(filename):
    while True:
        for line in open(filename, encoding='utf-8'):
            concept1, concept2, weight_str, _dataset, relation = line.strip().split('\t')
            weight = float(weight_str)
            if weight >= 1.:
                yield (relation, concept1, concept2, weight)


def ltvar(numbers):
    return autograd.Variable(torch.LongTensor(numbers))


class SemanticMatchingModel(nn.Module):
    def __init__(self, frame):
        super().__init__()
        self.n_terms, self.term_dim = frame.shape
        self.index = frame.index
        self.term_vecs = nn.Embedding(frame.shape[0], self.term_dim)
        self.term_vecs.weight.data.copy_(
            torch.from_numpy(frame.values)
        )
        self.rel_vecs = nn.Embedding(N_RELS, RELATION_DIM)
        assoc_t = torch.Tensor(RELATION_DIM, self.term_dim, self.term_dim)
        nn.init.normal(assoc_t, std=.000001)
        self.assoc_tensor = autograd.Variable(assoc_t)
        assoc_o = torch.Tensor(RELATION_DIM)
        nn.init.normal(assoc_o, std=.000001)
        self.assoc_offset = autograd.Variable(assoc_o)

    def forward(self, rels, terms_L, terms_R):
        # Get relation vectors for the whole batch, with shape (b * i)
        rels_b_i = self.rel_vecs(rels)
        # Get left term vectors for the whole batch, with shape (b * j)
        terms_b_j = self.term_vecs(terms_L)
        # Get right term vectors for the whole batch, with shape (b * k)
        terms_b_k = self.term_vecs(terms_R)
        # Reshape our (i * j * k) assoc_tensor into (ij * k), then (k * ij)
        assoc_ij_k = self.assoc_tensor.view(-1, self.term_dim)
        assoc_k_ij = assoc_ij_k.transpose(0, 1)

        # An intermediate product of shape (b * i * j)
        inter_b_ij = torch.mm(terms_b_k, assoc_k_ij)
        inter_b_i_j = inter_b_ij.view(-1, RELATION_DIM, self.term_dim)

        # Next we want to batch-multiply this (b * i * j) term by a term of
        # shape (b * j * 1), giving a (b * i * 1) result.
        terms_b_j_1 = terms_b_j.view(-1, self.term_dim, 1)
        inter_b_i_1 = torch.bmm(inter_b_i_j, terms_b_j_1)

        # Reshape the result to (b * i).
        inter_b_i = inter_b_i_1.view(-1, RELATION_DIM)

        # Multiply our (b * i) term elementwise by rels_b_i. This indicates
        # how well the interaction between term j and term k matches each
        # component of the relation vector.
        relmatch = inter_b_i * rels_b_i

        # Add the offset vector for relations -- this should help us learn
        # that some relations are rare or special-purpose.
        shifted_b_i = relmatch + self.assoc_offset

        # Add up the components for each batch
        energy_b = torch.sum(shifted_b_i, 1)
        return energy_b

    def positive_negative_batch(self, edge_iterator):
        pos_rels = []
        pos_left = []
        pos_right = []

        neg_rels = []
        neg_left = []
        neg_right = []

        weights = []

        for rel, left, right, weight in edge_iterator:
            try:
                if not ENTAILED_RELATIONS[rel]:
                    continue

                # Possibly replace a relation with a more general relation
                if coin_flip():
                    rel = random.choice(ENTAILED_RELATIONS[rel])

                # Possibly swap the sides of a symmetric relation
                if rel in SYMMETRIC_RELATIONS and coin_flip():
                    left, right = right, left

                rel_idx = RELATION_INDEX.get_loc(rel)
                left_idx = self.index.get_loc(left)
                right_idx = self.index.get_loc(right)

                corrupt_rel_idx = rel_idx
                corrupt_left_idx = left_idx
                corrupt_right_idx = right_idx

                corrupt_which = random.randrange(3)
                if corrupt_which == 0:
                    rel = random.choice(UNRELATED_RELATIONS)
                    corrupt_rel_idx = RELATION_INDEX.get_loc(rel)
                elif corrupt_which == 1:
                    while corrupt_left_idx == left_idx:
                        corrupt_left_idx = random.randrange(self.n_terms)
                elif corrupt_which == 2:
                    while corrupt_right_idx == right_idx:
                        corrupt_right_idx = random.randrange(self.n_terms)

                pos_rels.append(rel_idx)
                pos_left.append(left_idx)
                pos_right.append(right_idx)

                neg_rels.append(corrupt_rel_idx)
                neg_left.append(corrupt_left_idx)
                neg_right.append(corrupt_right_idx)

                weights.append(weight)
            except KeyError:
                pass

            if len(weights) == BATCH_SIZE:
                break

        pos_data = (ltvar(pos_rels), ltvar(pos_left), ltvar(pos_right))
        neg_data = (ltvar(neg_rels), ltvar(neg_left), ltvar(neg_right))
        weights = autograd.Variable(torch.Tensor(weights))
        return pos_data, neg_data, weights


    def make_batches(self, edge_iterator):
        while True:
            yield self.positive_negative_batch(edge_iterator)


def run():
    frame = load_hdf(get_data_filename('vectors-20170630/mini.h5'))
    model = SemanticMatchingModel(frame.astype(np.float32))
    loss_function = nn.MarginRankingLoss(margin=1)
    optimizer = optim.SGD(model.parameters(), lr=0.1)
    losses = []
    preference_labels = autograd.Variable(torch.Tensor([1] * BATCH_SIZE))
    steps = 0
    for pos_batch, neg_batch, weights in model.make_batches(
        iter_edges_forever(get_data_filename('assoc/reduced.csv'))
    ):
        model.zero_grad()
        pos_energy = model(*pos_batch)
        neg_energy = model(*neg_batch)
        loss = loss_function(pos_energy, neg_energy, preference_labels)
        loss.backward()
        optimizer.step()

        losses.append(loss.data[0])
        if len(losses) >= 200:
            losses = losses[-100:]
        steps += 1
        if steps in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000) or steps % 10000 == 0:
            avg_loss = np.mean(losses)
            print("%d steps, loss=%4.4f" % (steps, avg_loss))
    print()


run()
