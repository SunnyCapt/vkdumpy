var result = [];
var offset = '{{OFFSET}}';
var start_message_id = '{{START_MESSAGE_ID}}';
var kwargs = '{{KWARGS}}';

kwargs.count = 200;
kwargs.offset = offset;
kwargs.v = '5.120';

var history = API.messages.getHistory(kwargs);
result = result + history.items;

var i = 1;
while (i < 25 && (offset + result.length) < history.count && result[result.length - 1].id > start_message_id) {
    kwargs.offset = offset + result.length;
    history = API.messages.getHistory(kwargs);
    result = result + history.items;
    i = i + 1;
}

return {'count': history.count, 'items': result};
