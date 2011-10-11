db.nodes.ensureIndex({uri: 1});
db.edges.ensureIndex({key: 1});
db.edges.ensureIndex({start: 1, type: 1});
db.edges.ensureIndex({end: 1, type: 1});
