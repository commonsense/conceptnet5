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
}

reduceNop = function (key, values) {
    return values[0];
}

// This is based on MIT-licensed code by Joshua Bell:
//
// Convert a JavaScript number to IEEE-754 Double Precision
// value represented as an array of 8 bytes (octets)
//
// http://cautionsingularityahead.blogspot.com/2010/04/javascript-and-ieee754-redux.html

function toIEEE754(v, ebits, fbits) {

    var bias = (1 << (ebits - 1)) - 1;

    // Compute sign, exponent, fraction
    var s, e, f;
    if (isNaN(v)) {
        e = (1 << bias) - 1; f = 1; s = 0;
    }
    else if (v === Infinity || v === -Infinity) {
        e = (1 << bias) - 1; f = 0; s = (v < 0) ? 1 : 0;
    }
    else if (v === 0) {
        e = 0; f = 0; s = (1 / v === -Infinity) ? 1 : 0;
    }
    else {
        s = v < 0;
        v = Math.abs(v);

        if (v >= Math.pow(2, 1 - bias)) {
            var ln = Math.min(Math.floor(Math.log(v) / Math.LN2), bias);
            e = ln + bias;
            f = v * Math.pow(2, fbits - ln) - Math.pow(2, fbits);
        }
        else {
            e = 0;
            f = v / Math.pow(2, 1 - bias - fbits);
        }
    }
     
    // Pack sign, exponent, fraction
    var i, bits = [];
    for (i = fbits; i; i -= 1) { bits.push(f % 2 ? 1 : 0); f = Math.floor(f / 2); }
    for (i = ebits; i; i -= 1) { bits.push(e % 2 ? 1 : 0); e = Math.floor(e / 2); }
    bits.push(s ? 1 : 0);
    bits.reverse();
    var str = bits.join('');
     
    // Bits to bytes
    var bytes = [];
    while (str.length) {
        bytes.push(parseInt(str.substring(0, 8), 2));
        str = str.substring(8);
    }
    return bytes;
}

function fromIEEE754(bytes, ebits, fbits) {

    // Bytes to bits
    var bits = [];
    for (var i = bytes.length; i; i -= 1) {
        var byte = bytes[i - 1];
        for (var j = 8; j; j -= 1) {
            bits.push(byte % 2 ? 1 : 0); byte = byte >> 1;
        }
    }
    bits.reverse();
    var str = bits.join('');
   
    // Unpack sign, exponent, fraction
    var bias = (1 << (ebits - 1)) - 1;
    var s = parseInt(str.substring(0, 1), 2) ? -1 : 1;
    var e = parseInt(str.substring(1, 1 + ebits), 2);
    var f = parseInt(str.substring(1 + ebits), 2);
     
    // Produce number
    if (e === (1 << ebits) - 1) {
        return f !== 0 ? NaN : s * Infinity;
    }
    else if (e > 0) {
        return s * Math.pow(2, e - bias) * (1 + f / Math.pow(2, fbits));
    }
    else if (f !== 0) {
        return s * Math.pow(2, -(bias-1)) * (f / Math.pow(2, fbits));
    }
    else {
        return s * 0;
    }
}

function fromIEEE754Single(b) { return fromIEEE754(b,  8, 23); }
function   toIEEE754Single(v) { return   toIEEE754(v,  8, 23); }

// The functions below were added by Rob.

function toScoreCode(v) {
  var ieee = toIEEE754Single(Math.max(v, 0));
  var bytes = [];
  for (var i=0; i<4; i++) {
    bytes.push((255 - ieee[i]).toString(16));
  }
  return bytes.join('');
}

function fromScoreCode(h) {
  var bytes = [];
  for (var i=0; i<4; i++) {
    var hex = h.substring(i*2, i*2+2);
    bytes.push(255 - parseInt(hex, 16));
  }
  return fromIEEE754Single(bytes);
}

//db.justification.mapReduce(mapNodeScores, reduceNop, {out: 'scoredNodes'});
db.edges.mapReduce(mapEdgeScores, reduceNop, {out: 'scoredEdges'});
db.scoredEdges.ensureIndex({'value.start': 1, 'value.type': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.end': 1, 'value.type': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.start': 1, 'value.score': 1})
db.scoredEdges.ensureIndex({'value.end': 1, 'value.score': 1})

