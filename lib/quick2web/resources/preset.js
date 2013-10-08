$(function() {
	var savePath = $('#save_preset').data('shared');
	if(savePath) {
		var savePreset = new SharedValue(savePath)
			.open(function() {
				$('#save_preset').enable;
			})
			.close(function() {
				$('#save_preset').disable;
			})
			.change(function() {
				$('#save_preset').refresh;
			});
	}
	
	$('#save_preset').click(function(event, element) {
		var presets = new Array;
		$('input[data-type="range"]').each(function(i, el) {
			presets[i]= $(el).val();
		});
		console.log(presets);
		savePreset.set(presets);
	});
	
	var readPath = $('#read_preset').data('shared');
	if(readPath) {
		var readPreset = new SharedValue(readPath)
			.open(function() {
				$('#read_preset').prop('disabled',false);
			})
			.close(function() {
				$('#read_preset').prop('disabled',true);
			})
			.change(function() {
				$('#read_preset').refresh;
			});
	}
	
	$('#read_preset').click(function(event, element) {
		presets = savePreset.get();
		$('input[data-type="range"]').each(function(i, el) {
			$(el).val(presets[i]).slider('refresh');
		});
		readPreset.set(presets);
	});
});