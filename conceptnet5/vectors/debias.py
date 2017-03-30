from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import standardized_uri, get_vector, cosine_similarity, normalize_vec
from conceptnet5.vectors.transforms import l2_normalize_rows
import numpy as np
import pandas as pd
from sklearn import svm


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
    'accountant', 'paralegal'
    'addiction', 'eating disorder',
    'professor emeritus', 'associate professor',
    'programmer', 'homemaker'
]


def get_weighted_vector(frame, weighted_terms):
    total = frame.iloc[0] * 0.
    for term, weight in weighted_terms:
        if term in frame.index:
            vec = frame.loc[term]
            total += vec * weight
    return normalize_vec(total)


def get_category_axis(frame, category_examples):
    return get_weighted_vector(
        frame,
        [(standardized_uri('en', term), 1.)
         for term in category_examples]
    )


def reject_subspace(frame, axes):
    current_array = frame.copy()
    for axis in axes:
        axis = normalize_vec(axis)
        projection = current_array.dot(axis)
        current_array -= np.outer(projection, axis)

    return l2_normalize_rows(current_array, offset=1e-9)


def get_vocabulary_vectors(frame, vocab):
    uris = [standardized_uri('en', term) for term in vocab]
    return frame.loc[uris].dropna()


def two_class_svm(frame, pos_vocab, neg_vocab):
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


def de_bias_category(frame, category_examples, bias_examples):
    category_predictor = two_class_svm(frame, category_examples, bias_examples)
    applicability = category_predictor.predict_proba(frame)[:, 1]

    vocab = [
        standardized_uri('en', term) for term in bias_examples
    ]
    components_to_reject = frame.loc[vocab].values
    modified_component = reject_subspace(frame, components_to_reject).mul(applicability, axis=0)
    original_component = frame.mul(1 - applicability, axis=0)
    return l2_normalize_rows(original_component + modified_component)


def de_bias_binary(frame, pos_examples, neg_examples, left_examples, right_examples):
    category_predictor = two_class_svm(frame, pos_examples, neg_examples)
    applicability = category_predictor.predict_proba(frame)[:, 1]
    bias_axis = get_category_axis(frame, right_examples) - get_category_axis(frame, left_examples)
    modified_component = reject_subspace(frame, [bias_axis]).mul(applicability, axis=0)
    original_component = frame.mul(1 - applicability, axis=0)
    return l2_normalize_rows(original_component + modified_component)


def de_bias_frame(frame):
    """
    Take in a DataFrame representing a semantic space, and make a strong
    effort to modify it to remove biases and prejudices against certain
    classes of people.

    The resulting space attempts not to learn stereotyped associations with
    anyone's race, color, religion, national origin, sex, gender presentation,
    or sexual orientation.
    """
    newframe = de_bias_category(frame, PEOPLE_BY_ETHNICITY, CULTURE_PREJUDICES + SEX_PREJUDICES)
    newframe = de_bias_category(newframe, PEOPLE_BY_BELIEF, CULTURE_PREJUDICES + SEX_PREJUDICES)
    newframe = de_bias_category(newframe, FEMALE_WORDS + MALE_WORDS + ORIENTATION_WORDS + AGE_WORDS, CULTURE_PREJUDICES + SEX_PREJUDICES)
    newframe = de_bias_binary(newframe, GENDER_NEUTRAL_WORDS, GENDERED_WORDS, MALE_WORDS, FEMALE_WORDS)
    return newframe
