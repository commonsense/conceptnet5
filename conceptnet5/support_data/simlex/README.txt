SimLex-999 is a gold standard resource for the evaluation of models that learn the meaning of words and concepts.

SimLex-999 provides a way of measuring how well models capture similarity, rather than relatedness or association.

A detailed description of the dataset including how data was collected can be found in the following publication: 

SimLex-999: Evaluating Semantic Models with (Genuine) Similarity Estimation. 2014. Felix Hill, Roi Reichart and Anna Korhonen.

PLEASE CITE THIS PUBLICATION IF USING SIMLEX-999 IN YOUR RESEARCH.

If you are unsure about aspects of the dataset, the paper may well be instructive. Otherwise send an email to Felix Hill: 
felix.hill@cl.cam.ac.uk 

#########################################################################################################
# Dataset Description # 

SimLex-999.txt is a tab separated plaintext file, where rows correspond to concept pairs and columns correspond to properties of each pair. 

# word1: The first concept in the pair.

# word2: The second concept in the pair. Note that the order is only relevant to the column Assoc(USF). These values (free association scores) are asymmetric. All other values are symmetric properties independent of the ordering word1, word2. 

# POS: The majority part-of-speech of the concept words, as determined by occurrence in the POS-tagged British National Corpus. Only pairs of matching POS are included in SimLex-999. 

# SimLex999: The SimLex999 similarity rating. Note that average annotator scores have been (linearly) mapped from the range [0,6] to the range [0,10] to match other datasets such as WordSim-353. 

# conc(w1): The concreteness rating of word1 on a scale of 1-7. Taken from the University of South Florida Free Association Norms database. 

# conc(w2): The concreteness rating of word2 on a scale of 1-7. Taken from the University of South Florida Free Association Norms database. 

# concQ: The quartile the pair occupies based on the two concreteness ratings. Used for some analyses in the above paper. 

# Assoc(USF): The strength of free association from word1 to word2. Values are taken from the University of South Florida Free Association Dataset. 

# SimAssoc333: Binary indicator of whether the pair is one of the 333 most associated in the dataset (according to Assoc(USF)). This subset of SimLex999 is often the hardest for computational models to capture because the noise from high association can confound the similarity rating. See the paper for more details. 

# SD(SimLex): The standard deviation of annotator scores when rating this pair. Low values indicate good agreement between the 15+ annotators on the similarity value SimLex999. Higher scores indicate less certainty. 
