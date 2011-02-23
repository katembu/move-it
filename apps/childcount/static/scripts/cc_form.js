SMSes = {};

ChildCountFormSection = function (id, name, title)
{
    this.id = id;
    this.name = name;
    this.title = title;
    this.fields = [];

    this.displayName = function () { return "+" + this.name; }
    this.addField = function (field) { this.fields.push(field); }
    this.toString = function () { return this.displayName(); }
}

ChildCountFormField = function (id, name, title)
{
    this.id = id;
    this.name = name;
    this.title = title;

    this.displayName = function () { return this.name; }        
    this.toString = function () { return this.displayName(); }        
}

function ChildCountForm (name)
{

    var ds = new ChildCountFormSection('date_entered','date','date');
    ds.addField(new ChildCountFormField('date_entered', date_name, date_title));

    this.name = name;
    this.sections = [ds];

    this.id = this.name.replace(/\s+/, '_');

    this.displayName = function (section) { return this.name; }

    this.addSection = function (section)
    {
        this.sections.push(section);
    }

    this.getSection = function (section_id)
    {
        for (var i in this.sections) {
            if (this.sections[i].id == section_id)
                return this.sections[i];
        }
        return null;
    }

    this.getSectionByName = function (section_name)
    {
        for (var i in this.sections) {
            if (this.sections[i].name.toUpperCase() == section_name.toUpperCase())
                return this.sections[i];
        }
        return null;
    }
}

/*
 * Generates History Log
 * table rows ; including header one.
 *
 */
function gen_table(id)
{
    var snippet = '<tr id="sms_' + id + '">';
    for (var i in dataentry_form.sections) {
        var section = dataentry_form.sections[i];

        if (section.id != 'root' && section.id != 'date_entered')
            snippet += '<td id="' + section.id + '" class="s" title="' + section.title + '">' + section.displayName() + '</td>';
        
        for (var j in section.fields) {
            var field = section.fields[j];
            // header only add text
            var fname = (id == 0) ? field.displayName() : '';

            snippet += '<td id="' + build_id_for(section, field, id) + '" class="f" title="' + field.title + '">' + fname + '</td>';
        }
    }
    snippet += '<td id="duplicate_' + id + '" title="Duplicate SMS"><img class="duplicate" src="/static/childcount/icons/copy.png" onclick="duplicate_sms(' + id + ');" /></td></tr>';
    if (id == 0)
        $('#ccform_head').append(snippet);
    else
        $('#ccform_body').append(snippet);
}

// returns ID string for fields
function build_id_for(section, field, id)
{
    if (id == null)
        id = current;
    return section.id + '_' + field.id + '_' + id;
}


/*
 * Parse input text
 * copy values into table
 */
function parse_message()
{
    // reset fields
    var doc = document.getElementById('sms_'+current);
    tds = doc.getElementsByTagName('td');
    for (var i in tds)
    {
        var td = tds[i];
        if (td['id'] != 'duplicate_'+current && td.className != 's') {
            tds[i].innerHTML = '';
        }
    }

    // original message
    var text = $('#message').val();

    // replacing multiple space with single one
    var str = text.replace(/(\s+)/, ' ');

    // splitting on + to get all forms.
    var tforms = str.split(/\+/);

    // Get the stuff before the first +
    var start = tforms.shift();
    // Before the first +, we should have "DATE ROOT_MSG"
    var start_parts = start.split(/\s+/);
    var edate = start_parts.shift();
    start_parts = start_parts.join(' ');

    var forms = [];
    forms.push(edate);
    forms = forms.concat(start_parts);
    forms = forms.concat(tforms);

    //clog = console.log;
    clog("All forms: " + forms);

    for (var i in forms)
    {
        var appendToLast = false;

        // retrieve text part
        var section_content = forms[i].trim();
        clog("form-like: --"+section_content+"--");

        // split args/form
        var args = section_content.split(/\s+/);

        // first one is encounter date and health id
        if (i == 0) {
            var csection = dataentry_form.getSection('date_entered');
        } else if (i == 1) {
            var csection = dataentry_form.getSection('root');
        } else {
            var section_name = args[0];
            var csection = dataentry_form.getSectionByName(section_name);
            if (csection == null) {
                var csection = dataentry_form.getSection('root');
                appendToLast = true;
            }
        }

        clog(csection.displayName());

        // store max number of fields for section
        var max_args = csection.fields.length;
        clog("max: "+max_args);

        clog("args: " + args + ' : '+args.length);
        // remove command from args list
        // except for UUID
        if (i > 1)
            args = args.slice(1);            
        clog("args: " + args + ' : '+args.length);

        for (var j in args)
        {
            // retrieve field definition
            var content = args[j];
            var cfield = csection.fields[j];

            clog(csection + ' entry: ' + content);

            // if args contains more than max_args
            // append latest to last field
            if (j > csection.fields.length - 1)
            {
                cfield = csection.fields[max_args -1];
                var doc = document.getElementById(build_id_for(csection, cfield));
                doc.innerHTML += ' ' + content;
            // otherwise, set as field content
            } else if (appendToLast) {
                cfield = csection.fields[max_args -1];
                var doc = document.getElementById(build_id_for(csection, cfield));
                doc.innerHTML += ' +' + section_name + ' ' +content;
            } else {
                var doc = document.getElementById(build_id_for(csection, cfield));
                doc.innerHTML = content;
            }
        }
    }
}
