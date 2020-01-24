#!flask/bin/python
from flask import Flask, jsonify, request
import argparse
from pathlib import Path
import json
from styleeq_utils import load_model, load_batcher, get_features, get_pivots
from plum.seq2seq.search import BeamSearch
import numpy as np


app = Flask(__name__)

@app.route('/styleeq/api/v1.0/getpivots', methods=['POST'])
def getpivots():
    sources = request.json["sources"]
    if "genre" in request.json:
        genre = request.json["genre"]
        num_opts = min(request.json.get("num_pivots", 8), 32)
        features = get_features(sources)    
        pivots = get_pivots(features, app.PLUM["db"], genre, num_opts)
        return jsonify({"sources": sources, "features": features,
                        "pivots": pivots})
    else:
        features = get_features(sources)
        pivots = request.json["pivots"]
        pivots = [get_features(p) for p in pivots]
        return jsonify({"sources": sources, "features": features,
                        "pivots": pivots})
        

@app.route('/styleeq/api/v1.0/frompivots', methods=['POST'])
def frompivots():
    all_sources = request.json["sources"]
    all_features = request.json["features"]
    all_pivots = request.json["pivots"]

    all_outputs = []

    for source, features, pivots in zip(all_sources, all_features, all_pivots):
        batch = []
        for opt in pivots:
            batch.append(
                [
                    {
                        "sequence": features["sequence"], 
                        "controls": opt["controls"],
                        "source_string": opt["original"],
                    }
                ]
            )
        batch = app.PLUM["batcher"]._collate_fn(batch)

        encoder_state, controls_state = app.PLUM["model"].encode(batch)
        search = BeamSearch(beam_size=8, max_steps=100, 
                            vocab=app.PLUM["decoder_vocab"])
        search(app.PLUM['model'].decoder, encoder_state, 
               controls=controls_state)
        outputs = [" ".join(output) for output in search.output()]
        
        all_outputs.append(
            {
                "source": source, 
                "transfers": [{"pivot": p["original"], "transfer": o}
                              for p, o in zip(pivots, outputs)]
            }
        )

    return jsonify({"outputs": all_outputs}), 201

@app.route('/styleeq/api/v1.0/getfeatures', methods=['POST'])
def getfeatures():
    sources = request.json["sources"]
    features = get_features(sources)
    return jsonify({"features": features, "sources": sources}), 201

@app.route('/styleeq/api/v1.0/fromfeatures', methods=['POST'])
def fromfeatures():
    sources = request.json["sources"]
    features = request.json["features"]
    flens = [len(x["sequence"]["tokens sensored"]) for x in features]
    batch = [[f] for f in features] 
    batch = app.PLUM["batcher"]._collate_fn(batch)
    I = np.argsort(flens)[::-1]

    encoder_state, controls_state = app.PLUM["model"].encode(batch)
    search = BeamSearch(beam_size=8, max_steps=100, 
                        vocab=app.PLUM["decoder_vocab"])
    search(app.PLUM['model'].decoder, encoder_state, 
           controls=controls_state)
    outputs = [" ".join(output) for output in search.output()]

    return jsonify({"outputs": [{"source": src, "transfer": outputs[i]}    
                                for src, i in zip(sources, I)]}), 201


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "StyeEQ server. Transfer the literary style of sentences.\n"
        "       Wow your friends! Astound your boss! Fun for all ages!")
    parser.add_argument("--corenlp", type=int, default=9000,
                        help="Port for corenlp directory.")
    parser.add_argument("--model", type=Path, 
                        help="Path to model directory")
    parser.add_argument("--data", type=Path, 
                        help="Path to data directory")
    args = parser.parse_args()

    print("loading model...", end="", flush=True)
    model = load_model(args.model)
    print(" OK!")

    batcher, decoder_vocab, db = load_batcher(args.model, args.data)
    app.PLUM = {"model": model, "batcher": batcher, 
                "decoder_vocab": decoder_vocab, "db": db}

    app.run(host="0.0.0.0", debug=False)
