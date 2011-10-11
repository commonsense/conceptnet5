// initiaize your "justification" table with {_id: '/', value: 1}
// make sure '/' has an edge to itself of weight 1

mapConjunctEdges = function () {
    if (this.type === 'conjunct') {
        var startEntry = db.justification.findOne({_id: this.start});
        var endEntry = db.conjunctions.findOne({_id: this.end});
        if (startEntry && endEntry && endEntry.value && startEntry.value > 0) {
            var weight = endEntry.value / startEntry.value;
            emit(this.key, {
                start: this.start,
                end: this.end,
                weight: weight,
                type: this.type
            })
        }
    }
}

reduceNop = function (key, values) {
    return values[0];
}

mapOtherEdges = function () {
    if (this.weight && this.type !== 'conjunct') {
        emit(this.key, {
            start: this.start,
            end: this.end,
            weight: this.weight,
            type: this.type
        })
    }
}   

reduceSum = function (key, values) {
    return Array.sum(values);
}

mapActivation = function () {
    var val = this.value;
    if (val.weight) {
        if (val.start === val.end && val.start !== "/") {
            return;
        }
        var entry = db.justification.findOne({_id: val.start});
        if (entry && entry.value) {
            emit(val.end, entry.value * val.weight);
        }
    }
}

mapConjunctActivation = function () {
    if (this.type === 'conjunct') {
        var entry = db.justification.findOne({_id: this.start});
        if (entry && entry.value) {
            emit(this.end, entry.value);
        }
    }
}


reduceParallel = function (key, values) {
    var invWeight = 0.0;
    for (var i=0; i<values.length; i++) {
        invWeight += 1/values[i];
    }
    return 1/invWeight;
}

db.justification.insert({_id: '/', value: 1});
db.edgeWeights.insert({_id: 'justifies / /', value: {start: '/', end: '/', type: 'justifies', weight: 1}});

db.edges.mapReduce(mapConjunctEdges, reduceNop, {out: {merge: 'edgeWeights'}, query: {type: 'conjunct'}});
db.edges.mapReduce(mapOtherEdges, reduceNop, {out: {merge: 'edgeWeights'}});
db.edgeWeights.mapReduce(mapActivation, reduceSum, {out: 'justification'});
db.edgeWeights.mapReduce(mapActivation, reduceSum, {out: 'justification'});
db.edges.mapReduce(mapConjunctActivation, reduceParallel, {out: 'conjunctions'});

db.edges.mapReduce(mapConjunctEdges, reduceNop, {out: {merge: 'edgeWeights'}, query: {type: 'conjunct'}});
db.edges.mapReduce(mapOtherEdges, reduceNop, {out: {merge: 'edgeWeights'}});
db.edgeWeights.mapReduce(mapActivation, reduceSum, {out: 'justification'});
db.edgeWeights.mapReduce(mapActivation, reduceSum, {out: 'justification'});
db.edges.mapReduce(mapConjunctActivation, reduceParallel, {out: 'conjunctions'});

