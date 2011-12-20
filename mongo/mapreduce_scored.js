mapNodeScores = function () {
    // take in a justification entry
    var node = db.nodes.findOne({'uri': this._id});
    // add the score, plus some jitter for uniqueness
    node.jitter = Math.random() * .000001;
    node.score = this.value + node.jitter;
    emit(this._id, node);
};

mapEdgeScores = function () {
    var scored1 = db.justification.findOne({'_id': this.start});
    var scored2 = db.justification.findOne({'_id': this.end});
    this.jitter = Math.random() * 0.001;
    var score1 = this.jitter;
    var score2 = this.jitter;
    if (scored1) score1 += scored1.value;
    if (scored2) score2 += scored2.value;

    var scoreCodeIn = toScoreCode(score1);
    var scoreCodeOut = toScoreCode(score2);
    var codeAout = 'Aout ' + this.start + ' ' + scoreCodeOut + ' ' + this.end;
    var codeAin = 'Ain ' + this.end + ' ' + scoreCodeIn + ' ' + this.start;
    var codeBout = 'Bout ' + this.type + ' ' + this.start + ' ' + scoreCodeOut + ' ' + this.end;
    var codeBin = 'Bin ' + this.type + ' ' + this.end + ' ' + scoreCodeIn + ' ' + this.start;

    emit(codeAout, this);
    emit(codeAin, this);
    emit(codeBout, this);
    emit(codeBin, this);
};

reduceNop = function (key, values) {
    return values[0];
};

//db.justification.mapReduce(mapNodeScores, reduceNop, {out: 'scoredNodes'});
db.edges.mapReduce(mapEdgeScores, reduceNop, {out: 'scoredEdges'});
db.scoredEdges.ensureIndex({'value.start': 1, 'value.type': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.end': 1, 'value.type': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.start': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.end': 1, 'value.score': 1})

