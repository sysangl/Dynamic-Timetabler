
/**
 *  Fetches all timetable items (unfiltered)
 * 
 */
async function fetchPayload() {
    const response = await fetch('/api/timetable', {
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

/**
 * Generates the numbers on the top timeline
 */
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

/**
 * Generates the grids that identify day and hour boundaries
 */
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
    const left = document.getElementById("tt-topbar-timeline").scrollWidth * scheduleProgress();
    document.getElementById("time-marker").style.left = left + "px";
}

/**
 * Scroll the value so the timemarker is visible
 */
function alignTimetimetableView() {
    const schedule = document.getElementById("tt-schedule-container")
    const marker = document.getElementById("time-marker")
    const tl = document.getElementById("tt-topbar-timeline")

    var scroll = parseInt(marker.style.left) - (tl.scrollWidth/24)*2.5;
    if (scroll < 0) scroll = 0;
    schedule.scrollLeft = scroll;
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
    const clock = document.getElementById('tt-topbar-time');
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
    const scheduleContainer = document.getElementById('tt-schedule-container')
    const backdrop  = document.getElementById('backdrop')
    const popupMenu = document.getElementById('popup-menu');
    const alreadyOpen = popupMenu.classList.contains('open') && target === popupMenu._currentTarget;
    if (alreadyOpen) {
        closePopupMenu();
        return;
    }
    const bRect = target.getBoundingClientRect()
    popupMenu.style.top = `${bRect.bottom + window.scrollY}px`;
    // popupMenu.style.left = `${bRect.left + window.scrollX}px`;
    popupMenu.style.left = `${e.pageX}px`;
    popupMenu._currentTarget = target;
    popupMenu.classList.add('open');
    backdrop.classList.add('active');
}

function closePopupMenu() {
    const popupMenu = document.getElementById('popup-menu');
    const backdrop  = document.getElementById('backdrop')
    popupMenu.classList.remove('open');
    backdrop.classList.remove('active');
    if (popupMenu._currentTarget) {
        delete popupMenu._currentTarget
    }
}

document.getElementById('tt-schedule-container').addEventListener('click', (e)=>{
    const block = e.target.closest('.timetable-block');
    if (!block) return;
    e.stopPropagation();
    showPopupMenu(block, e);
})

document.getElementById('backdrop').addEventListener('click', closePopupMenu)

document.addEventListener('keydown', (e) => {
    const popupMenu  = document.getElementById('popup-menu')
    if (e.key === 'Escape' && popupMenu.classList.contains('open')) {
        closePopupMenu();
    }
});

async function deleteBlock() {
    const popupMenu = document.getElementById('popup-menu');
    const blockId = popupMenu._currentTarget.dataset.blockId
    console.log(`Deleting block ${blockId}`)
    const response = await fetch(`/api/timetable/blocks/${blockId}`,{
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

/**
 * 
 * @param {Object} block 
 * @param {number} startMins 
 * @param {number} lengthMins 
 * @param {HTMLDivElement} tl
 * @returns {HTMLDivElement}
 */
function buildPieceElement(block, startMins, lengthMins, tl) {
    const start = new Date(block.start_datetime);
    const end = new Date(block.end_datetime);
    const minsInDay = 24 * 60;
    const scheduleStartMins = (window.settings?.start_hour ?? 0) * 60;
    const effectiveStart = startMins - scheduleStartMins;
    const leftPx = (effectiveStart/minsInDay) * tl.scrollWidth;
    const widthPx = (lengthMins/minsInDay) * tl.scrollWidth;

    const el = document.createElement('div');
    el.className = 'timetable-block';
    el.id = `timetable-block-${block.id}`;
    el.style.setProperty('--left', `${leftPx}px`);
    el.style.setProperty('--width', `${widthPx}px`);
    el.style.setProperty('--bg-colour', block.colour);
    el.dataset.blockId = block.id;

    const titleSpan = document.createElement('span');
    titleSpan.className = 'block-title';
    titleSpan.textContent = block.title;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'block-time';
    timeSpan.textContent = `${formatTime(start.getHours())}:${formatTime(start.getMinutes())} - ${formatTime(end.getHours())}:${formatTime(end.getMinutes())}`

    el.append(titleSpan, document.createElement('br'), timeSpan);
    return el;
}

/**
 * Turns a block into an element
 * ONLY for timetable blocks
 * Splits the block if it extends past the visible space
 * 
 * @param {Object} block
 * @returns {Array<{dayIdx:number, el:HTMLDivElement}} 
 */
function makeBlockElement(block) {
    const start = new Date(block.start_datetime);
    const end = new Date(block.end_datetime);

    // days were misaligned by -1 in the previous script.
    // so we normalise the day index
    // Mon : 0 -> Sun : 6
    const dayIdx = (start.getDay() + 6 ) % 7; 

    // i had a really messy way of calculating the offset for each block, but it worked
    // this is just more refined
    const minsInDay = 24 * 60;
    const startMins = start.getHours() * 60 + start.getMinutes();
    var endMins = end.getHours() * 60 + end.getMinutes();
    if (endMins <= startMins) endMins += minsInDay;

    const scheduleStartMins = (window.settings?.start_hour ?? 0) * 60;
    const scheduleEndMins = ((window.settings?.start_hour ?? 0)%24) * 60;
    
    const tl = document.getElementById('tt-topbar-timeline');
    const pieces = [];

    // if the block starts before the visible space
    if (startMins < scheduleStartMins) {
        // normalise idx for the previous day
        const prevDayidx = (dayIdx - 1 + 7) % 7
        const prevLength = Math.min(scheduleStartMins, endMins) - startMins;
        if (prevLength > 0) {
            const prevEl = buildPieceElement(block,minsInDay+startMins,prevLength, tl);
            pieces.push({dayIdx: prevDayidx, el:prevEl});
        }

        const remainingStart = scheduleStartMins;
        const remainingLength = endMins - scheduleStartMins;
        if (remainingLength > 0) {
            const currentEl = buildPieceElement(block, remainingStart, remainingLength, tl);
            pieces.push({dayIdx: dayIdx, el: currentEl})
        }
    } else {
        const currentStart = Math.max(startMins, scheduleStartMins);
        const currentEnd = Math.min(endMins, minsInDay + scheduleEndMins);
        const currentLength = currentEnd - currentStart;

        if (currentLength > 0) {
            const currentEl = buildPieceElement(block, currentStart, currentLength, tl);
            pieces.push({dayIdx: dayIdx, el:currentEl});
        }

        if (endMins > minsInDay + scheduleEndMins) {
            const nextDayIdx = (dayIdx + 1) % 7;
            const overflowMins = endMins - minsInDay;
            const overflowEl = buildPieceElement(block,scheduleEndMins,overflowMins-scheduleEndMins,tl);
            pieces.push({dayIdx: nextDayIdx, el: overflowEl})
        }

    }
    return pieces
}

async function renderTimetable() {
    console.log("Rendering timetable")
    const payload = await fetchPayload();
    const blocks = payload.blocks;
    const dayContainers = Array.from({ length: 7 }, (_, i) => {
        // The DOM has: <section id="day-container-Mon"><div class="day-inner"></div></section>
        const container = document.getElementById(`day-container-${['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i]}`);
        return container;
    });

    const fragments = Array.from({length: 7}, () => document.createDocumentFragment());

    for (const block of blocks) {
        const pieces = makeBlockElement(block);
        // fragments[dayIdx].appendChild(el);
        for (const {dayIdx, el} of pieces) {
            fragments[dayIdx].appendChild(el);
        }
    }

    fragments.forEach((frag, i)=>{
        if (frag.childElementCount) {
            dayContainers[i].appendChild(frag);
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
    document.getElementById('timetable-container').dispatchEvent(new Event('finishedBuilding'))

    // Render timetable (events, block, content)
    renderTimetable().catch(err => console.error('Timetable render failed:', err))
    window.addEventListener('resize', closePopupMenu);
    window.addEventListener('scroll', closePopupMenu);
}

initTimetable();
