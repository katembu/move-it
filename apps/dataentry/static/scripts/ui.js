
/* setup environment */
$(document).ready( function() {
    // setup variables
    SMSes = {};
    current = 0;
    gen_table(current);

    // set identity from cookie if exists
    var identity = readCookie('dataentry_identity');
    if (identity && identity.length > 0) {

        if (decodeURIComponent)
            identity = decodeURIComponent(identity);

        $('#phone').val(identity);

    }

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

    // store identity in a cookie
    if (encodeURIComponent)
        identity = encodeURIComponent(identity);

    createCookie('dataentry_identity', identity);

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

/* sorts an array of nodes with order attribute */
function sortNodes(a, b)
{
    try { ao = a.getAttribute('order'); } catch(e) { ao = 0; }
    try { bo = b.getAttribute('order'); } catch(e) { bo = 0; }
    return bo - ao;
}

/* get_message callback: copy message info into the Inbox table */
function on_proxy_get(data)
{
    if (data && data.text) {
        var status = data.status || 'unknown';
        var text = data.text || "";

        // get the tbody
        var doc = document.getElementById('log');

        // create new element for the row
        var new_tr = document.createElement('tr');
        new_tr.setAttribute('order', current);
        new_tr.className = 'out';
        var status_td = document.createElement('td');
        status_td.className = 'status';
        status_td.innerHTML = '<img src="/static/childcount/icons/' + status.toLowerCase() + '.png" />';
        var msg_td = document.createElement('td');
        msg_td.className = 'msg';
        msg_td.innerHTML = text;
        new_tr.appendChild(status_td);
        new_tr.appendChild(msg_td);

        // add new row at end of list
        doc.appendChild(new_tr);

        // retrieve all rows and sort by order attribute
        var trs = doc.getElementsByTagName('tr');
        nodesA = [];
        for (var i=0;i<trs.length;i++) {
            nodesA.push(trs[i]);
        }
        var sorted_nodes = nodesA.sort(sortNodes);

        // remove all trs from tbody
        while (doc.firstChild) {
              doc.removeChild(doc.firstChild);
        }

        // add all tr from sorted list
        for (var i=0;i<sorted_nodes.length;i++) {
            doc.appendChild(sorted_nodes[i]);
        }
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

/* generic function to record a cookie */
function createCookie(name,value,days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
}

/* generic function to read a cookie */
function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

/* generic function to delete a cookie */
function eraseCookie(name) {
	createCookie(name,"",-1);
}

