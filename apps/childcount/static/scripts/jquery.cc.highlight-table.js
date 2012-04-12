/* jQuery CC Highlight Table
 -   ask Alex Dorey for more info: dorey415@gmail.com
 -
 -   usage: $('table').highlightTable(options)
 -   highlights columns with "th"s with the class 'highlight-column'
*/

(function($){
	var hTable,
		cycleTime,
		cyclePauseUntil = 0,
		cyclePause = false,
		hc = 'highlight-column',
		hcA = 'highlighted',
		cycleTimeout = false,
		//debug = console.log,
		cycle = {
			ticker: 0,
			pause: function() {
				//debug(">>ticker " + cycle.ticker + " -> " + (cycle.ticker+1));
				cycle.ticker++;
			},
			resume: function() {
				//debug(">>ticker " + cycle.ticker + " -> " + (cycle.ticker-1));
				cycle.ticker--
				setCycleTimeout(CycleColumns, cycleTime);
			}
		};

	function HighlightTable(options) {
		hTable = this.addClass('highlight-table');
		var opts = {
			cycleTime: 5000,
			activateEvent: 'hover',
			thWidth: 220
		}
		
		$.extend(opts, options);
		
		var absWrap = $("<div />").addClass('absolute-wrap').css({'width': opts.thWidth}),
			hThs = $('th.'+hc, this),
			tTds,
			colIndexes = hThs.map(function(){return $(this).index()+1});
		
		$.map(colIndexes, function(ii){
				return $('tr', hTable).find('td:nth-child('+ii+')').addClass(hc)
			});
		
		hTds = $('td.'+hc, hTable);
		hTds.wrapInner('<div />');
		
		hThs.wrapInner(absWrap).wrapInner("<div class='relative-wrap' />")
		hTds.live(opts.activateEvent, function(){
			HighlightColumn($(this));
		});
		
		if(opts.activateEvent=='hover') {
			hTds.hover(cycle.pause, cycle.resume);
		} else if(opts.activateEvent=='click') {
			hTds.click(cycle.pause);
		}
		
		if(opts.cycleTime && opts.cycleTime>0) {
			cycleTime = (opts.cycleTime > 1000) ? opts.cycleTime : (1000*opts.cycleTime);
			HighlightColumn($(hTable.find('th.'+hc).get(0)))
			//debug("Starting off the show");
			setCycleTimeout(CycleColumns, cycleTime);
		}
		return this;
	}
	function CycleColumns() {
		//debug("CycleColumns ", cycleTimeout);
		if(cycle.ticker > 0) {
			//debug(" --but ticker says pause ", cycleTimeout);
			return false;
		}
		var curCol = hTable.find('th.'+hcA),
			nextCol = curCol.next('.'+hc).get(0);
		
		if(!nextCol) {
			nextCol = curCol.siblings('th.'+hc).get(0)
		}

		if(nextCol) {
			HighlightColumn($(nextCol), function() {
				setCycleTimeout(CycleColumns, cycleTime);
			});
		}
	}
	function setCycleTimeout(fn, ct) {
		if(cycleTimeout) {
			//debug("Clearing timeout to set a new one", cycle.ticker)
			window.clearTimeout(cycleTimeout);
		}
		cycleTimeout = window.setTimeout(fn, ct);
	}
	function HighlightColumn(elm, switchCallback) {
		//debug("highlight column called");
		if(!elm.hasClass(hcA)) {
			//debug(" --switching ");
			hTable.find('td.'+hcA).removeClass(hcA)
			hTable.find('th.'+hcA).removeClass(hcA)
			hTable.find('td:nth-child('+(elm.index()+1)+').'+hc).addClass(hcA);
			hTable.find('th:nth-child('+(elm.index()+1)+').'+hc).addClass(hcA);
			
			if(typeof(switchCallback)=='function') {
				switchCallback();
			}
		}
	}
	
	$.fn.highlightTable = HighlightTable;
})(jQuery);