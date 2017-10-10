import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd

from conceptnet5.relations import ALL_RELATIONS, SYMMETRIC_RELATIONS


RELATION_INDEX = pd.Index(ALL_RELATIONS)
N_RELS = len(RELATION_INDEX)
RELATION_DIM = 5


class SemanticMatchingModel(nn.Module):
    def __init__(self, frame):
        self.n_terms, self.term_dim = frame.shape[0], frame.shape[1]
        self.index = frame.index
        self.term_vecs = nn.Embedding(frame.shape[0], self.term_dim)
        self.term_vecs.weight.data.copy_(
            torch.from_numpy(frame.values)
        )
        self.rel_vecs = nn.Embedding(N_RELS, RELATION_DIM)
        self.assoc_tensor = autograd.Variable(
            torch.Tensor(RELATION_DIM, self.term_dim, self.term_dim)
        )

    def forward(self, rels, terms_L, terms_R):
        # Get relation vectors for the whole batch, with shape (b * i)
        rels_b_i = self.rel_vecs(rels)
        # Get left term vectors for the whole batch, with shape (b * j)
        terms_b_j = self.term_vecs(terms_L)
        # Get right term vectors for the whole batch, with shape (b * k)
        terms_b_k = self.term_vecs(terms_R)
        # Reshape our (i * j * k) assoc_tensor into (i * jk)
        assoc_i_jk = self.assoc_tensor.view(RELATION_DIM, -1)
        # Matrix multiplication: (b * i) x (i * jk) -> (b * jk)
        inter_b_jk = torch.mm(rel_vecs, rel_i_jk)
        # Reshape this intermediate result to (b * j * k)
        inter_b_j_k = inter_b_jk.view(-1, self.term_dim, self.term_dim)

        # Reshape the left term vectors to (b * 1 * j)
        terms_b_1_j = terms_b_j.view(-1, 1, self.term_dim)
        # Reshape the right term vectors to (b * k * 1)
        terms_b_k_1 = terms_b_k.view(-1, self.term_dim, 1)
        # Batch matrix multiplication: (b * 1 * j) x (b * j * k) -> (b * 1 * k)
        inter_b_1_k = torch.bmm(terms_b_1_j, inter_b_j_k)
        # Batch matrix multiplication: (b * 1 * k) x (b * k * 1) -> (b * 1 * 1)
        energy_b_1_1 = torch.bmm(inter_b_1_k, terms_b_k_1)
        energy_b = energy_b_1_1.view(-1)
        return energy_b
