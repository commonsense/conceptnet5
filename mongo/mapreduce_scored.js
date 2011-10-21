
mapNodeScores = function () {
    // take in a justification entry
    var node = db.nodes.findOne({'uri': this._id});
    // add the score, plus some jitter for uniqueness
    node.jitter = Math.random() * .000001;
    node.score = this.value + node.jitter;
    emit(this._id, node);
}

mapEdgeScores = function () {
    var scored1 = db.justification.findOne({'_id': this.start});
    var scored2 = db.justification.findOne({'_id': this.end});
    this.jitter = Math.random() * .000001;
    var score = 1+this.jitter;
    if (scored1) score *= scored1.value; else score *= 0.001;
    if (scored2) score *= scored2.value; else score *= 0.001;
    this.score = score;
    emit(this._id, this);
}

reduceNop = function (key, values) {
    return values[0];
}


//db.justification.mapReduce(mapNodeScores, reduceNop, {out: 'scoredNodes'});
db.edges.mapReduce(mapEdgeScores, reduceNop, {out: 'scoredEdges'});
db.scoredEdges.ensureIndex({'value.start': 1, 'value.type': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.end': 1, 'value.type': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.start': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.end': 1, 'value.score': 1})

