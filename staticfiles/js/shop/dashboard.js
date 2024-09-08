$(function () {
    //Dashboard clock
    function timeDisplay() {
        var d = new Date();
        var s = d.getSeconds();
        var m = d.getMinutes();
        var h = d.getHours();
        var day = d.getDay();
        var dt = d.getDate();
        var month = d.getMonth();
        var yr = d.getFullYear();
    
        switch (day) {
        case 0: day = 'Sunday';
        break;
        case 1: day = 'Monday';
        break;
        case 2: day = 'Tueday';
        break;
        case 3: day = 'Wednesday';
        break;
        case 4: day = 'Thursday';
        break;
        case 5: day = 'Friday';
        break;
        case 6: day = 'Saturday';
        break;
        }
    
        switch (month) {
        case 0: month = 'January';
        break;
        case 1: month = 'February';
        break;
        case 2: month = 'March';
        break;
        case 3: month = 'April';
        break;
        case 4: month = 'May';
        break;
        case 5: month = 'June';
        break;
        case 6: month = 'July';
        break;
        case 7: month = 'August';
        break;
        case 8: month = 'September';
        break;
        case 9: month = 'October';
        break;
        case 10: month = 'November';
        break;
        case 11: month = 'December';
        break;
        }
    
        s = (s < 10 ? '0'+s : s);
        m = (m < 10 ? '0'+m : m);
        h = (h < 10 ? '0'+h : h);
        $("#clock").html(day+", "+dt+" "+month+" "+yr+" - "+h+" : "+m+" : "+s);
    }
    setInterval(timeDisplay,1000);
});