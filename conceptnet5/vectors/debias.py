import numpy as np
import pandas as pd
from sklearn import svm
from sklearn.preprocessing import normalize

from conceptnet5.vectors import normalize_vec, standardized_uri

# A list of English words referring to nationalities, nations, ethnicities, and
# religions. Our goal is to prevent ConceptNet from learning insults and
# stereotypes about these classes of people.

PEOPLE_BY_ETHNICITY = [
    # Regions of the world
    'africa', 'african', 'sub-saharan',
    'america', 'american',
    'caribbean',
    'polynesia', 'polynesian',
    'asia', 'asian',
    'europe', 'european',
    'middle east', 'middle eastern',
    'arabia', 'arabian', 'arab'
    'latin america', 'latin american', 'latino', 'latina', 'hispanic',

    # Colors used as races
    'white', 'black', 'brown',

    # A perhaps unnecessarily thorough list of countries (by Wikipedia's
    # definition, mostly).
    'abkhazia', 'abkhazian',
    'afghanistan', 'afghani',
    'albania', 'albanian',
    'algeria', 'algerian',
    'american samoa', 'american samoan',
    'andorra', 'andorran',
    'angola', 'angolan',
    'anguilla', 'anguillan',
    'antigua', 'antiguan', 'barbuda', 'barbudan',
    'argentina', 'argentinian',
    'armenia', 'armenian',
    'aruba', 'aruban',
    'australia', 'australian',
    'austria', 'austrian',
    'azerbaijan', 'azerbaijani',
    'bahamas', 'bahamian',
    'bahrain', 'bahraini',
    'bangladesh', 'bangladeshi',
    'barbados', 'barbadian',
    'belgium', 'belgian',
    'belarus', 'belarusian',
    'belize', 'belizean',
    'benin', 'beninese',
    'bermuda', 'bermudan',
    'bhutan', 'bhutanian',
    'bolivia', 'bolivian',
    'bonaire',
    'bosnia', 'bosnian', 'herzegovina', 'herzegovinian',
    'botswana', 'botswanan',
    'brazil', 'brazilian',
    'brunei', 'bruneian',
    'bulgaria', 'bulgarian',
    'burkina faso', 'burkinabé',
    'burma', 'burmese', 'myanmar',
    'burundi', 'burundian',
    'cabo verde', 'cape verde',
    'cambodia', 'cambodian',
    'cameroon', 'cameroonian',
    'canada', 'canadian',
    'cayman islands', 'caymanian',
    'central african republic',
    'chad', 'chadian',
    'chile', 'chilean',
    'china', 'chinese',
    'taiwan', 'taiwanese',
    'colombia', 'colombian',
    'comoros', 'comorian',
    'congo', 'congolese',
    'costa rica', 'costa rican',
    "côte d'ivoire", 'ivory coast', 'ivorian',
    'croatia', 'croatian',
    'cuba', 'cuban',
    'curaçao', 'curaçaoan',
    'cyprus', 'cypriot',
    'czech republic', 'czech', 'czechia',
    'denmark', 'danish',
    'djibouti', 'djiboutian',
    'dominica', 'dominican',
    'dominican republic',
    'east timor', 'timorese', 'timor-leste',
    'ecuador', 'ecuadoran',
    'egypt', 'egyptian',
    'el salvador', 'salvadoran',
    'england', 'english',
    'equatorial guinea', 'equatoguinean',
    'eritrea', 'eritrean',
    'estonia', 'estonian',
    'ethiopia', 'ethiopian',
    'faroe islands', 'faroese',
    'fiji', 'fijian',
    'finland', 'finnish',
    'france', 'french',
    'gabon', 'gabonese',
    'georgia',
    'germany', 'german',
    'ghana', 'ghanaian',
    'gibraltar',
    'great britain', 'british',
    'greece', 'greek',
    'greenland', 'greenlandic',
    'grenada', 'grenadian',
    'gambia', 'gambian',
    'guinea', 'guinean',
    'guatemala', 'guatemalan',
    'guadeloupe',
    'guam', 'guamanian',
    'guinea-bissau', 'bissau-guinean',
    'guyana', 'guyanese',
    'haiti', 'haitian',
    'honduras', 'honduran',
    'hong kong', 'hongkongese',
    'hungary', 'hungarian',
    'iceland', 'icelandic',
    'india', 'indian',
    'indonesia', 'indonesian',
    'iraq', 'iraqi',
    'iran', 'iranian',
    'ireland', 'irish',
    'isle of man', 'manx',
    'israel', 'israeli',
    'italy', 'italian',
    'jamaica', 'jamaican',
    'japan', 'japanese',
    'jordan', 'jordanian',
    'kazakhstan', 'kazakh',
    'kenya', 'kenyan',
    'kiribati', 'i-kiribati',
    'korea', 'korean',
    'north korea', 'north korean',
    'south korea', 'south korean',
    'kosovo', 'kosovar',
    'kuwait', 'kuwaiti',
    'kyrgyzstan', 'kyrgyz',
    'laos', 'laotian',
    'latvia', 'latvian',
    'lebanon', 'lebanese',
    'lesotho', 'basotho',
    'liberia', 'liberian',
    'libya', 'libyan',
    'liechtenstein', 'liechtensteiner',
    'lithuania', 'lithuanian',
    'luxembourg', 'luxembourgish',
    'macau', 'macanese',
    'macedonia', 'macedonian',
    'madagascar', 'malagasy',
    'malawi', 'malawian',
    'malaysia', 'malaysian',
    'maldives', 'maldivian',
    'mali', 'malinese',
    'malta', 'maltese',
    'marshall islands', 'marshallese',
    'martinique', 'martinican',
    'mauritania', 'mauritanian',
    'mauritius', 'mauritian',
    'mayotte', 'mahoran',
    'mexico', 'mexican',
    'micronesia', 'micronesian',
    'moldova', 'moldovan',
    'monaco', 'monégasque',
    'mongolia', 'mongolian',
    'montenegro', 'montenegrin',
    'morocco', 'moroccan',
    'mozambique', 'mozambican',
    'namibia', 'namibian',
    'nauru', 'nauruan',
    'nepal', 'nepali',
    'netherlands', 'dutch',
    'new caledonia', 'new caledonian',
    'new zealand',
    'nicaragua', 'nicaraguan',
    'niger', 'nigerien',
    'nigeria', 'nigerian',
    'niue', 'niuean',
    'norway', 'norwegian',
    'oman', 'omani',
    'pakistan', 'pakistani',
    'palau', 'palauan',
    'palestine', 'palestinian',
    'panama', 'panamanian',
    'papua new guinea', 'papuan',
    'paraguay', 'paraguayan',
    'peru', 'peruvian',
    'phillipines', 'filipino',
    'poland',
    'portugal', 'portuguese',
    'puerto rico', 'puerto rican',
    'qatar', 'qatari',
    'réunion', 'réunionese',
    'romania', 'romanian',
    'russia', 'russian',
    'rwanda', 'rwandan',
    'saint lucia', 'saint lucian',
    'saint vincent and the grenadines', 'vincentian',
    'samoa', 'samoan',
    'san marino', 'sammarinese',
    'são tome and principe', 'são toméan',
    'saudi arabia', 'saudi arabian',
    'scotland', 'scottish',
    'senegal', 'senegalese',
    'serbia', 'serbian',
    'seychelles', 'seychellois',
    'sierra leone', 'sierra leonean',
    'singapore', 'singaporean',
    'slovakia', 'slovakian',
    'slovenia', 'slovenian',
    'somalia', 'somalian',
    'somaliland', 'somalilander',
    'south africa', 'south african',
    'south sudan', 'south sudanese',
    'spain', 'spanish',
    'sri lanka', 'sri lankan',
    'sudan', 'sudanese',
    'surinam', 'surinamese',
    'svalbard',
    'swaziland', 'swazi',
    'sweden', 'swedish',
    'switzerland', 'swiss',
    'syria', 'syrian',
    'tajikistan', 'tajikistani',
    'tanzania', 'tanzanian',
    'thailand', 'thai',
    'togo', 'togolese',
    'tokelau', 'tokelauan',
    'tonga', 'tongan',
    'trinidad', 'trinidadian',
    'tobago', 'tobagonian',
    'tunisia', 'tunisian',
    'turkey', 'turkish',
    'turkmenistan', 'turkmen',
    'tuvalu', 'tuvaluan',
    'uganda', 'ugandan',
    'ukraine', 'ukrainian',
    'united arab emirates', 'emirati',
    'united kingdom',
    'united states',
    'uruguay', 'uruguayan',
    'uzbekistan', 'uzbek',
    'vanuatu', 'vanuatuan',
    'venezuela', 'venezuelan',
    'vietnam', 'vietnamese',
    'virgin islands',
    'wales', 'welsh',
    'wallis and futuna', 'wallisian', 'futunan',
    'western sahara', 'sahrawi',
    'yemen', 'yemeni',
    'zambia', 'zambian',
    'zimbabwe', 'zimbabwean'
]

PEOPLE_BY_BELIEF = [
    'agnosticism', 'agnostic',
    'atheism', 'atheist',
    'buddhism', 'buddhist',
    "bahà'i",
    'catholicism', 'catholic',
    'christianity', 'christian',
    'humanism', 'humanist', 'secular',
    'islam', 'muslim',
    'jainism', 'jain',
    'judaism', 'jewish',
    'mormonism', 'mormon',
    'orthodox',
    'paganism', 'pagan',
    'protestantism', 'protestant',
    'shinto',
    'sikhism', 'sikh',
    'zoroastrianism', 'zoroastrian',
]


# A list of things we don't want our semantic space to learn about various
# cultures of people. This list doesn't have to be exhaustive; we're modifying
# the whole vector space, so nearby terms will also be affected.
CULTURE_PREJUDICES = [
    'illegal', 'terrorist', 'evil', 'threat',
    'dumbass', 'shithead', 'wanker', 'dickhead',
    'illiterate', 'ignorant', 'inferior',
    'good',
    'sexy', 'suave',
    'wealthy', 'poor',
    'racist', 'slavery',
    'torture', 'fascist', 'persecute',
    'fraudster', 'rapist', 'robber', 'dodgy', 'perpetrator',
]

# Numberbatch acquires a "porn bias" from the Common Crawl via GloVe.
# Because so much of the Web is about porn, words such as 'teen', 'girl', and
# 'girlfriend' acquire word associations from porn.
#
# We handle this and related problems by making an axis of words that refer to
# gender or sexual orientation, and exclude them from making associations with
# porn and sexually-degrading words.

FEMALE_WORDS = [
    'woman', 'feminine', 'female',
    'girl', 'girlfriend', 'wife', 'mother', 'sister', 'daughter',
]

MALE_WORDS = [
    'man', 'masculine', 'male',
    'boy', 'boyfriend', 'husband', 'father', 'brother', 'son'
]

ORIENTATION_WORDS = [
    'gay', 'lesbian', 'bisexual', 'trans', 'transgender'
]

AGE_WORDS = [
    'young', 'teen', 'old'
]

SEX_PREJUDICES = [
    'slut', 'whore', 'shrew', 'bitch', 'faggot',
    'sexy', 'fuck', 'fucked', 'fucker', 'nude', 'porn',
    'cocksucker'
]

GENDERED_WORDS = FEMALE_WORDS + MALE_WORDS

# Words identified as gender stereotypes by 10 Turkers, in Bolukbasi et al.,
# "Quantifying and Reducing Stereotypes in Word Embeddings".
# https://arxiv.org/pdf/1606.06121.pdf
GENDER_NEUTRAL_WORDS = [
    'surgeon', 'nurse',
    'doctor', 'midwife',
    'paramedic', 'registered nurse',
    'hummer', 'minivan',
    'karate', 'gymnastics',
    'woodworking', 'quilting',
    'alcoholism', 'eating disorder',
    'athlete', 'gymnast',
    'neurologist', 'therapist',
    'hockey', 'figure skating',
    'architect', 'interior designer',
    'chauffeur', 'nanny',
    'curator', 'librarian',
    'pilot', 'flight attendant',
    'drug trafficking', 'prostitution',
    'musician', 'dancer',
    'beer', 'cocktail',
    'weightlifting', 'gymnastics',
    'headmaster', 'guidance counselor',
    'workout', 'pilates',
    'home depot', 'jcpenney',
    'carpentry', 'sewing',
    'accountant', 'paralegal',
    'addiction', 'eating disorder',
    'professor emeritus', 'associate professor',
    'programmer', 'homemaker'
]


def make_shard_endpoints(total_length, shard_size=int(1e6)):
    """
    Partition the half-open integer interval [0, total_length) into a
    sequence of half-open subintervals [s0,e0), [s1,e1), ... [s_n, e_n)
    such that s0 = 0, s_(k+1) = e_k, e_n = total_length, and each of these
    subintervals (except possibly the last) has length equal to the given
    shard_size.  Return the sequence of pairs of endpoints of the
    subintervals.
    """
    shard_end = 0
    shards = []
    while True:
        shard_start = shard_end
        shard_end = shard_start + shard_size
        if shard_end > total_length:
            shard_end = total_length
        if shard_start >= shard_end:
            break
        shards.append((shard_start, shard_end))
    return shards


def get_weighted_vector(frame, weighted_terms):
    """
    Given a list of (term, weight) pairs, get a unit vector corresponding
    to the weighted average of those term vectors.

    A simplified version of VectorSpaceWrapper.get_vector().
    """
    total = frame.iloc[0] * 0.
    for term, weight in weighted_terms:
        if term in frame.index:
            vec = frame.loc[term]
            total += vec * weight
    return normalize_vec(total)


def get_category_axis(frame, category_examples):
    """
    Get a vector representing the average of several example terms, where
    the terms are specified as plain English text.
    """
    return get_weighted_vector(
        frame,
        [(standardized_uri('en', term), 1.)
         for term in category_examples]
    )


def reject_subspace(frame, vecs):
    """
    Return a modification of the vector space `frame` where none of
    its rows have any correlation with any rows of `vecs`, by subtracting
    the outer product of `frame` with each normalized row of `vecs`.
    """
    current_array = frame.copy().values
    for vec in vecs:
        vec = normalize_vec(vec)
        projection = current_array.dot(vec)
        np.subtract(current_array, np.outer(projection, vec), out=current_array)

    normalize(current_array, norm='l2', copy=False)

    current_array = pd.DataFrame(current_array, index=frame.index)
    current_array.fillna(0, inplace=True)
    return current_array


def get_vocabulary_vectors(frame, vocab):
    """
    Given a vocabulary (as a list of English terms), get a sub-frame of the
    given DataFrame containing just the known vectors for that vocabulary.
    """
    uris = [standardized_uri('en', term) for term in vocab]
    return frame.reindex(uris).dropna()


def two_class_svm(frame, pos_vocab, neg_vocab):
    """
    Given a DataFrame of word vectors, and lists of words that should be
    positive or negative examples of a given category, get a linear
    decision boundary between them (and a function that estimates the
    probability of the membership of a word in that category) using an SVM.
    """
    pos_vecs = get_vocabulary_vectors(frame, pos_vocab)
    pos_values = np.ones(pos_vecs.shape[0])
    neg_vecs = get_vocabulary_vectors(frame, neg_vocab)
    neg_values = -np.ones(neg_vecs.shape[0])
    vecs = np.vstack([pos_vecs.values, neg_vecs.values])
    values = np.concatenate([pos_values, neg_values])

    svc = svm.SVC(
        verbose=False, random_state=0, max_iter=10000, class_weight='balanced',
        probability=True, kernel='linear'
    )
    svc.fit(vecs, values)
    return svc


def de_bias_binary(frame, pos_examples, neg_examples, left_examples, right_examples):
    """
    De-bias a distinction that is presumed - for the purposes of de-biasing -
    to form two ends of a scale. The prototypical example is male vs. female,
    where words that are not inherently defined by gender end up being "more
    male" or "more female" due to stereotypes and biases in the data.

    The goal is not to remove the distinction from every word in the system's
    vocabulary, only those where making the distinction is inappropriate. A
    gender distinction between "she" and "he" is appropriate. A gender
    distinction between "doctor" and "nurse" is inappropriate.

    This function takes in four lists of vocabulary:

    - "Positive examples": examples of words that *should* be de-biased,
      such as "doctor" and "nurse" in the case of gender.

    - "Negative examples": examples of words that *should not* be de-biased,
      such as "she" and "he".

    - "Left examples": words that define one end of the distinction to be
      de-biased, such as "man".

    - "Right examples": words that define the other end of the distinction,
      such as "woman".

    The left and right examples are probably also good negative examples:
    they appropriately represent the distinction to be made, so they should
    not be de-biased.
    """
    # Make the SVM that distinguishes positive examples (words that should
    # be de-biased) from negative examples.
    category_predictor = two_class_svm(frame, pos_examples, neg_examples)

    # The SVM can predict the probability, for each vector in the frame, that
    # it's in each class. The positive class is column 1 of this prediction.
    # This gives us a vector of how much each word in the vocabulary should be
    # de-biased.  This is done on shards, to reduce peak memory consumption.
    applicability = np.zeros(shape=(len(frame),), dtype=np.float32)
    for shard_start, shard_end in make_shard_endpoints(len(frame)):
        applicability[shard_start:shard_end] = category_predictor.predict_proba(
            frame[shard_start:shard_end])[:, 1]
    del category_predictor

    # The bias axis is the vector difference between the average right example
    # and the average left example.
    bias_axis = get_category_axis(frame, right_examples) - get_category_axis(frame, left_examples)

    # Make a modified version of the space that projects the bias axis to 0.
    # Then weight each row of that space by "applicability", the probability
    # that each row should be de-biased.  This is also done on shards.
    modified_component = np.zeros(shape=frame.values.shape, dtype=np.float32)
    for shard_start, shard_end in make_shard_endpoints(len(frame)):
        modified_component[shard_start:shard_end, :] = \
            reject_subspace(frame[shard_start:shard_end], [bias_axis]).mul(
                applicability[shard_start:shard_end], axis=0).values

    # Make another component representing the vectors that should not be
    # de-biased: the original space times (1 - applicability).
    np.multiply(1 - applicability.reshape((len(frame), 1)), frame.values,
                out=frame.values)

    # The sum of these two components is the de-biased space, where de-biasing
    # applies to each row proportional to its applicability.
    np.add(frame.values, modified_component, out=frame.values)
    del modified_component

    # L_2-normalize the resulting rows in-place.
    normalize(frame.values, norm='l2', copy=False)


def de_bias_category(frame, category_examples, bias_examples):
    """
    Remove correlations between a class of words that should have biases
    removed (category_examples) and a set of words reflecting those biases
    (bias_examples). For example, the `category_examples` may be ethnicities,
    and `bias_examples` may be stereotypes about them.

    The check for whether a word should be de-biased works like
    `de_bias_binary`, where the category words are positive examples and the
    bias words are negative examples (because the words that define the bias
    presumably should not be de-biased).

    The words that should be de-biased will have their correlations with
    each of the bias words removed.
    """
    # Make an SVM that distinguishes words that are in the category to be
    # de-biased from words that are not.
    category_predictor = two_class_svm(frame, category_examples, bias_examples)

    # Predict the probability of each word in the vocabulary being in the
    # category.  This is done on shards, to reduce peak memory consumption.
    applicability = np.zeros(shape=(len(frame),), dtype=np.float32)
    for shard_start, shard_end in make_shard_endpoints(len(frame)):
        applicability[shard_start:shard_end] = category_predictor.predict_proba(
            frame[shard_start:shard_end])[:, 1]
    del category_predictor

    # Make a matrix of vectors representing the correlations to remove.
    vocab = [
        standardized_uri('en', term) for term in bias_examples
    ]
    components_to_reject = frame.reindex(vocab).dropna().values

    # Make a modified version of the space that projects the bias vectors to 0.
    # Then weight each row of that space by "applicability", the probability
    # that each row should be de-biased.  This is also done on shards.
    modified_component = np.zeros(shape=frame.values.shape, dtype=np.float32)
    for shard_start, shard_end in make_shard_endpoints(len(frame)):
        modified_component[shard_start:shard_end, :] = \
            reject_subspace(frame[shard_start:shard_end], components_to_reject).mul(
                applicability[shard_start:shard_end], axis=0).values
    del components_to_reject

    # Make another component representing the vectors that should not be
    # de-biased: the original space times (1 - applicability).
    np.multiply(1 - applicability.reshape((len(frame), 1)), frame.values,
                out=frame.values)

    # The sum of these two components is the de-biased space, where de-biasing
    # applies to each row proportional to its applicability.
    np.add(frame.values, modified_component, out=frame.values)
    del modified_component

    # L_2-normalize the resulting rows in-place.
    normalize(frame.values, norm='l2', copy=False)


def de_bias_frame(frame):
    """
    Take in a DataFrame representing a semantic space, and make a strong
    effort to modify it to remove biases and prejudices against certain
    classes of people.

    The resulting space attempts not to learn stereotyped associations with
    anyone's race, color, religion, national origin, sex, gender presentation,
    or sexual orientation.

    The input frame is modified in-place; this can save considerable memory
    with realistically sized semantic spaces.
    """
    de_bias_category(frame, PEOPLE_BY_ETHNICITY, CULTURE_PREJUDICES + SEX_PREJUDICES)
    de_bias_category(frame, PEOPLE_BY_BELIEF, CULTURE_PREJUDICES + SEX_PREJUDICES)
    de_bias_category(
        frame,
        FEMALE_WORDS + MALE_WORDS + ORIENTATION_WORDS + AGE_WORDS,
        CULTURE_PREJUDICES + SEX_PREJUDICES
    )
    de_bias_binary(frame, GENDER_NEUTRAL_WORDS, GENDERED_WORDS, MALE_WORDS, FEMALE_WORDS)
