/*--	JS Classes in this file:
----	RsmsForm, TColumn 
----	
----	
----	
----	RsmsForms object stores template information about each form.
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

//		this.view = $H(TCViews._default).merge($H(TCViews[this.qtype])).toObject();
//		this.logic = this.view;
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
