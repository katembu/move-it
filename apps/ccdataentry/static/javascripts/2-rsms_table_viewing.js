/*--	TViewSheet ==> Table View Sheet
----         This is the instance of the form that creates the table, handles input, and interfaces with sms class
----
--*/

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
			var _className = fld.col.qtype || "simple";
			fld[_s]=new Element('td').update(new Element('div', {className: _className }));
			return tr.insert(fld[_s])
		},
		headRow: function(tr, fld) {
			fld.rowImage=new Image();
			fld.rowImage.src='images/th_'+fld.id+'.png';
			var _td = new Element('div', {className: 'image-wrap'}).insert(fld.rowImage);
			return tr.insert(new Element('th', {className: fld.col.qtype }).update(_td));
		},
		editRow: function(tr, fld) {
			var _className = fld.col.qtype || "simple";
			return tr.insert(fld.ef.editRowTd().addClassName(_className))
		}
	},
/*	createTable: function() {
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
			this.headRow.insert(fzl.view.th.call(this, fzl));
			this.adviceRow.insert(_tTd.clone(true).insert(new Element('div').insert(new Element('div'))));
			this.editRow.insert(fzl.view.eh.call(this, fzl));
		}.bind(this))
		
		this.fieldHelp=new Element('div', {className: 'fieldHelp'});
		this.helpRow.insert(new Element('td', {colspan: this.editRow.childElements().length}).insert(this.fieldHelp.wrap('div', {style:'position:relative;height:40px'})));

		this._elem = new Element('table', {class: 'rsmsList'});
		this._elem.insert(this.headRow).insert(this.adviceRow).insert(this.editRow).insert(this.helpRow);
	}, */
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
		// NEXT ISSUE
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


//Fades the table. This was part of the "separate view from content" effort that I abandoned toward the end.
var TableEffects = {
	fade: function(opts){ return new Effect.Fade(this._elem, opts) }
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