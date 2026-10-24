
/**
 *  Fetches all timetable items (unfiltered)
 * 
 */
async function fetchPayload() {
    const dates = document.getElementsByClassName('day-container')
    const dpv = window.settings['days_per_view'];
    const response = await fetch(`/api/timetable/range/?start=${dates[0].dataset.isoDate}&end=${dates[dpv-1].dataset.isoDate}`, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return response.json()
}


/**
 * Clamps a number
 * @param {number} value 
 * @param {number} min 
 * @param {number} max 
 * @returns {number}
 */
function clamp(value, min, max) {
    return Math.max(Math.min(value,max), min)
}

/**
 * Generates the days and their respective containers
 */
function generateWeek() {
    const days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    const legend = document.getElementById("tt-legend");
    const schedule = document.getElementById("tt-schedule");
    window.dayContainers = {};
    legend.innerHTML = '<div id="tt-time">-</div>';
    const msInDay = 24*60*60*1000;
    const now = new Date();
    negative = false
    const dpv = window.settings['days_per_view']
    for (let inc = 0; inc < dpv; inc++) {
        var dayIdx = ((inc + window.settings['start_day']) % 7);
        const day = days[dayIdx+7-dpv];
        if (dayIdx >= window.settings['start_day']) {
            dayIdx-=dpv
        }
        const nextDay = new Date(Number(now) + msInDay*(1-now.getDay()+dayIdx));
        const newDay = document.createElement('div');
        newDay.id = `day-${day}`;
        newDay.classList.add('tt-weekday');

        const dayName = document.createElement('span');
        dayName.textContent = `${day}`;
        dayName.className = 'day-name';
        const dayDate = document.createElement('span');
        dayDate.textContent = nextDay.toDateString().slice(3);
        dayDate.className = 'day-date';
        newDay.append(dayName, document.createElement('br'), dayDate)

        const newDayCont = document.createElement('div');
        newDayCont.id = `day-container-${day}`;
        newDayCont.classList.add('day-container');
        newDayCont.dataset.date = nextDay.toDateString().slice(3)
        newDayCont.dataset.isoDate = nextDay.toISOString().slice(0,10)
        legend.appendChild(newDay)
        schedule.appendChild(newDayCont)
    }
}

/**
 * Generates the numbers on the top timeline
 */
function generateTimeline() {
    document.getElementById("tt-timeline").innerHTML = "";
    for (let inc = 0; inc < 24; inc++) {
        const hour = (inc + window.settings['start_hour']) % 24;
        const timeline = document.getElementById('tt-timeline');
        const timelineNumber = document.createElement('div');
        
        if (hour >= 12 ) {
            timelineNumber.classList.add('timeline-number-pm')
        } else {
            timelineNumber.classList.add('timeline-number')
        }
        timelineNumber.innerText = hour;
        timeline.appendChild(timelineNumber)
    }

}

/**
 * Generates the grids that identify day and hour boundaries
 */
function buildGrid() {
    const hl = document.getElementById('hour-lines');
    const dl = document.getElementById('day-lines');

    let hlHtml = '';
    for (let i=0; i<24; i++) hlHtml += '<div></div>';
    hl.innerHTML = hlHtml;

    let dlHtml = '';
    for (let i=0; i<7; i++) dlHtml += '<div></div>';
    dl.innerHTML = dlHtml;
}

/**
 * Gives the current progress through the day as a value from (0.0 - 1.0)
 * @returns {number}
 */
function dayProgress() {
    const now = new Date();
    const start = new Date(now.getFullYear() , now.getMonth(), now.getDate());
    const msSinceMidnight = now - start;
    const dayMs = 24 * 60 * 60 * 1000;
    return msSinceMidnight / dayMs;
}

/**
 * Gives the progress through the schedule (starting from the set startHour instead of 0:00)
 * @returns {number}
 */
function scheduleProgress() {
    const now = new Date();
    const start = new Date(now.getFullYear() , now.getMonth(), now.getDate(), window.settings['start_hour'], 0, 0, 0)
    const dayMs = 24 * 60 * 60 * 1000;
    let elapsed = now - start;
    if (elapsed<0) elapsed += dayMs;

    return elapsed / dayMs;
}


/**
 * Moves the current time marker
 */
function alignTimeMarker() {

    if (window.settings.timetable_view == 'horizontal') {
        const left = document.getElementById("tt-timeline").scrollWidth * scheduleProgress();
        document.getElementById("time-marker").style.left = left + "px";
    } else {
        const top = document.getElementById("tt-timeline").scrollHeight * scheduleProgress();
        document.getElementById("time-marker").style.top = top + "px";
    }
}

/**
 * Scroll the value so the timemarker is visible
 */
function alignTimetimetableView() {
    const schedule = document.getElementById("tt-schedule-container")
    const marker = document.getElementById("time-marker")
    if (window.settings.timetable_view == 'horizontal') {
        var scroll = parseInt(marker.style.left) - (schedule.scrollWidth/24);
        if (scroll < 0) scroll = 0;
        schedule.scrollLeft = scroll;
    } else {
        var scroll = parseInt(marker.style.top) - (schedule.scrollHeight/24);
        if (scroll < 0) scroll = 0;
        schedule.scrollTop = scroll;
    }
}


/**
 * Formats a number so it is always 2 digits (7 -> 07, 12 -> 12)
 * @param {number} number 
 */
function formatTime(number) {
    return number < 10 ? '0' + number : number;
}

/**
 * Update the clock on the top left corner of the timetable
 */
function updateTime() {
    const clock = document.getElementById('tt-time');
    const now = new Date();
    let hours = formatTime(now.getHours());
    let minutes = formatTime(now.getMinutes());

    clock.innerHTML = hours + ':' + minutes
}



/**
 * 
 * @param {HTMLDivElement} target 
 * @returns 
 */
function showPopupMenu(target, e) {
    const backdrop  = document.getElementById('backdrop')
    const popupMenu = document.getElementById('popup-menu');
    const alreadyOpen = popupMenu.classList.contains('open') && target === popupMenu._currentTarget;
    if (alreadyOpen) {
        closePopupMenu();
        return;
    }
    const bRect = target.getBoundingClientRect()
    popupMenu.style.top = `${e.pageY}px`;
    // popupMenu.style.left = `${bRect.left + window.scrollX}px`;
    popupMenu.style.left = `${e.pageX}px`;
    popupMenu._currentTarget = target;
    popupMenu.classList.add('open');
    backdrop.classList.add('active');
}

function closePopupMenu() {
    const popupMenu = document.getElementById('popup-menu');
    const backdrop  = document.getElementById('backdrop')
    if (!popupMenu || !backdrop) return;
    popupMenu.classList.remove('open');
    backdrop.classList.remove('active');
    if (popupMenu._currentTarget) {
        delete popupMenu._currentTarget
    }
}



async function deleteBlock() {
    const popupMenu = document.getElementById('popup-menu');
    const blockId = popupMenu._currentTarget.dataset.blockId
    const response = await fetch(`/api/timetable/block/${blockId}`,{
        'method' : 'DELETE'
    })
    document.querySelectorAll(`#timetable-block-${blockId}`).forEach(block=>block.remove())
    closePopupMenu();
}

function editBlock() {
    console.log("Edit")
}

function completeBlock() {
    console.log("complete")
}

function markRescheduleBlock() {
    console.log('mark resc')
}

function splitBlock(block) {
    const schedule = document.getElementById('tt-schedule');
    const pieces = [];
    const minsInDay = 24 * 60

    function splitBlockRecursive(currentBlock, wasSplit=false) {
        const start = new Date(currentBlock.start_datetime);
        const end = new Date(currentBlock.end_datetime);
        const endOfDay = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1);

        const startMins = start.getHours() * 60 + start.getMinutes();
        let lengthMins = (end-start) / (60*1000);
        const scheduleStartMins = (window.settings?.start_hour ?? 0) * 60;

        var sTime = `${formatTime(start.getHours())}:${formatTime(start.getMinutes())} `
        var eTime = ` ${formatTime(end.getHours())}:${formatTime(end.getMinutes())}`
        if (wasSplit) {
            sTime = `<`
        }
        if (end>endOfDay) {
            lengthMins = (endOfDay-start)/(60*1000);
            eTime = `>`
        }
        var displayTime = `${sTime}-${eTime}`

        const el = document.createElement('div');
        el.className = 'timetable-block';
        el.dataset.blockId = block.id;
        el.id = `timetable-block-${block.id}`;

        if (window.settings.timetable_view =='horizontal') {
            const leftPx = ((startMins - scheduleStartMins) / minsInDay) * schedule.scrollWidth;
            const widthPx = (lengthMins / minsInDay) * schedule.scrollWidth;
            el.style.setProperty('--left', `${leftPx}px`)
            el.style.setProperty('--width', `${widthPx}px`)
        } else {
            const topPx = ((startMins - scheduleStartMins) / minsInDay) * schedule.scrollHeight;
            const heightPx = (lengthMins / minsInDay) * schedule.scrollHeight;
            el.style.setProperty('--top', `${topPx}px`)
            el.style.setProperty('--height', `${heightPx}px`)
        }
        el.style.setProperty('--bg-colour', block.colour ?? (window.settings?.default_block_colour ?? '#3b3d68'))
    
        const infoDiv = document.createElement('div');
        infoDiv.classList.add('block-info', 'sticky')

        const titleSpan = document.createElement('span');
        titleSpan.className = 'block-title';
        titleSpan.textContent = block.title;
        const timeSpan = document.createElement('span');
        timeSpan.className = 'block-time';
        timeSpan.textContent = displayTime;
        infoDiv.append(titleSpan, document.createElement('br'), timeSpan);
        el.appendChild(infoDiv)
        el.dataset.date = start.toDateString().slice(3);
        pieces.push(el);
        
        if (end > endOfDay) {
            const nextBlock = {
                ...currentBlock,
                start_datetime: endOfDay.toISOString()
            }
            splitBlockRecursive(nextBlock, true);
        }
    }

    splitBlockRecursive(block);
    return pieces
}

async function renderTimetable() {
    const payload = await fetchPayload();
    const blocks = payload.blocks;
    const getDayContainer = (date) => document.querySelector(`[data-date="${date}"]`)

    const fragmentMap = new Map();

    for (const block of blocks) {
        const pieces = splitBlock(block);
        for (const el of pieces) {
            const date = el.dataset.date;
            if (!fragmentMap.has(date)) {
                fragmentMap.set(date, document.createDocumentFragment())
            }
            fragmentMap.get(date).appendChild(el);
        }
    }

    fragmentMap.forEach((frag, date)=>{
        const dayContainer = getDayContainer(date);
        if (dayContainer) {
            dayContainer.appendChild(frag);
        }
    })
}


async function clearTimetable() {
    const dayContainers = Array.from({ length: 7 }, (_, i) => {
        // The DOM has: <section id="day-container-Mon"><div class="day-inner"></div></section>
        const container = document.getElementById(`day-container-${['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i]}`);
        return container;
    });
    dayContainers.forEach(container => {
        container.children.forEach(child=>child.remove())
    })
}



async function initTimetable() {
    // Build timetable (actual html and timetable divs)
    window.settings = await fetchSettings();
    document.documentElement.style.setProperty('--days', window.settings['days_per_view']);
    generateWeek(); // generate first column of the timetable
    generateTimeline(); // generate top row of the timetable
    updateTime(); // set the timetable corner clock
    buildGrid(); // generate grid
    alignTimeMarker(); // make sure time marker is in the right place
    window.pageIntervals.temporary.push(setInterval(alignTimeMarker, 60*1000)); // update the time marker every 60 seconds
    window.pageIntervals.temporary.push(setInterval(updateTime, 5*1000)); // set the timetable corner clock
    alignTimetimetableView(); // scroll timetable to the current time
    document.getElementById('timetable-container').dispatchEvent(new Event('finishedBuilding'))

    // Render timetable (events, block, content)
    renderTimetable().catch(err => console.error('Timetable render failed:', err))
    window.addEventListener('resize', closePopupMenu);
    window.addEventListener('scroll', closePopupMenu);

    const scheduleContainer = document.getElementById('tt-schedule-container')
    scheduleContainer.addEventListener('click', (e)=>{
        const block = e.target.closest('.timetable-block');
        if (!block) return;
        e.stopPropagation();
        showPopupMenu(block, e);
    })

    document.getElementById('backdrop').addEventListener('click', closePopupMenu)

    document.addEventListener('keydown', (e) => {
        const popupMenu  = document.getElementById('popup-menu')
        if (!popupMenu) return;
        if (e.key === 'Escape' && popupMenu.classList.contains('open')) {
            closePopupMenu();
        }
    });

}

initTimetable();
