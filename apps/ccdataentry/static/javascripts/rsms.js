//BEGIN RSMS_TEMPLATE_CLASS JS

/*--	TColumn () ==> Table Column
----		is a prototype.js class that stores the template for form columns and it links to view and logic functions
--*/

var TColumns={};
var TColumn = Class.create({
	initialize: function(arr, priority, parent) {
		this.id			=	arr[0];
		var opts		=	arr[1];
		
		this.setTcolumn();
		
		this.title		=	opts.title;
		this.priority	=	priority || -1;
		this.letters		=	String(opts.letter || opts.letters).toUpperCase();
		this._subCategories	=	opts.subCategories;
		if(this._subCategories) {this.processSubcategories()}
		this.spec		=	opts.spec;
		this.colgroup	=	opts.colgroup || 'main';
		this.parentCol	=	parent;
		this.advice		=	opts.advice;
		this.choices	=	opts.choices || opts.options || $A();
		this.qtype		=	opts.qtype || 'plain';
		this.vtype		=	opts.vtype || opts.qtype;
		
		if(opts.options) this.choices=opts.options.split(' ');

		this.view = $H(TCViews._default).merge($H(TCViews[this.qtype])).toObject();
		this.logic = this.view;
	},
	processSubcategories: function() {
		this.subCategories = $A(this._subCategories).map(function(scd, priority){
			var _tscd=[this.id+RsmsGlobals.nameDivider+scd[0], scd[1]]
			return new TColumn(_tscd, priority+1, this)
		}.bind(this))
	},
	toHash: function() {
		return this.toArray().inject($H(), function(kz, az){
			kz.set(az.id, az)
			return kz;
		})
	},
	toArray: function() {
		return $A([
			this,
			this.subCategories
			]).flatten().compact();
	},
	setTcolumn: function() {
		if(typeof(TColumns[this.id])=='undefined') { TColumns[this.id]=this;
		} else {
			cerr("Overriding a column with id: "+this.id);
			TColumns[this.id]=this;
		}
	}
});
//END RSMS_FIELD_TEMPLATE_CLASS JS

//BEGIN RSMS FORM_TEMPLATE CLASS
/*--	RsmsForms object stores template information about each form.
----	It does not create the table.
----	The table is created by a "Sheet" object (see "table_views.js")
--*/

var RsmsForms={};
var RsmsForm=Class.create({
	initialize: function(arr){
		this.id				=	arr[0];
		var opts			=	arr[1];
		
		if(typeof(RsmsForms[this.id])!=='undefined') { throw("Overriding Form Definition : "+this.id) }
		RsmsForms[this.id]	=	this

		this.title			=	opts.title;
		this.optgroup		=	opts.optgroup;
		this.date			=	opts.date;
//		this.tview			=	opts.tview || 'standard'; //preferred set of rendering functions
		this.fieldRefs		=	$w(opts.fields);

		this.processFields		(this.fieldRefs);

		this.sheets			=	$A();
	},
	processFields: function(flds) {
		var _fields=flds.map(function(fldStr){ return TColumns[fldStr] }).compact();
		this.fieldGroups = _fields.inject($H(), function(zt, ab){
			zt.set(ab.id, ab.toArray());
			return zt;
		});
		this.fieldGroupIds = this.fieldGroups.keys();
		this.fields = this.fieldGroups.toArray().map(function(qzar){return qzar[1]})
		this.fieldIds = this.fieldGroups.toArray().map(function(qzar){return qzar[1].map(function(qew){return qew.id})})
	},
	newSheet: function(opts) {
		var _ts = NewSheet(this);
		this.sheets.push(_ts);
		return _ts;
	}
})


var SheetFns={
	create: function(formDef, opts) {
		return new TViewSheet(formDef, opts);
	},
	retrieve : function(str) {
		return RsmsGlobals.sheets[str] || false;
	}
}
var NewSheet = SheetFns.create;
var GetSheet = SheetFns.retrieve;
//END RSMS_FIELD_TEMPLATE_CLASS JS

//BEGIN RSMS_CREATION_CLASS JS
/*--	TViewSheet ==> Table View Sheet
----         This is the instance of the form that creates the table, handles input, and interfaces with sms class
--*/

var TableEffects = {
	fade: function(opts){ return new Effect.Fade(this._elem, opts) }
}

var TViewSheet = Class.create({
	initialize: function(frmSrc, _opts) {
		var opts		=	_opts || {};
		this.frm		=	frmSrc;
		this.id			=	opts.id || RsmsGlobals.newSheetId();
		this.register();
		
		this.smsRows	=	$A();
		this._elem		=	false;
		this.editable	=	opts.editable || true;
		this.editRowFields=$A();
		
		this.fadeEffect	=	TableEffects.fade.bind(this);
		
		this.submitted	=	opts.submitted || false;
		this.entries	=	opts.entries || $A();
		this.FIELD_IDS	=	this.frm.fieldIds;
		this.processFields();
	},
	register: function() {if(!RsmsGlobals.sheets){RsmsGlobals.sheets={}};RsmsGlobals.sheets[this.id]=this;},
	processFields: function(){
		if(this.FIELD_IDS.flatten()==this.FIELD_IDS) {
			this.groupsExist = false;
		} else {
			this.groupsExist = true;
		}
		this.groupIds=$A();
		this.fields = this.FIELD_IDS.map(function(fid){  // Collects both groupIds and fields
			var _group = $A(fid).flatten();
			var _groupId = _group.first()
			
			this.push(_groupId);
			return _group.map(function(fld){
				return {id: fld, groupId: String(this), ef: false}}, _groupId)
		}, this.groupIds).flatten()
	},
	addRow: function(hsh) {
		var smsHsh = $H(hsh);
		var _newRow=new Element('tr');
		this.aboveRow.insert({before: _newRow});

		this.fields.inject(_newRow, function(ttr, fld){
			var _ttd=new Element('td');
			if(smsHsh.keys().include(fld.id)) {
				_ttd.insert(smsHsh.get(fld.id))
			}
			return ttr.insert(_ttd);
		}.bind(this))
		return hsh;
	},
	addEntryField: function(fld, opts){
		cerr('entry field needed');
	},
	isAView: function(){return true;},
	elem: function() {
		if(!this._elem) { this.generateTable() }
		EntrySwitcher.activeSheet =this;
		return this._elem;
	},
	generateTable: function() {
		this.fields = this.fields.inject($A(), this.ensureTentry, this);

		this.headRow = this.fields.inject(new Element('tr', {className: 'headRow'}), this.injectors.headRow);
		this.aboveRow = this.fields.inject(new Element('tr', {className: 'adviceRow top'}), this.injectors.filler, "adviceTop");
		this.belowRow = this.fields.inject(new Element('tr', {className: 'adviceRow bottom'}), this.injectors.filler, "adviceBottom");
		this.submitSms = new Element('input', {type:'submit', value: 'new sms', id:'new_sms', style:'position: absolute;right: -75px; top:-32px;'})
		this.submitSms.observe('click', EntrySwitcher.submitSms)
		this.belowRow.childElements().last().down().insert(this.submitSms);
		if(this.editable) {
			this.editRow = this.fields.inject(new Element('tr', {className: 'editButtonRow'}), this.injectors.editRow);
		}
		this._elem = $A([
			this.headRow,
			this.smsRows,
			this.aboveRow,
			(this.editRow || null),
			this.belowRow
			]).flatten().compact().inject(new Element('table', {className: 'rsmsList'}), function(tb, tr){return tb.insert(tr)})
	},
	ensureTentry: function(arr, fld) {
		if(!fld.ef) { var _Tc=$H(TColumns).get(fld.id); fld.ef=new TEntry(this, _Tc, {groupId: fld.groupId, id: fld.id, elms: fld}); fld.col=fld.ef.column; }
		arr.push(fld);
		return arr;
	},
	injectors: {
		filler: function(tr, fld) {
			var _s = String(this)
			fld[_s]=new Element('td').update(new Element('div'));
			return tr.insert(fld[_s])
		},
		headRow: function(tr, fld) {
			fld.rowImage=new Image();
			fld.rowImage.src='images/th_'+fld.id+'.png';
			var _td = new Element('div', {className: 'image-wrap'}).insert(fld.rowImage);
			return tr.insert(new Element('th', {className: fld.col.qtype }).update(_td));
		},
		editRow: function(tr, fld) {
			return tr.insert(fld.ef.editRowTd())
		}
	},
	createTable: function() {
		this.headRow = new Element('tr', {className: 'headRow'});
		this.adviceRow = new Element('tr', {className: 'adviceRow'});
		this.editRow = new Element('tr', {className: 'editButtonRow'});
		this.helpRow =new Element('tr', {className: 'helpRow'});
		var _tTd=this.blankTd();

		this.beforeRowItems().each(function(bri){
			this.headRow.insert(_tTd.clone(true));
			this.adviceRow.insert(_tTd.clone(true));
			this.editRow.insert(_tTd.clone(true));
		}.bind(this));

		this.frm.fields.flatten().each(function(fzl){
//			this.headRow.insert(fzl.view.th.call(this, fzl));
//			this.adviceRow.insert(_tTd.clone(true).insert(new Element('div').insert(new Element('div'))));
//			this.editRow.insert(fzl.view.eh.call(this, fzl));
		}.bind(this))
		
		this.fieldHelp=new Element('div', {className: 'fieldHelp'});
		this.helpRow.insert(new Element('td', {colspan: this.editRow.childElements().length}).insert(this.fieldHelp.wrap('div', {style:'position:relative;height:40px'})));

		this._elem = new Element('table', {class: 'rsmsList'});
		this._elem.insert(this.headRow).insert(this.adviceRow).insert(this.editRow).insert(this.helpRow);
	},
	blankTd: function() {
		return new Element('td');
	},
	beforeRowItems: function() {return $A()}
});


/*--	TEntry ==> Table Sheet Entry
----		this is the lowest level of storage (individual points)
----	
----		Parameters:
----			• Sheet
----			• Column Type
----			• Options (optional)
--*/
var EntrySwitcher = {
	activeEntry: null,
	activeGroup: null,
	activeSheet: null,
	onGuard: false,
	queue: $A(),
	directory: $H(),
	activeChain: $A(),
	submitSms: function(evt) {
		var vals = EntrySwitcher.activeSheet.entries.inject($H(), function(hsh, mm){
			if(mm.processedValue) {
				hsh.set(mm.id, mm.showValue);
			}
			return hsh;
		});
		EntrySwitcher.activeSheet.addRow(vals.toObject())
	},
	reset: function(){ 
		EntrySwitcher.queue=$A()
		},
	next: function() {
		if(EntrySwitcher.activeEntry) {
			
		}
	},
	handleKey: function(evt) {
		return null;
		var ck = evt.ctrlKey;
		switch(evt.keyCode) {
			case 9: //tab pushed

			break;
			case 13: //enter or cr
			
			break;
			case 39: //rt arrow
			
			break;
			case 37: //left arrow
			
			break;
			case 38: //up
			
			break;
		}
	},
	unfocus: function(nm) {
		if(nm==1) {}
	}
}


$(document).observe('keypress', EntrySwitcher.handleKey.bind(EntrySwitcher))
var TEntry = Class.create({
	initialize: function(parSheet, colmn, opts){
		var opts			=	opts || {};
		this.sheet			=	parSheet;
		this.sheet.entries.push(this);
		this.updateElement	=	opts.updateElement;
		this.activateElement=	opts.activateElement;
		this.clickEditElement=	opts.clickEditElement;
		this.groupId		=	opts.groupId;
		this.id				=	opts.id;
		this.elms			=	opts.elms;
		this.registerInDirectory();
		if(this.clickEditElement) {this.clickEditElement.observe('click', this.edit.bind(this))}
		this.column			=	colmn;
		this.qtype			=	colmn.qtype || 'plain';
		this.view			=	GetRsmsFieldLogic(this.qtype);
		this.inputs			=	{};
		this.active			=	false;
		this.processedValue	=	false;
		this.dirty			=	false;
		this.logic			=	GetRsmsFieldLogic(this.qtype);
		this.processEvent	=	this.view.processEvent || 'blur';
		this.editable		=	this.view.editable.call(this);
		this.updateOptions();
	},
	siblings: function() {
		
	},
	registerInDirectory: function() {
		if(!EntrySwitcher.directory.get(this.groupId)) {
			EntrySwitcher.directory.set(this.groupId, $A())
		}
		EntrySwitcher.directory.get(this.groupId).push(this);
	},
	updateOptions: function(){},
	activateGroup: function(grpBool) {
		this.activateElement.addClassName('active');
	},
	activate: function(grp) {
		if(!this.active) {
//			clog("ACTIVATE ME" ,this);
			var _toMakeActive=$A();
			if(this.elms.adviceTop) {
				this.elms.adviceTop.up('tr').select('td.selected').each(function(qz){qz.removeClassName('selected')})
			}
			if(this.elms.adviceBottom) {
				this.elms.adviceBottom.up('tr').select('td.selected').each(function(qz){qz.removeClassName('selected')})
			}
			if(grp) {
				_toMakeActive.push(EntrySwitcher.directory.get(this.groupId))
			} else {
				_toMakeActive.push(this)
			}
			_toMakeActive.flatten().compact().map(function(tma){
				return [ tma.elms.adviceTop, tma.elms.adviceBottom]
			}).flatten().compact().each(function(elm){elm.addClassName('selected')})
			_toMakeActive=$A();
			this.active=true;
			this.setEditMode(true);
		}
	},
	spawn: function() {
		cerr('spawining');
	},
	fieldChanged: function(evt) {
		if(this.updateElement) {
			this.updateElement.update(this.showValue);
		}
	},
	editRowTd: function() {
		this.editTd = new Element('td');
		if(this.editable) {
			var _if = Try.these(function(){
				if(this.view.editable) {
					return this.inputFieldDiv()
				}
			}.bind(this),function(){
				return new Element('input', {value: this.qtype, style: 'width:30px'}).wrap('div', {className:'editField'})
			}.bind(this))
			this.editTd.insert(_if);
		}
		this.updateElement=this.editRowShowField()
		this.editTd.insert(this.updateElement);
		return this.editTd;
	},
	inputFieldDiv: function() {
		this.observeInput	=	this.view.inputField.call(this);
		$A([this.view.observers, "focus"]).flatten().uniq().each(function(ostr){
//			clog(this.observeInput, this.observes[ostr]);
			this.observeInput.observe(ostr, this.observes[ostr].bind(this))
		}.bind(this))
		return this.observeInput.wrap('div', {className: 'editField'});
	},
	observes: {
		focus: function(evt) {
			this.activate()
		},
		blur: function(evt){
			if(this.active) {
				this.observes.customFire.call(this, evt);
			}
		},
		change: function(evt){
			if(this.active) {
				this.observes.customFire.call(this, evt);
			}
		},
		customFire: function(evt) {
			evt.stop();
			var _val=this.observeInput.getValue();
			var _nv=this.view.processValue(_val)
			if(this.processedValue!==_nv) {
				this.setEditMode(false);
				this.showValue=this.view.showValue.call(this, _val)
				this.processedValue=_nv;
				this.fieldChanged();
			}
			this.active=false;
		},
		keypress: function(evt){

		}
	},
	editRowShowField: function() {
		if(this.editable) {
			this.tdEditButton = new Element('a', {className: 'showField', href: '#'}).update(String(this.view.defaultShow.call(this)).interpolate(this));
			this.tdEditButton.observe('click', this.editClick.bind(this));
		} else {
			this.tdEditButton = new Element('div', {className: 'showField'}).update(String(this.view.defaultShow.call(this)).interpolate(this));
		}
		return this.tdEditButton;
	},
	editClick: function() {
		if(!this.inEditMode()) {
			this.activate(true);
		}
		Try.these(function(){
//			this.
		}.bind(this))
	},
	setEditMode: function(tf) {
		if(!tf) {
			this.editTd.removeClassName('edit');
		} else {
			this.editTd.addClassName('edit');
		}
	},
	inEditMode: function() {
		return this.editTd.hasClassName('edit');
	}
});
//EMD RSMS_CREATION_CLASS JS


//BEGIN RSMS FIELD PROCESSING
function GetRsmsFieldLogic(str) {
	var _zz= $H(RsmsFormFieldLogic['_default']).merge($H(RsmsFormFieldLogic[str] || RsmsFormFieldLogic['plain'])).toObject();
//	clog(_zz);
	return _zz;
	}
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
	//		clog("single dig this.column ", this.column)
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
//		observers: $w('focus blur keypress'), // obsolete
		observers: $w('blur change'),
		focus: function(evt) {},
		blur: function(evt) {},
		change: function(evt) {},
		processValue: function(inp) {
			return inp;
//			return inp.getValue();
		},
		showValue: function(val) {
			return val;
		}
	}
};
//END RSMS FIELD PROCESSING


//BEGIN RSMS FIELD VIEWING
/*--	TCViews ==> Table Column Views
----
----		CONNECTED TO »» TColumn
----
----		FNS CALLED BY »» TEntry (in the context of the entry)
----		
----	the values in '_default' are the bare minimum and will be overridden
----	the values in 'plain' are generic, if no "vtype" is listed
--*/

var TCViews = {
	plain: {
		tah: function(fld) {
			return new Element('div', {
					className: 'image', style: 'background-image:url('+fld.view.tabImage.interpolate(fld)+')'
				}).update('aa').wrap('div', {
					className:'image-wrap'
				}).wrap('th', {className: fld.thClass, title: this.title})
		},
		thClass: 'colh',
		tdClass: 'bob'
	},
	_default: {
		th: function(fld) {
			return new Element('div', {
					className: 'image', style: 'background-image:url('+fld.view.tabImage.interpolate(fld)+')', alt: fld.id
					}).wrap('div', {className:'image-wrap'
					}).wrap('th', {className: fld.thClass, title: fld.id});
		},
		eh: function(fld) {
			var _placeholder = fld.view.inputPlaceholder(fld).update('__');
			var _td = new Element('td', {className: fld.view.tdClass, title: fld.qtype});
			var _showFld = new Element('div', {className: 'showField'}).update(_placeholder);
			var _ef=this.addEntryField(fld, {
				updateElement: _placeholder,
				activateElement: _td,
				clickEditElement: _placeholder
			});
			var _editFld = new Element('div', {className: 'editField'}).insert(_ef.spawn())
			return _td.insert(_editFld).insert(_showFld)
		},
		defaultText: '__',
		thClass: 'norm',
		tdClass: 'norm',
		tabImage: 'images/th_#{id}.png',
		adviceField: function(fld){
			if(fld.advice) {
				return new Element('div', {className:'advice', title: fld.title}).insert(fld.advice);
			}
		},
		inputField: function(args) {
			return new Element('input', {style: 'width:25px'})
		},
		inputPlaceholder: function(fld) {
			return new Element('a', {href:'#', title: fld.title})
		},
		tabImUrl: function(fld) {
			return fld.view.tabImage.interpolate(fld)
		},
		editable: function() {
			return true
		}
	},
	fullDate: {
		inputField: function(fld){
			return new Element('input', {type: 'text', maxlength:'6', style:'width: 70px; font-size: 14px; color: rgb(68, 68, 68); -moz-border-radius-topleft: 2px; -moz-border-radius-topright: 2px; -moz-border-radius-bottomright: 2px; -moz-border-radius-bottomleft: 2px;'})
		}
	},
	letter: {
		th: function(fld) {
			var uDiv = new Element('div', {className: 'image', style: 'background-image:url('+fld.view.tabImUrl(fld)+')'}).wrap('div', {className:'image-wrap'});
			return new Element('th', {className: fld.view.thClass, title: fld.title}).update(uDiv);
		},
		thClass: 'catTitle',
		tdClass: 'letter',
		eh: function(fld) {
			var _placeholder = fld.view.inputPlaceholder(fld);
			var _td = new Element('td', {className: fld.view.tdClass, title: fld.qtype});
			var _showFld = new Element('div', {className: 'showField'}).update(_placeholder);
//			var _ef=this.addEntryField(fld, {});
			var _editFld = new Element('div', {className: 'editField'}).insert(_ef.spawn())
			return _td.insert(_editFld).insert(_showFld)
		},
		inputField: function(args) {
			return new Element('input', {type: 'hidden', value: '+'+this.getValue('letters') })
		},
		inputPlaceholder: function(fld){
			return new Element('div').update("+#{letters}".interpolate(fld))
		},
		editable: function() {
			return false;
		}
	},
	column: {
		th: function() {
			return new Element('th', {
					className: 'image', style: 'background-image:url('+this.tabImage()+')', alt: this.id
				}).wrap('div', {className:'image-wrap'}).wrap('th', {
					className: this.thClass, title: this.id
				});
		},
		thClass: 'catTitle',
		eh: function() {}
	},
	singleDigit: {
		inputField: function(az){
			return $R(0,9).toArray().inject(new Element('select'), function(nh, num){return nh.insert(new Element('option').update(num))});
		},
		tabImage: 'images/th_#{id}.png'
	}
}
//END RSMS FIELD VIEWING

