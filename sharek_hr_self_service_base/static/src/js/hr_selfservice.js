odoo.define('sharek_hr_self_service_base.hr_selfservice', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var xhttp = new XMLHttpRequest();
    var ajax = require('web.ajax');

    // publicWidget.registry.check_in_out = publicWidget.Widget.extend({
    //     selector:'.oe_hr_self_service',
    //     events:{
    //         'click .check_in_out': 'check_in_out',
    //     },

    //     check_in_out: function (event) {
    //         this.update_attendance()
    //     },
    //     update_attendance: function() {
    //         var self = this;
    //         var options = {
    //             enableHighAccuracy: true,
    //             timeout: 5000,
    //             maximumAge: 60000,
    //         };
    //         if (navigator.geolocation) {
    //             navigator.geolocation.getCurrentPosition(
    //                 self._manual_attendance.bind(self),
    //             );
    //         }
    //     },
    //     _manual_attendance: function(position) {
    //         var self = this;
    //         window.location.href = window.location.origin + '/checkin/checkout?latitude=' + position.coords.latitude + '&longitude=' + position.coords.longitude;
    //     },
    // })

    

});