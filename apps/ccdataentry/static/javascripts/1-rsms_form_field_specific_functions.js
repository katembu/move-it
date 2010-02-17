/*--	Hashes in this file are used to process the JSON forms and turn them into
----	nice, clickable tables.
----
----	RsmsFormFieldLogic -- defines functions that return:
----       -FieldName-          -Arguments-        -Returns-
----		* inputField . . . . () . . . . . . . . .the input field of an item
----		* defaultShow. . . . () . . . . . . . . .the default value shown in the column's box
----		* editable . . . . . () . . . . . . . . .
----		* observers. . . . . () . . . . . . . . .an array of strings for which observers should be set
----												  ex. ['click', 'blur']
----		* showValue. . . . . (processed Value). .the string (or element) that is entered into the <TD />
----		* processValue . . . (input value)  . . .the string that should eventually represent that value in the sms
----
----
--*/

function GetRsmsFieldLogic(str) { return $H(RsmsFormFieldLogic['_default']).merge($H(RsmsFormFieldLogic[str] || RsmsFormFieldLogic['plain'])).toObject(); }



var RsmsFormFieldLogic={
	plain: {
		inputField: function(){
			return new Element('div', {title: 'Field Logic Entry must exist in rsms_field_processing.js'}).update(this.col.qtype).setStyle('color:red');
		}
	},
	letter: {
		editable: function(){return false},
		defaultShow: function() {return "+"+this.column.letters;}
	},
	yesNoUnknown: {
		inputField: function() {
			this.inputs.selectField = new Element('select', {style: 'font-size: 20px'});
			this.inputs.selectField.insert(new Element('option').update(""));
			this.inputs.selectField.insert(new Element('option', {value: 'Y'}).update("Y"));
			this.inputs.selectField.insert(new Element('option', {value: 'N'}).update("N"));
			this.inputs.selectField.insert(new Element('option', {value: 'U'}).update("?"));
			return this.inputs.selectField;
		}
	},
	mvpid: {
		inputField: function() {
			this.inputs.mvpid = new Element('input', {size: '6', type: 'text'});
			return this.inputs.mvpid;
		}
	},
	text: {
		inputField: function() {
			this.inputs.text = new Element('input', {size: '6', type: 'text'});
			return this.inputs.text;
		}
	},
	fullDate: {
		inputField: function() {
			this.inputs.dateField = new Element('input', {maxlength: '6', type: 'text', style: 'width: 45px;'})
			return this.inputs.dateField;
		},
		editable: function(){return true}
	},
	selectMany: {
		inputField: function() {
			this.inputs.selectField = new Element('select', {multiple: 'multiple'});
			this.column.choices.each(function(cz) {
				this.insert(new Element('option', {value: cz}).update(cz));
			}, this.inputs.selectField)
			return this.inputs.selectField
		},
		observers: $w('blur'),
		showValue: function(val){
			return $A(val).flatten().map(function(qz){return "<span>"+qz+"</span>"}).join(' ')
		}
	},
	splitWords: {
		inputField: function() {
			this.inputs.wordsField=new Element('input', {type: 'text', style: 'width: 33px'});
			return this.inputs.wordsField
		}
	},
	selectOne: {
		inputField: function() {
			var _selectOneField=new Element('select')
			this.column.choices.each(function(zfl){
				_selectOneField.insert(new Element('option').update(zfl));
			}.bind(this));
			return _selectOneField;
		},
		showValue: function(q) {
			return $A(q).first().toUpperCase()
		}
	},
	singleDigit: {
		observers: $w('blur'),
		blur: function() {},
		inputField: function() {
			this.inputs.selectOneField=new Element('select')
			$R(0,9).toArray().each(function(zfl){
				this.inputs.selectOneField.insert(new Element('option').update(zfl));
			}.bind(this));
			return this.inputs.selectOneField;
		}
	},
	_default: {
		editable: function(){return true},
		onCreate: function(orig) {
		},
		inputField: function() {
			return new Element('div').update('cool');
		},
		defaultShow: function() {
			return "__"
		},
		observers: $w('blur change'),
		focus: function(evt) {},
		blur: function(evt) {},
		change: function(evt) {},
		processValue: function(inp) {
			return inp;
		},
		showValue: function(val) {
			return val;
		}
	}
};
