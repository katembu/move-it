
/* setup environment */
$(document).ready( function() {
    // setup variables
    SMSes = {};
    current = 0;
    gen_table(current);

    // give message box the focus
    focus_entry();

    // setup form action
    $('#form').submit( function() { try { send_message(); } catch(e) {} return false; });

    // start message query loop
    setInterval("get_message()", 5000);
});

/* sends the current message to the proxy for processing */
function send_message()
{
    var identity = $('#phone').val();
    var text =  $('#message').val();

    if (identity.length == 0) {
        alert("You must set your Identity to be able to send messages.\nPlease fill the Identity box and retry.");
        return false;
    }

    if (text.length == 0) {
        alert("You can't send empty messages!\nPlease write something and retry.");
        return false;   
    }

    data = {'identity': identity, 'message': text};
    res = proxy_send(data, on_proxy_send);
}

/* send_message callback: copy message text to history and create a new row in Sent table */
function on_proxy_send(data)
{
    if (data) {
        // store msg in row
        SMSes[current] = {'message': $('#message').val()}

        // create new row
        current = parseInt(current) + 1;
        gen_table(current);

        // scroll to new row
        $('#ccform_body').scrollTo('#sms_' + current, 1);

        // empty entry input
		$('#message').val("");

        // return focus to text box
        focus_entry();
    }
}

/* calls the proxy for new message */
function get_message()
{
    var identity = $('#phone').val();

    if (identity.length == 0) {
        return false;
    }
    data = proxy_get(identity, on_proxy_get);
}

/* get_message callback: copy message info into the Inbox table */
function on_proxy_get(data)
{
    if (data && data.text) {
        var status = data.status || 'unknown';
        var text = data.text || "";

	    snippet = '<tr class="out"><td class="status"><img src="/static/childcount/icons/' + status.toLowerCase() + '.png" /></td><td class="msg">' + text + '</td></tr>';
        doc = document.getElementById('log');
	    doc.innerHTML = snippet += doc.innerHTML;

	    $('div.tester').scrollTo('#log tr:last', 800);
    }
}

/* generates a new empty row in Sent Messages */
function gen_table(id)
{
    var snippet = '<tr id="sms_' + id + '">';
    snippet += '<td id="td_' + id + '" class="f" title="message"></td>';
    snippet += '<td id="duplicate_' + id + '" title="Duplicate SMS"><img class="duplicate" src="/static/childcount/icons/copy.png" onclick="duplicate_sms(' + id + ');" /></td></tr>';
    $('#ccform_body').append(snippet);
}

/* replicates message box content into the Sent Message table row */
function parse_message()
{
    var doc = document.getElementById('td_'+current);
    var text = $('#message').val();
    doc.innerHTML = text;
}

/* copy a previously entered message from the Sent table to message box */
function duplicate_sms(id)
{
    $('#message').val(SMSes[id].message);
    parse_message();
    focus_entry();
}

/* gives message box the focus */
function focus_entry()
{
    $('#message').focus();
}
