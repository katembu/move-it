//BEGIN HANDLERS JS
/*--	Handlers do the non-OO related grunt-work
----
----	eg. formselector ensures the 
--*/
var FormSelector = {
	_selectElement: RsmsGlobals.formSelector,
	pick: function(str) {
		clog(this);
	},
	prep: function(){
		this.selectElement=$(this._selectElement);
		this.formList = $H(RsmsForms).map(function(hArr){
			return {
				id: hArr[0],
				title: hArr[1].title,
				optgroup: hArr[1].optgroup
			}
		});
		this.populateSelectElement();
		this.selectElement.observe('change', this.handleChange)
	},
	handleChange: function(evt){
		var _changeTo=NewSheet(RsmsForms[evt.element().getValue()]);
		TVHandler.switchIn(_changeTo)
//		clog(evt.element().getValue())
	},
	populateSelectElement: function() {
		this.optgroupList = this.getOptgrouplist();
		this.selectElement.update('');
		this.optgroupList.each(function(cgl){
			var _optgroup = new Element('optgroup', {label: cgl[0].optgroup});
			cgl.each(function(frm){ this.insert(new Element('option', {value: frm.id }).update(frm.title)) }, _optgroup);
			this.insert(_optgroup)
		}, this.selectElement)
		this.selectElement.enable();
	},
	getOptgrouplist: function(){ /*-- sorts the list by groups (for <optgroup> tag) --*/
		var _optgroups = this.formList.map(function(tfg){return tfg.optgroup}).uniq()
		return _optgroups.map(function(tcg){ return this.findAll(function(tfrm){return this==tfrm.optgroup}, tcg) }, this.formList)
	}
}
$(document).observe('dom:loaded', FormSelector.prep.bind(FormSelector))

var TVHandler, __TVHandler;
var TableViewHandler=Class.create({ /*-- Table View Handler --*/
	initialize: function(opts){
		var opts			=	opts || {};
		this.current		=	null;
		this.open			=	false;
		this._wrap			=	RsmsGlobals.tableWrap || opts.tableWrapId;
		this._logo			=	RsmsGlobals.logoBox || opts.logoBoxId;
		this.mode			=	opts.view || 'view';
		this.prepped		=	false;
		$(document).observe('dom:loaded', this.prep.bind(this))
	},
	prep: function() {
		if(!this.prepped) {
			this.logo = $(this._logo).down('a');
			this.wrap = $(this._wrap);
			this.iWrap=new Element('div');
			this.wrap.insert(this.iWrap);
			this.prepped=true;
		}
	},
	openWith: function(sheetObj) {
		this.current	=	sheetObj;
		this.showCurrent();
	},
	switchIn: function(sheetObj) {
		this.oldCurrent		=	this.current || ({fadeEffect:function(){return null}});
		this.current=sheetObj;
		this.current.elem();
		this.prep();
		new Effect.Parallel($A([
				this.oldCurrent.fadeEffect({sync:true}), // || null,
				this.close({sync:true})
			]).compact(), {
				duration: 0.5,
				afterFinish: this.showCurrent.bind(this)
			})
	},
	close: function(opts) {
		if(this.open) {
			return new Effect.SlideUp(this.wrap, opts)
		} else {
			return null;
		}
//		this.wrap.slideUp(opts);
	},
	shift: function(num) {
		
	},
	feature: function(sheet) {
		TVHandler.queuedUp=sheet;
		TVHandler.wrap.fade({
			afterFinish: TVHandler.switchAndAppear
		})
	},
	switchAndAppear: function(){
		TVHandler.wrap.update(TVHandler.queuedUp.elem());
		TVHandler.wrap.appear();
	},
	changeForm: function(str) {
		if(!str) return false;
	},
	selectChangeForm: function(evt) {
		eval('var _tT=BTables.'+evt.element().value);
		TVHandler.focusOn(_tT);
	},
	showSheet: function() {
	},
	focusOn: function(tabl) {
		if(TVHandler.current!==tabl) {
			if(TVHandler.current) {
				TVHandler.current=tabl;
				new Effect.Parallel([
					new Effect.Fade(TVHandler.wrap, {from: 1.0, to: 0.0, sync:true}),
					new Effect.Fade(TVHandler.logo, {from:1.0, to: 0.0, sync:true})
					], {
						duration: 0.2,
						afterFinish: this.showCurrent.bind(this)
					});
			} else {
				TVHandler.current=tabl;
				TVHandler.showCurrent();
			}
//			UrlParse.setUrl({ form: TVHandler.current.id })
		}
	},
	showCurrent: function() {
		var _tElem=TVHandler.current.elem();
		new Effect.Parallel([
			new Effect.Appear(this.wrap.setStyle('display:none').update(_tElem), {sync: true}),
			new Effect.Appear(this.logo, {sync: true})
			], {
				duration: 0.5,
				afterFinish: function(){
				}
			})
		TVHandler.updateTopBar();
	},
	changeLogo: function(str) {
		$('form_logo').down('a').setStyle('background-image:url(images/logo_'+str+'.png)');
	},
	updateTopBar: function(tab) {
	}
});
TVHandler = new TableViewHandler();
//END HANDLERS JS

//BEGIN TRANSLATE JS
/*--	Translations are pretty straightforward. Look at the definition of F below for more help with use.
*/
var T_en = {
	errors: {
		noProcess: "There was an error processing the file at the following url: #{url}"
	}
}
var T_fr = {
	errors: {
		noProcess: "Le texte"
	}
}

/*--	T ==> Translation fn
----		parameters:
----		  • msgCode [string or object]: the tree location of the translation text within the language object
----			     eg: "errors.noProcess"
----		  • msgString [string]: the preliminary English translation of the message
----		  • interpolateHash [object]: the hash object with whch to call prototype.js' interpolate 
----		         eg: {url:'translations.json'} // for the message "Problem with #{url}"
--*/

function T(msgCode, msgString, interpolateHash) {
	var _msgString=false;
	if(typeof(msgCode)=='string') {
		_msgString = eval('T_'+RsmsGlobals.lang+'.'+msgCode);
	} else if(typeof(msgCode)=='undefined') {
		_msgString = "Invalid Error Code";
	}
	if(!_msgString) { _msgString("No translation available: ", msgCode)}
	cerr(String(_msgString || msgString).interpolate(interpolateHash));
}

/*--
if(RsmsGlobals.translationJson) {
	new Ajax.Request(RsmsGlobals.translationJson, {
		method: 'get',
		asynchronous: true,
		requestHeaders: {Accept: 'application/json'},
		onComplete: function(transport){
			if(transport.errorText) { cerr(transport.errorText) }
		},
		onSuccess: function(transport) {
			$H(transport.responseJSON).keys().each(function(tk){eval('window.T_'+tk+'={}')});
			$H(transport.responseJSON).each(function(kvArr){
				eval('window.T_'+kvArr[0]+'=kvArr[1]');
			})
		}
	})
}
--*/
//END TRANSLATE JS

