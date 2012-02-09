reduceNop = function (key, values) {
    return values[0];
}

mapEdges = function () {
    if (this.weight) {
        emit(this.start, {type: this.type, end: this.end, weight: this.weight})
    }
}

mapNodes = function () {
      emit(this._id, {type: 'NODE', end: 'NODE', weight: this.value});
}

reduceNode = function (key, values) {
    if (key.substring(0, 12) === '/conjunction') {
      var invWeight = 0.0;
      for (var i=0; i<values.length; i++) {
        if (values[i] === 0) return 0;
        invWeight += 1/values[i];
      }
      return 1/invWeight;
    } else {
      return Array.sum(values);
    }
}

mapActivation = function () {
    if (this.value.type === 'NODE') {
        db.cachedValue = this.value.weight;
    }
    else if (this.weight) {
        if (this.value.start === this.value.end && this.value.start !== "/") {
            return;
        }
        emit(this.value.end, db.cachedValue * this.value.weight);
    }
}

db.nodeScores.save({_id: '/', value: 1});
db.edges.mapReduce(mapEdges, reduceNop, {out: {replace: 'mrEdges', sharded: true}});
db.nodeScores.mapReduce(mapNodes, reduceNop, {out: {merge: 'mrEdges', sharded: true}});

db.edges.mapReduce(mapActivation, reduceNode, {out: {merge: 'nodeScores', sharded: true}});

//db.nodeScores.save({_id: '/', value: 1});
//db.edges.mapReduce(mapActivation, reduceNode, {out: {merge: 'nodeScores'}});
