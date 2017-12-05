import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import random
import os

from conceptnet5.relations import (
    COMMON_RELATIONS, ALL_RELATIONS, SYMMETRIC_RELATIONS, ENTAILED_RELATIONS,
)
from conceptnet5.uri import uri_prefix, assertion_uri
from conceptnet5.util import get_data_filename
from conceptnet5.vectors.formats import load_hdf
from conceptnet5.vectors.transforms import l2_normalize_rows

RELATION_INDEX = pd.Index(COMMON_RELATIONS)
N_RELS = len(RELATION_INDEX)


random.seed(0)


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


ENTAILED_INDICES, UNRELATED_INDICES = _make_rel_chart()


def iter_edges_forever(filename):
    while True:
        yield from iter_edges_once(filename)


def iter_edges_once(filename):
    for line in open(filename, encoding='utf-8'):
        _assertion, relation, concept1, concept2, _rest = line.split('\t', 4)
        yield (relation, concept1, concept2, 1.)


class SemanticMatchingModel(nn.Module):
    def __init__(self, frame, use_cuda=True, relation_dim=8, batch_size=100):
        super().__init__()
        self.n_terms, self.term_dim = frame.shape
        self.relation_dim = relation_dim
        self.batch_size = batch_size

        # Initialize term embeddings, including the index that converts terms
        # from strings to row numbers
        self.index = frame.index
        self.term_vecs = nn.Embedding(frame.shape[0], self.term_dim)
        self.term_vecs.weight.data.copy_(
            torch.from_numpy(frame.values)
        )

        self.assoc_tensor = nn.Bilinear(
            self.term_dim, self.term_dim, self.relation_dim, bias=False
        )
        self.rel_vecs = nn.Embedding(N_RELS, self.relation_dim)

        # Using CUDA to run on the GPU requires different data types
        if use_cuda:
            self.float_type = torch.cuda.FloatTensor
            self.int_type = torch.cuda.LongTensor
            self.term_vecs = self.term_vecs.cuda()
            self.rel_vecs = self.rel_vecs.cuda()
            self.assoc_tensor = self.assoc_tensor.cuda()
        else:
            self.float_type = torch.FloatTensor
            self.int_type = torch.LongTensor

        self.identity_slice = self.float_type(np.eye(self.term_dim))
        self.reset_synonym_relation()

        self.truth_multiplier = nn.Parameter(self.float_type([5.]))
        self.truth_offset = nn.Parameter(self.float_type([-3.]))

    def reset_synonym_relation(self):
        self.assoc_tensor.weight.data[0] = self.identity_slice
        self.rel_vecs.weight.data[0, :] = 0
        self.rel_vecs.weight.data[0, 0] = 1

    def forward(self, rels, terms_L, terms_R):
        # Get relation vectors for the whole batch, with shape (b, i)
        rels_b_i = self.rel_vecs(rels)
        # Get left term vectors for the whole batch, with shape (b, j)
        terms_b_j = self.term_vecs(terms_L)
        # Get right term vectors for the whole batch, with shape (b, k)
        terms_b_k = self.term_vecs(terms_R)

        # Get the interaction of the terms in relation-embedding space, with
        # shape (b, i).
        inter_b_i = self.assoc_tensor(terms_b_j, terms_b_k)

        # Multiply our (b * i) term elementwise by rels_b_i. This indicates
        # how well the interaction between term j and term k matches each
        # component of the relation vector.
        relmatch_b_i = inter_b_i * rels_b_i

        # Add up the components for each item in the batch
        energy_b = torch.sum(relmatch_b_i, 1)

        norm_inter_b = torch.sum(inter_b_i * inter_b_i, 1)
        norm_rel_b = torch.sum(rels_b_i * rels_b_i, 1)

        return (
            energy_b * self.truth_multiplier + self.truth_offset,
            norm_inter_b,
            norm_rel_b
        )

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
                if rel not in COMMON_RELATIONS:
                    continue
                if not ENTAILED_INDICES[rel]:
                    continue

                left = uri_prefix(left)
                right = uri_prefix(right)

                # Possibly replace a relation with a more general relation
                if coin_flip():
                    rel = random.choice(ENTAILED_INDICES[rel])

                # Possibly swap the sides of a symmetric relation
                if rel in SYMMETRIC_RELATIONS and coin_flip():
                    left, right = right, left

                rel_idx = RELATION_INDEX.get_loc(rel)
                left_idx = self.index.get_loc(left)
                right_idx = self.index.get_loc(right)

                corrupt_rel_idx = rel_idx
                corrupt_left_idx = left_idx
                corrupt_right_idx = right_idx

                corrupt_which = random.randrange(5)
                if corrupt_which == 0:
                    if rel not in SYMMETRIC_RELATIONS and coin_flip():
                        corrupt_left_idx = right_idx
                        corrupt_right_idx = left_idx
                    else:
                        corrupt_rel_idx = random.choice(UNRELATED_INDICES[rel])
                elif corrupt_which == 1 or corrupt_which == 2:
                    while corrupt_left_idx == left_idx:
                        corrupt_left_idx = random.randrange(self.n_terms)
                else:
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

            if len(weights) == self.batch_size:
                break

        pos_data = (self.ltvar(pos_rels), self.ltvar(pos_left), self.ltvar(pos_right))
        neg_data = (self.ltvar(neg_rels), self.ltvar(neg_left), self.ltvar(neg_right))
        weights = autograd.Variable(self.float_type(weights))
        return pos_data, neg_data, weights

    def make_batches(self, edge_iterator):
        while True:
            yield self.positive_negative_batch(edge_iterator)

    def show_debug(self, batch, energy, positive):
        truth_values = energy
        rel_indices, left_indices, right_indices = batch
        if positive:
            print("POSITIVE")
        else:
            print("\nNEGATIVE")
        for i in range(len(energy)):
            rel = RELATION_INDEX[int(rel_indices.data[i])]
            left = self.index[int(left_indices.data[i])]
            right = self.index[int(right_indices.data[i])]
            value = truth_values.data[i]
            print("[%4.4f] %s %s %s" % (value, rel, left, right))

    @staticmethod
    def load_model(filename):
        frame = load_hdf(get_data_filename('vectors-20170630/mini.h5'))
        model = SemanticMatchingModel(l2_normalize_rows(frame.astype(np.float32)))
        model.load_state_dict(torch.load(filename))
        return model

    def evaluate_conceptnet(self, cutoff_value=-1):
        for pos_batch, neg_batch, weights in self.make_batches(
            iter_edges_once(get_data_filename('collated/sorted/edges-shuf.csv'))
        ):
            self.zero_grad()
            pos_energy, _, _ = self(*pos_batch)
            rel_indices, left_indices, right_indices = pos_batch
            for i in range(len(pos_energy)):
                value = pos_energy.data[i]
                if value < cutoff_value:
                    rel = RELATION_INDEX[int(rel_indices.data[i])]
                    left = self.index[int(left_indices.data[i])]
                    right = self.index[int(right_indices.data[i])]
                    assertion = assertion_uri(rel, left, right)
                    print("%4.4f\t%s" % (value, assertion))

    def train(self):
        relative_loss_function = nn.MarginRankingLoss(margin=0.5)
        absolute_loss_function = nn.BCEWithLogitsLoss()
        max_norm_loss_function = nn.MarginRankingLoss(margin=0)
        norm_loss_function = nn.MSELoss()

        optimizer = optim.SGD(self.parameters(), lr=0.1)
        losses = []
        true_target = autograd.Variable(self.float_type([1] * self.batch_size))
        false_target = autograd.Variable(self.float_type([0] * self.batch_size))
        steps = 0
        for pos_batch, neg_batch, weights in self.make_batches(
            iter_edges_forever(get_data_filename('collated/sorted/edges-shuf.csv'))
        ):
            self.zero_grad()
            pos_energy, pos_inter_norm, pos_rel_norm = self(*pos_batch)
            neg_energy, neg_inter_norm, neg_rel_norm = self(*neg_batch)

            synonymous = pos_batch[1]
            synonym_rel = autograd.Variable(self.int_type([0] * self.batch_size))
            synonym_energy, syn_inter_norm, _ = self(synonym_rel, synonymous, synonymous)

            loss = relative_loss_function(pos_energy, neg_energy, true_target)
            loss += absolute_loss_function(pos_energy, true_target)
            loss += absolute_loss_function(neg_energy, false_target)
            loss += absolute_loss_function(synonym_energy, true_target)
            for this_norm in [pos_inter_norm, pos_rel_norm, neg_inter_norm, neg_rel_norm]:
                loss += max_norm_loss_function(true_target, this_norm, true_target)
            loss += norm_loss_function(syn_inter_norm, true_target)

            loss.backward()
            optimizer.step()
            self.reset_synonym_relation()

            losses.append(loss.data[0])
            steps += 1
            if steps in (10, 20, 50, 100) or steps % 100 == 0:
                self.show_debug(neg_batch, neg_energy, False)
                self.show_debug(pos_batch, pos_energy, True)
                avg_loss = np.mean(losses)
                print("%d steps, loss=%4.4f" % (steps, avg_loss))
                losses.clear()
            if steps % 1000 == 0:
                torch.save(self.state_dict(), 'data/vectors/sme.model')
                print("saved")
        print()

    def ltvar(self, numbers):
        return autograd.Variable(self.int_type(numbers))


def get_model():
    if os.access('data/vectors/sme.model', os.F_OK):
        model = SemanticMatchingModel.load_model('data/vectors/sme.model')
    else:
        frame = load_hdf(get_data_filename('vectors-20170630/mini.h5'))
        model = SemanticMatchingModel(l2_normalize_rows(frame.astype(np.float32)))
    return model


if __name__ == '__main__':
    model = get_model()
    model.train()
    # model.evaluate_conceptnet()
