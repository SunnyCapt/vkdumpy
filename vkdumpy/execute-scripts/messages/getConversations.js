var result = [];
var extended = '{{EXTENDED}}';
var apiVersion = '{{API_VERSION}}';
var conversations = API.messages.getConversations('{{KWARGS}}');

var j = 0;
while (j < conversations.items.length) {
    if (extended)
        result.push(conversations.items[j]);
    else
        result.push(conversations.items[j].conversation.peer.id);
    j = j + 1;
}

var i = 1;
while (i < 25 && result.length < conversations.count) {
    conversations = API.messages.getConversations({'v': apiVersion, 'offset': result.length, 'count': 200});
    j = 0;
    while (j < conversations.items.length) {
        if (extended)
            result.push(conversations.items[j]);
        else
            result.push(conversations.items[j].conversation.peer.id);
        j = j + 1;
    }
    i = i + 1;
}

return {'count': conversations.count, 'items': result};
