import json
import plum
from collections import defaultdict
import random

from get_style_json import create_json


CONFIG = """
local PM = import 'PM.libsonnet';
local ds = PM.s2s.parallel_jsonl(
    "{data_dir}/SOURCE_80.jsonl",
    "{data_dir}/TARGET_80.jsonl",
    name="valid");
local src_tkn_vocab = PM.vocab.load("{styleeq_dir}/vocabs/source_tokens.pth");
local src_lem_vocab = PM.vocab.load("{styleeq_dir}/vocabs/source_lemmas.pth");
local pos_fine_vocab = PM.vocab.load("{styleeq_dir}/vocabs/pos_fine.pth");
local pos_coarse_vocab = PM.vocab.load("{styleeq_dir}/vocabs/pos_coarse.pth");
local ctrl_genre_vocab = PM.vocab.load("{styleeq_dir}/vocabs/ctrl_genre.pth", name="genre");
local tgt_tkn_vocab = PM.vocab.load("{styleeq_dir}/vocabs/target_tokens.pth");
local ctrl_list = ["conjunction", "determiner", "thirdNeutralPerson",
                   "thirdFemalePerson", "thirdMalePerson",
                   "firstPerson", "secondPerson", "thirdPerson",
                   "helperVerbs", "negation",
                   "simplePreposition",
                   "positionSimplePreposition",
                   "punctuation", "countParseS", "countParseSBAR",
                   "countParseADVP", "countParseFRAG"];
local pipelines = {{
    source_tokens: [
        0, "sequence", "tokens sensored",
        PM.data.pipeline.pad_list("<sos>", end=false),
        PM.data.pipeline.vocab_lookup(src_tkn_vocab),
    ],
    source_lemmas: [
        0, "sequence", "lemmas sensored",
        PM.data.pipeline.pad_list("<sos>", end=false),
        PM.data.pipeline.vocab_lookup(src_lem_vocab),
    ],
    source_pos_fine: [0, "sequence", "pos ptb",
        PM.data.pipeline.pad_list("<sos>", end=false),
        PM.data.pipeline.vocab_lookup(pos_fine_vocab),
    ],
    source_pos_coarse: [
        0, "sequence", "pos uni",
        PM.data.pipeline.pad_list("<sos>", end=false),
        PM.data.pipeline.vocab_lookup(pos_coarse_vocab),
    ],
}} + {{
    [ctrl]: [
        0, "controls", ctrl,
        {{
            __plum_type__: "dataio.pipeline.threshold_feature",
            thresholds: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                         11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        }},
        PM.data.pipeline.long_tensor(),
    ],
    for ctrl in ctrl_list
}};
local collate_funcs = {{
    source_tokens: PM.data.pipeline.batch_sequence_ndtensor(0, 0, 1),
    source_lemmas: PM.data.pipeline.batch_sequence_ndtensor(0, 0, 1),
    source_pos_fine: PM.data.pipeline.batch_sequence_ndtensor(0, 0, 1),
    source_pos_coarse: PM.data.pipeline.batch_sequence_ndtensor(0, 0, 1),
}} + {{
    [ctrl]: PM.data.pipeline.batch_sequence_ndtensor(0, 0, 1),
    for ctrl in ctrl_list
}};
local batches = PM.data.batches(
    ds,
    batch_size=1,
    num_workers=1,
    pipelines=pipelines,
    collate_funcs=collate_funcs,
    sort=true,
    sort_key=[0, "sequence", "tokens sensored", PM.data.pipeline.len()],
    sort_descending=true,
); 
[batches, tgt_tkn_vocab, ds]
"""

def load_batcher(proj_dir, data_dir):
    config = CONFIG.format(styleeq_dir=str(proj_dir),
                           data_dir=str(data_dir))
    plum_parser = plum.parser.PlumParser()
    (batches, target_vocab, ds), plum_pointers = plum_parser.parse_string(
        config)
    db = load_database(ds)
    
    return batches, target_vocab, db

def load_database(ds):
    database = defaultdict(lambda: defaultdict(list))
    for example in ds:
        genre = example[0]['controls']['genre']
        count = len(example[0]["sequence"]["tokens sensored"])
        new_item = dict(example[0])
        new_item["original"] = example[1]["reference_string"]
        database[genre][count].append(new_item)
    return database

def load_model(proj_dir):
    ckpt_dir = proj_dir / "train" / "run1" / "model_checkpoints"
    meta = json.loads((ckpt_dir / "ckpt.metadata.json").read_text())
    model_path = ckpt_dir / meta['optimal_checkpoint']
    return plum.load(model_path).eval()

def get_close_sent(base, new, database, verbose=False):
    """
    Return list of source objs most similar to base source obj w genre new.
    :param base: source json obj as string (json.loads(base))
    :param new: string of new genre, e.g. 'scifi'
    :param source: string path to file with source objs e.g. 'SOURCE_80.jsonl'
    :param verbose: boolean, if True prints some info as it runs
    :return options: list of dict
    """

    l = len(base["sequence"]["tokens sensored"])
    options = database[new][l]

    if verbose:
        print('same len', len(options))

    def slim_down_options(options, count_func, n=25, v=''):
        """Slim options if more than n left."""
        if len(options) > 100:
            options_slim = []
            c = count_func(base)
            for obj in options:
                if c == count_func(obj):
                    options_slim.append(obj)
            if len(options_slim) > n:
                options = options_slim
                if verbose:
                    print(v, len(options))
        return options
    # select ones w same number of PROPN
    def f(o):
        return o['sequence']['proper nouns'].count(' ')
    options = slim_down_options(options, f, v='same num PROPN')

    # select ones w same number of NOUNS
    def f(o):
        return o['sequence']['pos uni'].count('NOUN')
    options = slim_down_options(options, f, v='same num NOUNS')

    # select ones w same number of VERBS
    def f(o):
        return o['sequence']['pos uni'].count('VERB')
    options = slim_down_options(options, f, v='same num VERBS')

    # select ones w same number of ADJ
    def f(o):
        return o['sequence']['pos uni'].count('ADJ')
    options = slim_down_options(options, f, v='same num ADJ')

    return options

def make_transfer_inputs(orig, database, genre, num_opts=8):
    options = list(get_close_sent(orig, genre, database))
    random.shuffle(options)

    batch = []
    for opt in options[:num_opts]:
        batch.append(
            [
                {
                    "sequence": orig["sequence"], 
                    "controls": opt["controls"],
                    "source_string": " ".join(opt["sequence"]["original"]),
                }
            ]
        )

    return batch

def get_features(sentences):
    feats = [json.loads(create_json(s, source=True)) for s in sentences]
    for i, s in enumerate(sentences):
        feats[i]["original"] = s
    return feats

def get_pivots(features, db, genre, opts=8):
    pivots = []
    for feature in features:
        options = list(get_close_sent(feature, genre, db))
        random.shuffle(options)
        pivots.append(options[:opts])
    return pivots
