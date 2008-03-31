
update_link = function(data){
  if (data['object']=='link'){
    $('#points-'+data['id']).html(data['points']);
  }
  else{
    $('#compoints-'+data['id']).html(data['points']);
    
  }
    
  }
voting_failure = function(data){
  window.location = '/cannotvote/';
  
}
handle_click = function(){
  if (logged_in){  
    $('.vote, .comvote').click(function(){
    el = $(this);
    el.parent().next().children().filter('.details').children().filter('.points').html()
    if (el.hasClass('up')){
      el.next().removeClass('downmod')
      el.next().addClass('down')	
      el.removeClass('up');
      el.addClass('upmod');
    }
    else if (el.hasClass('upmod')){
      el.next().removeClass('downmod')
      el.next().addClass('down')	
      el.removeClass('upmod');
      el.addClass('up');
    }
    else if (el.hasClass('down')){
      el.prev().removeClass('upmod')
      el.prev().addClass('up')
      el.removeClass('down');
      el.addClass('downmod');
    }
    else if (el.hasClass('downmod')){
      el.prev().removeClass('upmod')	
      el.prev().addClass('up')	
      el.removeClass('downmod');
      el.addClass('down');
    }
    //points
    //$.post(el.attr('href')+'?ajax=1', update_link, 'json');
    $.ajax({
    url: el.attr('href')+'?ajax=1',
    type: 'post',
    dataType: 'json',
    success: update_link,
    failure: voting_failure
    
    })
    return false;
    });
  }
  else{
    $('.vote, .comvote').click(function(){
      window.location = '/login/';
      return false;
    })
    
  }

}  
$(document).ready(handle_click);
