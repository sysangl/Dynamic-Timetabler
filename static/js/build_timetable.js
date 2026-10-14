// clamp function
function clamp(value, min, max) {
    if (value < min) {
        return min
    }
    if (value > max) {
        return max
    }
}

// generates the days on the left side of the timetable view
function generateWeek() {
    console.log('Generating Week')
    const days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    window.dayContainers = {};
    document.getElementById("tt-legend").innerHTML = '<div id="tt-topbar-time">-</div>';
    for (let dayIdx = window.settings['start_day']; dayIdx < 7; dayIdx++) {
        document.getElementById("tt-legend").innerHTML+=`<div id="day-${days[dayIdx]}" class="tt-weekday"> ${days[dayIdx]} </div>`;
        document.getElementById("tt-schedule").innerHTML+=`<div id="day-container-${days[dayIdx]}" class="day-container"></div>`;
    }
    for (let dayIdx = 0; dayIdx < window.settings['start_day']; dayIdx++) {
        document.getElementById("tt-legend").innerHTML+='<div class="tt-weekday">'+days[dayIdx]+'</div>';
        document.getElementById("tt-schedule").innerHTML+=`<div id="day-container-${days[dayIdx]}" class="day-container"></div>`;

    }
}

// generates the hours along the top of the timetable view
function generateTimeline() {
    document.getElementById("tt-topbar-timeline").innerHTML = "";
    for (let hour = window.settings['start_hour']; hour < 24; hour++) {
        if (hour >= 12 ) {
            document.getElementById("tt-topbar-timeline").innerHTML+='<div class="timeline-number-pm"> '+hour+'</div>';
        } else {
            document.getElementById("tt-topbar-timeline").innerHTML+='<div class="timeline-number"> '+hour+'</div>';
        }
    }
    for (let hour = 0; hour < window.settings['start_hour']; hour++) {
        if (hour >= 12 ) {
            document.getElementById("tt-topbar-timeline").innerHTML+='<div class="timeline-number-pm"> '+hour+'</div>';
        } else {
            document.getElementById("tt-topbar-timeline").innerHTML+='<div class="timeline-number"> '+hour+'</div>';
        }
    }
}

// generates the grid that shows the hours and day boundaries
function buildGrid() {
    const tl = document.getElementById('tt-topbar-timeline');
    const ts = document.getElementById('tt-schedule')
    const l = document.getElementById('tt-legend');
    const hl = document.getElementById('hour-lines');
    const dl = document.getElementById('day-lines');


    hl.style.width = tl.scrollWidth + 'px';
    hl.style.height = l.scrollHeight + 'px';
    dl.style.top = tl.scrollHeight + 'px';
    dl.style.width = tl.scrollWidth + 'px';
    dl.style.height = ts.scrollHeight + 'px';

    let hlHtml = '';
    for (let i=0; i<24; i++) hlHtml += '<div></div>';
    hl.innerHTML = hlHtml;

    let dlHtml = '';
    for (let i=0; i<7; i++) dlHtml += '<div></div>';
    dl.innerHTML = dlHtml;

    const dayWidth = tl.scrollWidth;
    const dayContainers = document.querySelectorAll('.day-container');
    dayContainers.forEach(col => col.style.width = dayWidth + 'px');
}

// gives the progress through the day. returns a float from 0 to 1
function dayProgress() {
    const now = new Date();
    const start = new Date(now.getFullYear() , now.getMonth(), now.getDate());
    const msSinceMidnight = now - start;
    const dayMs = 24 * 60 * 60 * 1000;
    return msSinceMidnight / dayMs;
}

// gives the progress through the schedule (starts at startHour instead of 00:00)
function scheduleProgress() {
    const now = new Date();
    const start = new Date(now.getFullYear() , now.getMonth(), now.getDate(), window.settings['start_hour'], 0, 0, 0)
    const dayMs = 24 * 60 * 60 * 1000;
    let elapsed = now - start;
    if (elapsed<0) elapsed += dayMs;

    return elapsed / dayMs;
}

// moves the time marker (vertical red line)
function alignTimeMarker() {
    const left = document.getElementById("tt-topbar-timeline").scrollWidth * scheduleProgress();

    document.getElementById("time-marker").style.left = left + "px";
}

// scroll the schedule to make sure the time marker is visible
function alignTimetimetableView() {
    const schedule = document.getElementById("tt-schedule-container")
    const marker = document.getElementById("time-marker")
    const tl = document.getElementById("tt-topbar-timeline")

    var scroll = parseInt(marker.style.left) - (tl.scrollWidth/24)*2.5;
    if (scroll < 0) scroll = 0;
    schedule.scrollLeft = scroll;
}


// so the time always has two numbers, eg. 09:00, 15:52, 01:28
function formatTime(number) {
    return number < 10 ? '0' + number : number;
}

// updates the time on the top-left corner of the timetable
function updateTime() {
    const clock = document.getElementById('tt-topbar-time');
    const now = new Date();
    let hours = formatTime(now.getHours());
    let minutes = formatTime(now.getMinutes());

    clock.innerHTML = hours + ':' + minutes
}


async function initTimetable() {
    window.settings = await fetchSettings(1);
    generateWeek(); // generate first column of the timetable
    generateTimeline(); // generate top row of the timetable
    buildGrid(); // generate grid
    document.getElementById('tt-topbar-timeline').style.width=document.getElementById('tt-topbar-timeline').scrollWidth+'px'; // make sure the timeline has a continous bg
    alignTimeMarker(); // make sure time marker is in the right place
    window.pageIntervals.temporary.push(setInterval(alignTimeMarker, 60*1000)); // update the time marker every 60 seconds
    updateTime(); // set the timetable corner clock
    window.pageIntervals.temporary.push(setInterval(updateTime(), 5*1000)); // set the timetable corner clock
    alignTimetimetableView(); // scroll timetable to the current time
}

initTimetable();

// window.pageInits.timetable = initTimetable;