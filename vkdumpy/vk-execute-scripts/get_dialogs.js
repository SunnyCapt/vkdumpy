var apiVersion = '{{API_VERSION}}';
var result = [];
var peers = API.messages.getDialogs('{{ARGS}}');

var j = 0;
while (j < peers.items.length) {
    result.push(peers.items[j]);
    j = j + 1;
}
var i = 1;

while (i < 24 && 200 * i < peers.count) {
    peers = API.messages.getDialogs({'v': apiVersion, 'offset': i * 200, 'count': 200});
    j = 0;
    while (j < peers.items.length) {
        result.push(peers.items[j]);
        j = j + 1;
    }
    i = i + 1;
}

return {'count': peers['count'], 'items': result};
