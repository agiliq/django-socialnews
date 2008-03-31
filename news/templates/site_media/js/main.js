
function processComment(data) { 
    // 'data' is the json object returned from the server
		el = $('#comments') ;
		el.prepend(data['dom']); 
		handle_click();
		handle_commentreply();
}
function processTag(data){
	el = $('#tags');
	if (data['tagged']){
		el.prepend(data['dom']);
	}
}
function processCommentReply(data){
	el = 	$('#child-'+data['parent_id']);
	el.prepend(data['dom']);
	handle_commentreply();
	handle_click();
        $('.nocomment').hide();
}
function showError(data){
  alert(data);
}
$(document).ready(function(){
	 comment_url = $('#commentform').attr('action')+'?ajax=1';
	 $('#commentform').ajaxForm({
	  resetForm: true,
		success: processComment,
		url: comment_url,
		dataType: 'json'
	 });
	 
	 tag_url = $('#tagform').attr('action')+'?ajax=1'
	 	 $('#tagform').ajaxForm({
	   resetForm: true,		 
		 url: tag_url,
		 dataType:'json',
		 success: processTag,
		 failure: showError
		 });
	 $('.saved').click(function(){
	   el = $(this);
	   $.ajax({
		 url: el.attr('href')+'?ajax=1',
		 type: 'post',
		 dataType: 'json'
		 });
		 el.replaceWith('saved');
		 return false;
	 });
});
handle_commentreply = function(){
		 $('.commentreply').ajaxForm({
		 resetForm: true,		 
		 dataType:'json',
		 success: processCommentReply
		 })

  $('.commentreply').hide();
	$('.reply:not(.handled)').click(function(){
	   $(this).parent().parent().children().filter('.commentreply').toggle().addClass('handled');
		 return false;
	});
	$('.reply:not(.handled)').addClass('handled');
	}
$(document).ready(handle_commentreply);

handle_subscription = function(){
$('.unsubscribe, .subscribe').click(function(){
   el = $(this); 
	 $.ajax({
	 url: el.attr('href')+'?ajax=1',
	 type: 'post',
	 dataType: 'json',
	 success: function(data){
	 el.replaceWith(data['dom']);
	 handle_subscription();
	 }
	 });
	 return false;
});
}
$(document).ready(handle_subscription);
