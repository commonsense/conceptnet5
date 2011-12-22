mapEdgeScores = function () {
    var scored1 = db.nodeScores.findOne({'_id': this.start});
    var scored2 = db.nodeScores.findOne({'_id': this.end});

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

db.edges.mapReduce(mapEdgeScores, reduceNop, {out: 'edgeScores'});

