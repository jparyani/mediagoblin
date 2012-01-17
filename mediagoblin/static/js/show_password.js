$(document).ready(function(){
  $("#password").after('<input type="text" value="" name="password_clear" id="password_clear" /><label><input type="checkbox" id="password_boolean" />Show password</label>');
  $('#password_clear').hide();
  $('#password_boolean').click(function(){
    if($('#password_boolean').prop("checked")) {
      $('#password_clear').val($('#password').val());
      $('#password').hide();
      $('#password_clear').show();
    } else {
      $('#password').val($('#password_clear').val());
      $('#password_clear').hide();
      $('#password').show();
    };
  });
  $('#password,#password_clear').keyup(function(){
    $('#password').val($(this).val());
    $('#password_clear').val($(this).val());
  });
});
