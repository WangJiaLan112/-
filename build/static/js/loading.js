//loading
$(window).ready(function () {
    // WAIT FOR EVERYTHING TO LOAD
    $(window).on('load', function () {
        $('body').addClass('loaded');
        $('#loader-wrapper .load_title').remove();
    });
});
$(window).on('load', function () {
    $('body').addClass('loaded');
    $('#loader-wrapper .load_title').remove();
});