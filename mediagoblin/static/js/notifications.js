'use strict';
var notifications = {};

(function (n) {
    n._base = '/';
    n._endpoint = 'notifications/json';

    n.init = function () {
        $('.notification-gem').on('click', function () {
            $('.header_dropdown_down:visible').click();
        });
    }

})(notifications)

$(document).ready(function () {
    notifications.init();
});
