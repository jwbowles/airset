$(function() {
	var sliderControl = new Array();
	$('input[data-type="range"]').each(function(i, el) {
		sliderControl[i] = $(el);
		var sharedPath = sliderControl[i].data('shared');
		if (sharedPath) {
			var sliderValue = new SharedValue(sharedPath)
				.open(function() {
					sliderControl[i].slider('enable');
				})
				.close(function() {
					sliderControl[i].slider('disable');
				})
				.change(function(event, value) {
					sliderControl[i].val(value).slider('refresh')
				});
			
			sliderControl[i].change(function(event, element) {
				sliderValue.set(sliderControl[i].val());
			});
		}
	});
});