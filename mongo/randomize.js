mapRandom = function () {
    emit(this.uri, {type: this.type, random: Math.random()});
}

reduceNop = function (key, values) {
    return values[0];
}

db.nodes.mapReduce(mapRandom, reduceNop, {out: {merge: 'randomNodes'}});

