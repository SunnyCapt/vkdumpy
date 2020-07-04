var result = [];
var apiVersion = '{{API_VERSION}}';
var conversations = API.messages.getConversations('{{KWARGS}}');

var j = 0;
while (j < conversations.items.length) {
    result.push(conversations.items[j]);
    j = j + 1;
}

var i = 1;
while (i < 24 && result.length < conversations.count) {
    conversations = API.messages.getConversations({'v': apiVersion, 'offset': result.length, 'count': 200});
    j = 0;
    while (j < conversations.items.length) {
        result.push(conversations.items[j]);
        j = j + 1;
    }
    i = i + 1;
}

return {'count': conversations['count'], 'items': result};
